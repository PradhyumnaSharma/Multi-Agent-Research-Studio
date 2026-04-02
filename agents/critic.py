"""
Critic Agent - Evaluates research quality and provides feedback
"""
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from datetime import datetime
import re
import config
from utils.state import ResearchState, add_agent_action


class CriticAgent:
    """Agent responsible for evaluating research quality"""

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

    # ------------------------------------------------------------------
    def _parse_status(self, text: str) -> str:
        """
        Robustly detect SUFFICIENT vs INSUFFICIENT.
        Check for INSUFFICIENT *first* since it contains SUFFICIENT.
        """
        upper = text.upper()

        # Look for an explicit STATUS: line first
        m = re.search(r"STATUS\s*:\s*(INSUFFICIENT|SUFFICIENT)", upper)
        if m:
            return m.group(1)

        # Fall back: count occurrences
        insuf_count = upper.count("INSUFFICIENT")
        suf_count = upper.count("SUFFICIENT") - insuf_count  # net SUFFICIENT
        if insuf_count > suf_count:
            return "INSUFFICIENT"
        if suf_count > 0:
            return "SUFFICIENT"
        return "UNKNOWN"

    # ------------------------------------------------------------------
    def evaluate(self, state: ResearchState) -> ResearchState:
        print(f"\n[Critic] Starting review node: iteration {state.get('research_iteration', 0)}")
        topic = state["topic"]
        research_notes = state.get("research_notes", [])
        sources = state.get("sources", [])
        iteration = state.get("research_iteration", 0)
        previous_feedback = state.get("critic_feedback", "")
        research_depth = state.get("research_depth", "standard").lower()

        state["status"] = "reviewing"
        state = add_agent_action(
            state, "Critic", "Starting LLM logic evaluation", {"iteration": iteration}
        )

        max_iter_map = {"quick": 1, "standard": 3, "comprehensive": 5}
        depth_max_iterations = max_iter_map.get(research_depth, config.MAX_RESEARCH_ITERATIONS)
        max_iter_reached = iteration >= depth_max_iterations

        # ---- Build evaluation prompt ----
        notes_block = "\n".join(
            f"{i + 1}. {n.get('content', n) if isinstance(n, dict) else n}"
            for i, n in enumerate(research_notes)
        )
        evaluation_prompt = (
            f"You are an expert research quality critic. Evaluate this research on: \"{topic}\"\n\n"
            f"Research Notes ({len(research_notes)} notes):\n{notes_block}\n\n"
            f"Sources Found: {len(sources)}\n"
            f"Iteration: {iteration}\n"
            f"Previous Feedback: {previous_feedback or 'None'}\n\n"
            f"Your task is to determine if this research is comprehensive, accurate, and ready to be compiled into a final report. Use your own intelligence to assess completeness.\n"
            f"You MUST provide a QUALITY SCORE from 0.0 to 1.0 (where 1.0 is perfect coverage).\n\n"
            f"Reply with EXACTLY this format:\n\n"
            f"SCORE: <float between 0.0 and 1.0>\n"
            f"STATUS: SUFFICIENT   (or STATUS: INSUFFICIENT)\n\n"
            f"If INSUFFICIENT:\n"
            f"FEEDBACK:\n<specific actionable feedback on what to research next>\n\n"
            f"If SUFFICIENT:\n"
            f"OUTLINE:\n<detailed hierarchical outline for a report>"
        )

        try:
            print("[Critic] Calling LLM to evaluate research quality intrinsically...")
            resp = self.llm.invoke([HumanMessage(content=evaluation_prompt)])
            eval_text = resp.content if hasattr(resp, "content") else str(resp)

            parsed_status = self._parse_status(eval_text)
            
            # Extract SCORE
            quality_score = 0.5
            score_match = re.search(r"SCORE\s*:\s*([0-9]*\.?[0-9]+)", eval_text.upper())
            if score_match:
                try:
                    quality_score = float(score_match.group(1))
                except ValueError:
                    pass
            state["quality_score"] = quality_score
            print(f"[Critic] Evaluated status: {parsed_status} with LLM Score: {quality_score}")

            # Pure LLM reliance (fallback only if max iterations hit)
            is_sufficient = (parsed_status == "SUFFICIENT" or max_iter_reached)

            if is_sufficient:
                print(f"[Critic] Research is SUFFICIENT. Generating outline...")
                # ---------- APPROVED: extract or generate outline ----------
                if "OUTLINE:" in eval_text:
                    outline = eval_text.split("OUTLINE:", 1)[-1].strip()
                    print("[Critic] Outline extracted from evaluation text directly.")
                else:
                    print("[Critic] Calling LLM to generate outline...")
                    outline_prompt = (
                        f"Create a detailed hierarchical outline for a research report on \"{topic}\".\n\n"
                        f"Research Notes:\n{notes_block}\n\n"
                        f"Use proper indentation, main sections, and subsections."
                    )
                    o_resp = self.llm.invoke([HumanMessage(content=outline_prompt)])
                    outline = o_resp.content if hasattr(o_resp, "content") else str(o_resp)
                    print("[Critic] Outline generation completed.")

                state["outline"] = outline
                state["critic_feedback"] = ""  # Clear feedback
                state["status"] = "awaiting_approval"

                state["refinement_history"].append({
                    "iteration": iteration,
                    "quality_score": quality_score,
                    "action": "approved_for_outline",
                    "timestamp": datetime.now().isoformat(),
                })
                state = add_agent_action(
                    state, "Critic", "Research approved – outline generated",
                    {"quality_score": quality_score, "sources": len(sources)},
                )
            else:
                print(f"[Critic] Research needs refinement (quality_score: {quality_score:.2f}). Generating feedback...")
                # ---------- NEEDS REFINEMENT ----------
                if "FEEDBACK:" in eval_text:
                    feedback = eval_text.split("FEEDBACK:", 1)[-1].strip()
                else:
                    print("[Critic] Calling LLM for specific refinement feedback...")
                    fb_prompt = (
                        f"The research on \"{topic}\" needs improvement.\n"
                        f"Sources: {len(sources)}, Notes: {len(research_notes)}, "
                        f"Quality: {quality_score:.2f}.\n"
                        f"Give specific, actionable feedback on what to research next."
                    )
                    fb_resp = self.llm.invoke([HumanMessage(content=fb_prompt)])
                    feedback = fb_resp.content if hasattr(fb_resp, "content") else str(fb_resp)
                
                print(f"[Critic] Feedback generated: {feedback[:100]}...")

                state["critic_feedback"] = feedback
                state["status"] = "researching"

                state["refinement_history"].append({
                    "iteration": iteration,
                    "quality_score": quality_score,
                    "feedback": feedback[:300],
                    "action": "needs_refinement",
                    "timestamp": datetime.now().isoformat(),
                })
                state = add_agent_action(
                    state, "Critic", "Research needs refinement",
                    {"quality_score": quality_score, "iteration": iteration},
                )

            print("[Critic] Evaluation node completed successfully.")

        except Exception as e:
            error_msg = f"Critic evaluation error: {e}"
            print(f"[Critic] ERROR: {error_msg}")
            state["error_message"] = error_msg
            state = add_agent_action(
                state, "Critic", "Evaluation error", {"error": str(e)}
            )
            # Fallback: if we have enough research, generate a basic outline
            if len(research_notes) >= 2 and len(sources) >= 2:
                print("[Critic] ERROR fallback triggered: generating default basic outline.")
                state["outline"] = (
                    f"# Research Report: {topic}\n\n"
                    f"## Introduction\n## Main Findings\n## Conclusion"
                )
                state["critic_feedback"] = ""
                state["status"] = "awaiting_approval"

        return state
