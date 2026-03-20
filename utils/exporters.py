"""
Export utilities for research reports
"""
from typing import Dict, Any, Optional, Tuple
import json
import markdown
from datetime import datetime


def export_markdown(state: Dict[str, Any]) -> str:
    """Export research report as Markdown"""
    report = state.get("final_report", "")
    if not report:
        # Generate from state if no final report
        report = generate_markdown_from_state(state)
    return report


def generate_markdown_from_state(state: Dict[str, Any]) -> str:
    """Generate markdown report from state"""
    md = f"# Research Report: {state.get('topic', 'Untitled')}\n\n"
    
    # Metadata
    md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += f"**Quality Score:** {state.get('quality_score', 0.0):.2f}\n\n"
    md += f"**Sources:** {len(state.get('sources', []))}\n\n"
    
    # Outline
    if state.get("outline"):
        md += "## Outline\n\n"
        md += state["outline"] + "\n\n"
    
    # Research Notes
    if state.get("research_notes"):
        md += "## Research Notes\n\n"
        for i, note in enumerate(state.get("research_notes", []), 1):
            md += f"### Note {i}\n\n"
            if isinstance(note, dict):
                md += f"**Topic:** {note.get('topic', 'N/A')}\n\n"
                md += f"{note.get('content', '')}\n\n"
            else:
                md += f"{note}\n\n"
    
    # Final Report
    if state.get("final_report"):
        md += "## Final Report\n\n"
        md += state["final_report"] + "\n\n"
    
    # Sources
    sources = state.get("sources", [])
    if sources:
        md += "## References\n\n"
        for i, source in enumerate(sources, 1):
            md += f"{i}. **{source.get('title', 'Untitled')}**\n"
            md += f"   - URL: {source.get('url', 'N/A')}\n"
            md += f"   - Credibility: {source.get('credibility_score', 0.0):.2f}\n"
            md += f"   - Type: {source.get('source_type', 'unknown')}\n\n"
    
    return md


def export_html(state: Dict[str, Any]) -> str:
    """Export research report as HTML"""
    md_content = export_markdown(state)
    html = markdown.markdown(md_content, extensions=['extra', 'codehilite'])
    
    # Wrap in styled HTML
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Research Report: {state.get('topic', 'Untitled')}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            h3 {{ color: #555; }}
            code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
            pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            blockquote {{ border-left: 4px solid #3498db; margin-left: 0; padding-left: 20px; color: #555; }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """
    return html_template


def export_json(state: Dict[str, Any]) -> str:
    """Export research state as JSON"""
    # Create exportable state (remove any non-serializable objects)
    export_state = {
        "topic": state.get("topic"),
        "research_notes": state.get("research_notes", []),
        "outline": state.get("outline"),
        "sources": state.get("sources", []),
        "citations": state.get("citations", []),
        "quality_score": state.get("quality_score", 0.0),
        "final_report": state.get("final_report"),
        "metadata": {
            "research_start_time": state.get("research_start_time"),
            "research_end_time": state.get("research_end_time"),
            "research_iteration": state.get("research_iteration", 0),
            "model_name": state.get("model_name"),
            "template_type": state.get("template_type"),
            "exported_at": datetime.now().isoformat()
        }
    }
    
    return json.dumps(export_state, indent=2, ensure_ascii=False)


def export_pdf(state: Dict[str, Any]) -> bytes:
    """Export research report as PDF (requires weasyprint or reportlab)"""
    try:
        from weasyprint import HTML
        html_content = export_html(state)
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as e:
        # Fallback to reportlab if weasyprint not available or DLL missing
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from io import BytesIO
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            story.append(Paragraph(f"<b>Research Report: {state.get('topic', 'Untitled')}</b>", styles['Title']))
            story.append(Spacer(1, 12))
            
            # Add content
            if state.get("final_report"):
                for line in state["final_report"].split("\n"):
                    if line.strip():
                        story.append(Paragraph(line, styles['Normal']))
                        story.append(Spacer(1, 6))
            
            doc.build(story)
            return buffer.getvalue()
        except ImportError:
            raise ImportError("PDF export requires either 'weasyprint' or 'reportlab' package")


def export_report(state: Dict[str, Any], format: str = "markdown") -> Tuple[str, bytes]:
    """Export report in specified format"""
    format = format.lower()
    
    if format == "markdown":
        return export_markdown(state), b""
    elif format == "html":
        return export_html(state), b""
    elif format == "json":
        return export_json(state), b""
    elif format == "pdf":
        pdf_bytes = export_pdf(state)
        return "", pdf_bytes
    else:
        raise ValueError(f"Unsupported export format: {format}")
