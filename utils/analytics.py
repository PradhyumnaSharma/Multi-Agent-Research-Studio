"""
Analytics and metrics utilities for research studio
"""
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd


def calculate_research_metrics(state: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate comprehensive research metrics"""
    metrics = {
        "total_sources": len(state.get("sources", [])),
        "total_notes": len(state.get("research_notes", [])),
        "total_citations": len(state.get("citations", [])),
        "research_iterations": state.get("research_iteration", 0),
        "quality_score": state.get("quality_score", 0.0),
        "refinement_cycles": len(state.get("refinement_history", [])),
        "agent_actions_count": len(state.get("agent_actions", [])),
    }
    
    # Calculate time metrics
    if state.get("research_start_time") and state.get("research_end_time"):
        start = datetime.fromisoformat(state["research_start_time"])
        end = datetime.fromisoformat(state["research_end_time"])
        metrics["research_duration_seconds"] = (end - start).total_seconds()
    elif state.get("research_start_time"):
        start = datetime.fromisoformat(state["research_start_time"])
        now = datetime.now()
        metrics["research_duration_seconds"] = (now - start).total_seconds()
    else:
        metrics["research_duration_seconds"] = 0
    
    # Source type distribution (always web)
    metrics["source_type_distribution"] = {}
    metrics["average_source_credibility"] = 0.0
    
    # Agent activity breakdown
    agent_actions = state.get("agent_actions", [])
    if agent_actions:
        agent_activity = {}
        for action in agent_actions:
            agent = action.get("agent", "unknown")
            agent_activity[agent] = agent_activity.get(agent, 0) + 1
        metrics["agent_activity"] = agent_activity
    else:
        metrics["agent_activity"] = {}
    
    return metrics


def get_research_timeline(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get chronological timeline of research activities"""
    timeline = []
    
    # Add agent actions
    for action in state.get("agent_actions", []):
        timeline.append({
            "timestamp": action.get("timestamp"),
            "event": f"{action.get('agent')}: {action.get('action')}",
            "type": "action",
            "details": action.get("details", {})
        })
    
    # Add refinement cycles
    for i, refinement in enumerate(state.get("refinement_history", [])):
        timeline.append({
            "timestamp": refinement.get("timestamp", ""),
            "event": f"Refinement Cycle {i + 1}",
            "type": "refinement",
            "details": refinement
        })
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x.get("timestamp", ""))
    
    return timeline


def get_quality_breakdown(state: Dict[str, Any]) -> Dict[str, float]:
    """Break down quality score into components"""
    sources = state.get("sources", [])
    notes = state.get("research_notes", [])
    citations = state.get("citations", [])
    
    breakdown = {
        "Source Count": min(len(sources) / 5, 0.4),
        "Note Completeness": min(len(notes) / 5, 0.3),
        "Outline Quality": 0.2 if state.get("outline") else 0.0,
        "Citation Count": min(len(citations) / 5, 0.1)
    }
    
    return breakdown


def prepare_analytics_dataframe(state: Dict[str, Any]) -> pd.DataFrame:
    """Prepare pandas DataFrame for analytics visualization"""
    agent_actions = state.get("agent_actions", [])
    
    if not agent_actions:
        return pd.DataFrame()
    
    data = []
    for action in agent_actions:
        data.append({
            "timestamp": action.get("timestamp"),
            "agent": action.get("agent"),
            "action": action.get("action"),
            "details": str(action.get("details", {}))
        })
    
    df = pd.DataFrame(data)
    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    
    return df
