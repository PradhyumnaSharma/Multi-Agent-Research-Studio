"""
Writer Agent - Generates final research report
"""
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from datetime import datetime
import config
from utils.state import ResearchState, add_agent_action
from config import RESEARCH_TEMPLATES


class WriterAgent:
    """Agent responsible for writing the final report"""

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

    def write_report(self, state: ResearchState) -> ResearchState:
        print(f"\n[Writer] Starting report generation for topic: {state.get('topic', '')}")
        topic = state["topic"]
        outline = state.get("outline", "")
        research_notes = state.get("research_notes", [])
        sources = state.get("sources", [])
        template_type = state.get("template_type", "academic")

        state["status"] = "writing"
        state = add_agent_action(state, "Writer", "Starting report generation")

        template = RESEARCH_TEMPLATES.get(template_type, RESEARCH_TEMPLATES["academic"])
        template_style = template.get("style", "academic")
        print(f"[Writer] Using template: {template_type}, style: {template_style}")

        notes_content = "\n\n".join(
            f"**Note {i + 1}:** {n.get('content', n) if isinstance(n, dict) else n}"
            for i, n in enumerate(research_notes)
        )
        sources_list = "\n".join(
            f"- {s.get('title', 'Untitled')} ({s.get('url', 'N/A')})"
            for s in sources[:20]
        )

        writing_prompt = (
            f"You are an expert research writer. Write a comprehensive Markdown "
            f"research report.\n\n"
            f"Topic: {topic}\n\nOutline:\n{outline}\n\n"
            f"Research Notes:\n{notes_content}\n\n"
            f"Sources:\n{sources_list}\n\n"
            f"Style: {template_style} | Template: {template_type}\n\n"
            f"Instructions:\n"
            f"1. Follow the outline structure\n"
            f"2. Synthesize the research notes\n"
            f"3. Use clear, professional language\n"
            f"4. Use proper Markdown (headers, lists, emphasis)\n"
            f"5. Include citations as [Source N] where appropriate\n"
            f"6. Make the report comprehensive yet readable"
        )

        try:
            print("[Writer] Calling LLM to write the comprehensive report...")
            resp = self.llm.invoke([HumanMessage(content=writing_prompt)])
            report = resp.content if hasattr(resp, "content") else str(resp)
            print(f"[Writer] Report generated. Length: {len(report)} chars.")

            final_report = report

            # Append references if not already present
            if "## References" not in final_report and "## Bibliography" not in final_report:
                final_report += "\n\n## References\n\n"
                for i, src in enumerate(sources, 1):
                    final_report += f"{i}. **{src.get('title', 'Untitled')}**\n"
                    if src.get("url"):
                        final_report += f"   - URL: {src['url']}\n"
                    if src.get("snippet"):
                        final_report += f"   - Summary: {src['snippet'][:150]}…\n"
                    final_report += "\n"

            state["final_report"] = final_report
            state["status"] = "completed"
            state["research_end_time"] = datetime.now().isoformat()

            state["report_metadata"] = {
                "word_count": len(final_report.split()),
                "section_count": final_report.count("##"),
                "sources_cited": len(sources),
                "generated_at": datetime.now().isoformat(),
                "template_used": template_type,
                "model_used": self.model_name,
            }

            state = add_agent_action(
                state, "Writer", "Report generation completed",
                {
                    "report_length": len(final_report),
                    "word_count": state["report_metadata"]["word_count"],
                },
            )
            print("[Writer] Write node completed successfully.")

        except Exception as e:
            print(f"[Writer] ERROR: {e}")
            state["error_message"] = f"Writing error: {e}"
            state["status"] = "failed"
            state = add_agent_action(
                state, "Writer", "Writing error", {"error": str(e)}
            )
            # Fallback report
            state["final_report"] = (
                f"# Research Report: {topic}\n\n"
                f"## Introduction\nResearch findings on {topic}.\n\n"
                f"## Findings\n{notes_content}\n\n"
                f"## References\n{sources_list}\n"
            )

        return state
