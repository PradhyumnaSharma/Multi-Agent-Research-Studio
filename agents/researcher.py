"""
Researcher Agent - Conducts web research using DuckDuckGo
Optimized for speed with parallel searches and batched LLM calls.
"""
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import config
from utils.state import ResearchState, Source, add_agent_action


class ResearcherAgent:
    """Agent responsible for conducting research"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.DEFAULT_MODEL
        if not config.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not found. Set it in .env file or environment."
            )

        self.llm = ChatGroq(
            groq_api_key=config.GROQ_API_KEY,
            model_name=self.model_name,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
        )
        self.search_tool = DuckDuckGoSearchAPIWrapper()
        if config.ENABLE_WIKIPEDIA:
            from langchain_community.utilities import WikipediaAPIWrapper
            self.wiki_tool = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=600)

    # ------------------------------------------------------------------
    # Single Wikipedia search (called in thread pool)
    # ------------------------------------------------------------------
    def _search_wikipedia(self, query: str) -> List[Source]:
        """Run one Wikipedia search and return Source objects."""
        sources: List[Source] = []
        if not hasattr(self, 'wiki_tool'):
            return sources
            
        try:
            raw = self.wiki_tool.run(query)
            if raw and raw.strip():
                for page_block in raw.split("\n\n"):
                    if "Page:" in page_block:
                        lines = page_block.split("\n", 1)
                        if len(lines) >= 2:
                            title = lines[0].replace("Page:", "").strip()
                            snippet = lines[1].replace("Summary:", "").strip()[:600]
                            
                            source = Source(
                                title=f"{title}",
                                url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                snippet=snippet,
                                retrieved_at=datetime.now().isoformat(),
                            )
                            sources.append(source)
        except Exception as e:
            print(f"[Researcher] Wiki error: {e}")
        return sources

    # ------------------------------------------------------------------
    # Single DuckDuckGo search (called in thread pool)
    # ------------------------------------------------------------------
    def _search_single_query(self, query: str) -> List[Source]:
        """Run one DuckDuckGo search and return Source objects."""
        sources: List[Source] = []
        try:
            results = self.search_tool.results(query, max_results=3)
            
            for index, res in enumerate(results):
                title = res.get("title", f"{query} - Result {index+1}")
                link = res.get("link", "")
                snippet = res.get("snippet", "")
                
                # Filter out sponsored ads from search results
                if "bing.com/aclick" in link or not link.strip():
                    continue
                
                # Exclude any snippet that looks like an API/connection error
                err_lower = snippet.lower()
                if not snippet.strip() or "connecterror:" in err_lower or "error sending request" in err_lower:
                    continue

                source = Source(
                    title=title,
                    url=link,
                    snippet=snippet[:600],
                    retrieved_at=datetime.now().isoformat(),
                )
                sources.append(source)
                
        except Exception as e:
            print(f"[Researcher] Search error for query '{query}': {e}")
            # We no longer append the error as a fake source to prevent confusing the Critic.
        return sources

    # ------------------------------------------------------------------
    # Parallel search across all queries
    # ------------------------------------------------------------------
    def _search_parallel(self, queries: List[str]) -> List[Source]:
        """Run all searches in parallel via ThreadPool."""
        all_sources: List[Source] = []
        # Calculate workers needed (ddg + wiki if enabled)
        workers = len(queries) * (2 if config.ENABLE_WIKIPEDIA else 1)
        
        with ThreadPoolExecutor(max_workers=min(workers, 8)) as pool:
            futures = []
            for i, q in enumerate(queries):
                # Always search DuckDuckGo
                futures.append(pool.submit(self._search_single_query, q))
                
                # If Wikipedia is enabled, submit a couple of broad queries to Wikipedia
                if config.ENABLE_WIKIPEDIA and i < 2:
                    futures.append(pool.submit(self._search_wikipedia, q))
                    
            for future in as_completed(futures):
                try:
                    all_sources.extend(future.result())
                except Exception:
                    pass
        return all_sources

    # ------------------------------------------------------------------
    # Main research entry-point (called by LangGraph)
    # ------------------------------------------------------------------
    def research(self, state: ResearchState) -> ResearchState:
        print(f"\n[Researcher] Starting research node: iteration {state.get('research_iteration', 0)}")
        topic = state["topic"]
        previous_feedback = state.get("critic_feedback", "")
        iteration = state.get("research_iteration", 0)
        research_depth = state.get("research_depth", "standard").lower()

        state["status"] = "researching"
        state = add_agent_action(
            state, "Researcher", "Starting research",
            {"topic": topic, "iteration": iteration},
        )

        # ---- Step 1: generate search queries (single LLM call) ----
        print(f"[Researcher] Step 1: Generating search queries for topic: {topic} at '{research_depth}' depth")
        
        # Configure query counts based on depth
        query_count_instructions = {
            "quick": "1-2 concise search queries",
            "standard": "3-5 concise search queries",
            "comprehensive": "5-8 concise, deep search queries covering different angles and opposing viewpoints"
        }
        query_instruction = query_count_instructions.get(research_depth, query_count_instructions["standard"])

        if previous_feedback:
            prompt = (
                f"Based on this feedback, generate {query_instruction} to "
                f"refine research on '{topic}'.\n\nFeedback: {previous_feedback}\n\n"
                f"Return ONLY a numbered list of queries, nothing else."
            )
        else:
            prompt = (
                f"Generate {query_instruction} to comprehensively "
                f"research: '{topic}'.\n\n"
                f"Cover: definitions, recent developments, statistics, expert views, "
                f"and related subtopics.\n\n"
                f"Return ONLY a numbered list of queries, nothing else."
            )

        try:
            print("[Researcher] Calling LLM to generate queries...")
            resp = self.llm.invoke([HumanMessage(content=prompt)])
            queries_text = resp.content if hasattr(resp, "content") else str(resp)
            print(f"[Researcher] LLM returned query text: {queries_text[:100]}...")

            queries: List[str] = []
            for line in queries_text.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
                    q = line.split(".", 1)[-1].strip().lstrip("-* ").strip()
                    if len(q) > 10:
                        queries.append(q)

            if not queries:
                queries = [topic]

            state = add_agent_action(
                state, "Researcher", "Generated research queries",
                {"queries": queries},
            )

            # Limit queries based on depth
            max_queries = {"quick": 2, "standard": 5, "comprehensive": 8}.get(research_depth, 5)
            queries_to_run = queries[:max_queries]

            # ---- Step 2: parallel DuckDuckGo searches ----
            print(f"[Researcher] Step 2: Running parallel searches for {len(queries_to_run)} queries...")
            all_sources = self._search_parallel(queries_to_run)
            print(f"[Researcher] Searches completed. Found {len(all_sources)} sources.")
            state = add_agent_action(
                state, "Researcher", "Web searches completed",
                {"sources_found": len(all_sources)},
            )

            # ---- Step 3: single batched synthesis LLM call ----
            snippets_block = "\n\n".join(
                f"[Query: {s['title']}]\n{s['snippet'][:300]}"
                for s in all_sources[:8]
            )
            synthesis_prompt = (
                f"You are a research assistant. Synthesize the following search "
                f"results into 3-5 concise, factual research notes about '{topic}'.\n\n"
                f"Search Results:\n{snippets_block}\n\n"
                f"Return each note on its own line prefixed with '- '."
            )

            print("[Researcher] Step 3: Calling LLM to synthesize research notes...")
            synth_resp = self.llm.invoke([HumanMessage(content=synthesis_prompt)])
            synth_text = synth_resp.content if hasattr(synth_resp, "content") else str(synth_resp)
            print(f"[Researcher] Synthesis complete. Length: {len(synth_text)} chars.")

            research_notes = []
            for line in synth_text.split("\n"):
                line = line.strip().lstrip("- ").strip()
                if len(line) > 20:
                    research_notes.append({
                        "query": topic,
                        "content": line,
                        "sources": [],
                        "timestamp": datetime.now().isoformat(),
                    })

            if not research_notes:
                research_notes.append({
                    "query": topic,
                    "content": synth_text.strip(),
                    "sources": [],
                    "timestamp": datetime.now().isoformat(),
                })

            # ---- Step 4: update state ----
            state["sources"] = state.get("sources", []) + all_sources
            state["research_notes"] = state.get("research_notes", []) + research_notes
            state["research_iteration"] = iteration + 1

            state = add_agent_action(
                state, "Researcher", "Research completed",
                {
                    "sources_found": len(all_sources),
                    "notes_created": len(research_notes),
                    "iteration": state["research_iteration"],
                },
            )
            print("[Researcher] Research node completed successfully.")

        except Exception as e:
            print(f"[Researcher] ERROR in research node: {e}")
            state["error_message"] = f"Research error: {e}"
            state = add_agent_action(
                state, "Researcher", "Research error", {"error": str(e)}
            )

        return state
