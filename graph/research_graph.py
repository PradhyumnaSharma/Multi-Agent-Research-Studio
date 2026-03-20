"""
LangGraph workflow for Multi-Agent Research Studio
"""
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.researcher import ResearcherAgent
from agents.critic import CriticAgent
from agents.writer import WriterAgent
from utils.state import ResearchState, ResearchStatus


class ResearchGraph:
    """Main research workflow graph"""
    
    def __init__(self, model_name: str = "llama-3.1-70b-versatile"):
        self.model_name = model_name
        self.researcher = ResearcherAgent(model_name)
        self.critic = CriticAgent(model_name)
        self.writer = WriterAgent(model_name)
        
        # Create graph
        self.graph = self._build_graph()
        
        # Create checkpointer
        self.checkpointer = MemorySaver()
        
        # Compile graph with checkpointer and interrupt at human_approval
        self.app = self.graph.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human_approval"]  # Interrupt before human approval
        )
    
    def _build_graph(self) -> StateGraph:
        """Build the research workflow graph"""
        workflow = StateGraph(ResearchState)
        
        # Add nodes
        workflow.add_node("researcher", self.researcher.research)
        workflow.add_node("critic", self.critic.evaluate)
        workflow.add_node("human_approval", self._human_approval_node)
        workflow.add_node("writer", self.writer.write_report)
        
        # Set entry point
        workflow.set_entry_point("researcher")
        
        # Add edges
        workflow.add_edge("researcher", "critic")
        
        # Conditional edge from critic
        workflow.add_conditional_edges(
            "critic",
            self._should_refine,
            {
                "refine": "researcher",
                "approve": "human_approval"
            }
        )
        
        # Conditional edge from human approval
        workflow.add_conditional_edges(
            "human_approval",
            self._after_human_approval,
            {
                "write": "writer",
                "refine": "researcher"
            }
        )
        
        # End after writer
        workflow.add_edge("writer", END)
        
        return workflow
    
    def _should_refine(self, state: ResearchState) -> Literal["refine", "approve"]:
        """Determine if research needs refinement or can proceed to approval"""
        print("[Graph] Edge check: checking if we should refine or approve...")
        
        # If there's an error, stop refining and pause for human review
        if state.get("error_message"):
            print("[Graph] Routing to 'approve' (human_approval) because of an error state.")
            return "approve"
            
        feedback = state.get("critic_feedback", "")
        has_feedback = bool(feedback and feedback.strip())
        
        # If there's feedback, we need to refine
        if has_feedback:
            print("[Graph] Routing to 'refine' (researcher) due to existing feedback.")
            return "refine"
        
        # Check if we have an outline (means research is sufficient)
        outline = state.get("outline", "")
        if outline and outline.strip():
            print("[Graph] Routing to 'approve' (human_approval) because outline exists.")
            return "approve"
        
        # Default to refine if unclear
        print("[Graph] Defaulting route to 'refine'.")
        return "refine"
    
    def _human_approval_node(self, state: ResearchState) -> ResearchState:
        """Human approval node - this will be interrupted in Streamlit"""
        # This node just marks that we're waiting for approval
        # The actual approval happens via Streamlit UI and graph.stream()
        print("[Graph] Entering 'human_approval' node. Setting status to AWAITING_APPROVAL.")
        state["status"] = ResearchStatus.AWAITING_APPROVAL
        return state
        
    def _after_human_approval(self, state: ResearchState) -> Literal["write", "refine"]:
        """Determine what to do after human review of outline."""
        if state.get("is_approved"):
            print("[Graph] Outline approved. Routing to 'writer'.")
            return "write"
        else:
            print("[Graph] Outline rejected. Routing back to 'researcher'.")
            return "refine"
    
    def get_graph(self):
        """Get the compiled graph application"""
        return self.app
