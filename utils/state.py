"""
State management for the Research Studio
"""
from typing import TypedDict, List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class ResearchStatus(str, Enum):
    """Research status enumeration"""
    INITIALIZED = "initialized"
    RESEARCHING = "researching"
    REVIEWING = "reviewing"
    AWAITING_APPROVAL = "awaiting_approval"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"


class Source(TypedDict):
    """Source information structure"""
    title: str
    url: str
    snippet: str
    retrieved_at: str


class ResearchState(TypedDict):
    """Main state for the research graph"""
    # Core fields
    topic: str
    research_notes: List[Dict[str, Any]]
    critic_feedback: str
    outline: str
    is_approved: bool

    # Enhanced fields
    sources: List[Source]
    citations: List[Dict[str, Any]]
    quality_score: float
    research_iteration: int
    status: str
    error_message: Optional[str]

    # Analytics
    research_start_time: Optional[str]
    research_end_time: Optional[str]
    agent_actions: List[Dict[str, Any]]
    refinement_history: List[Dict[str, Any]]

    # Configuration
    research_depth: str
    template_type: str
    model_name: str

    # Final output
    final_report: Optional[str]
    report_metadata: Optional[Dict[str, Any]]


def create_initial_state(
    topic: str,
    research_depth: str = "comprehensive",
    template_type: str = "academic",
    model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct"
) -> ResearchState:
    """Create initial research state"""
    return ResearchState(
        topic=topic,
        research_notes=[],
        critic_feedback="",
        outline="",
        is_approved=False,
        sources=[],
        citations=[],
        quality_score=0.0,
        research_iteration=0,
        status=ResearchStatus.INITIALIZED.value,
        error_message=None,
        research_start_time=datetime.now().isoformat(),
        research_end_time=None,
        agent_actions=[],
        refinement_history=[],
        research_depth=research_depth,
        template_type=template_type,
        model_name=model_name,
        final_report=None,
        report_metadata=None
    )


def add_agent_action(state: ResearchState, agent_name: str, action: str, details: Optional[Dict] = None) -> ResearchState:
    """Add an agent action to the state"""
    action_entry = {
        "agent": agent_name,
        "action": action,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    state["agent_actions"].append(action_entry)
    return state


def calculate_quality_score(state: ResearchState) -> float:
    """Calculate overall quality score based on various factors"""
    sources = state.get("sources", [])
    notes = state.get("research_notes", [])
    citations = state.get("citations", [])

    factors = {
        "source_count": min(len(sources) / 5, 0.4),
        "note_completeness": min(len(notes) / 5, 0.3),
        "outline_quality": 0.2 if state.get("outline") else 0.0,
        "citation_count": min(len(citations) / 5, 0.1)
    }

    score = sum(factors.values())
    return min(score, 1.0)
