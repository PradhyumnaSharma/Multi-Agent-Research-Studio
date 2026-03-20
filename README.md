# 🔬 Multi-Agent Research Studio

A comprehensive, production-ready Python application for autonomous multi-agent research using LangGraph, Groq API, and Streamlit.

## 🌟 Features

### Core Capabilities
- **Multi-Agent Workflow**: Researcher, Critic, and Writer agents working collaboratively
- **Intelligent Research**: Automated web research using DuckDuckGo
- **Quality Evaluation**: AI-powered research quality assessment and refinement
- **Human-in-the-Loop**: Interactive approval workflow for research outlines
- **State Persistence**: Checkpointing with MemorySaver for session continuity

### Advanced Features
- **Real-time Analytics Dashboard**: Quality scores, source distribution, agent activity
- **Research Timeline**: Chronological view of research activities
- **Source Management**: Credibility scoring and source validation
- **Multiple Export Formats**: Markdown, HTML, JSON, and PDF
- **Research Templates**: Academic, Business, Technical, and Custom templates
- **Session Management**: Persistent research sessions with thread IDs
- **Interactive UI**: Beautiful Streamlit interface with real-time updates

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **Groq API Key** (free tier available)

### Step 1: Get Groq API Key

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up or log in (free account)
3. Navigate to **API Keys** section
4. Click **Create API Key**
5. Copy your API key

### Step 2: Set Up Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
DEFAULT_MODEL=llama-3.1-70b-versatile
```

**Note**: Never commit your `.env` file to version control!

### Step 3: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## 📁 Project Structure

```
Langraph_project/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── agents/
│   ├── __init__.py
│   ├── researcher.py     # Research agent
│   ├── critic.py         # Quality evaluation agent
│   └── writer.py         # Report generation agent
├── graph/
│   ├── __init__.py
│   └── research_graph.py # LangGraph workflow
└── utils/
    ├── __init__.py
    ├── state.py          # State management
    ├── analytics.py      # Analytics utilities
    └── exporters.py      # Export utilities
```

## 🎯 Usage Guide

### Starting a Research Session

1. **Enter Research Topic**: Type your research topic in the input field
2. **Configure Settings** (Sidebar):
   - Select LLM model (llama-3.1-70b-versatile, mixtral-8x7b-32768, etc.)
   - Choose research depth (quick, standard, comprehensive)
   - Select report template (academic, business, technical, custom)
3. **Start Research**: Click "🚀 Start Research"
4. **Monitor Progress**: Watch real-time research activity in the log
5. **Review Outline**: When research is complete, review the generated outline
6. **Approve & Generate**: Click "Approve & Write Report" to generate final report
7. **Export**: Export your report in various formats (Markdown, HTML, JSON, PDF)

### Understanding the Workflow

1. **Researcher Agent**: Conducts web searches and gathers information
2. **Critic Agent**: Evaluates research quality
   - If insufficient → Provides feedback → Routes back to Researcher
   - If sufficient → Generates outline → Routes to Human Approval
3. **Human Approval**: You review and approve the outline
4. **Writer Agent**: Generates the final comprehensive report

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Groq Configuration
GROQ_API_KEY=your_groq_api_key_here
DEFAULT_MODEL=llama-3.1-70b-versatile
FALLBACK_MODEL=mixtral-8x7b-32768

# LLM Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Research Configuration
MAX_RESEARCH_ITERATIONS=5
MIN_SOURCES_REQUIRED=3
MAX_SEARCH_RESULTS=10
RESEARCH_DEPTH=comprehensive

# Quality Thresholds
MIN_QUALITY_SCORE=0.7
MIN_SOURCE_CREDIBILITY=0.5
```

### Customization

- **Research Templates**: Modify `RESEARCH_TEMPLATES` in `config.py`
- **Quality Thresholds**: Adjust in `config.py` or `.env`
- **Agent Behavior**: Customize prompts in agent files

## 🔧 Troubleshooting

### Groq API Key Issues

```bash
# Verify your API key is set
echo $GROQ_API_KEY  # Linux/Mac
echo %GROQ_API_KEY%  # Windows

# Check .env file exists and contains GROQ_API_KEY
```

### API Rate Limits

Groq free tier has generous limits. If you hit rate limits:
- Wait a few minutes and retry
- Consider upgrading to paid tier for higher limits
- Check your usage at https://console.groq.com

### Model Not Available

Available Groq models:
- `llama-3.1-70b-versatile` (recommended)
- `llama-3.1-8b-instant` (faster)
- `mixtral-8x7b-32768` (alternative)
- `gemma2-9b-it` (alternative)

### Import Errors

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt --upgrade
```

### PDF Export Issues

PDF export requires either `weasyprint` or `reportlab`:

```bash
# Option 1: Install weasyprint (recommended)
pip install weasyprint

# Option 2: Install reportlab
pip install reportlab
```

## 📊 Features in Detail

### Analytics Dashboard

- **Quality Metrics**: Real-time quality score calculation
- **Source Analysis**: Source type distribution and credibility scores
- **Agent Activity**: Breakdown of agent actions
- **Timeline Visualization**: Chronological research activity

### Export Options

- **Markdown**: Standard markdown format
- **HTML**: Styled HTML with embedded CSS
- **JSON**: Complete state export for programmatic use
- **PDF**: Professional PDF reports (requires additional package)

### Research Templates

- **Academic**: Structured for academic papers
- **Business**: Professional business reports
- **Technical**: Technical documentation style
- **Custom**: Flexible template for any use case

## 🤝 Contributing

This is a production-ready template. Feel free to:
- Add new agents
- Enhance search capabilities
- Improve UI/UX
- Add new export formats
- Integrate additional data sources

## 📝 License

This project uses open-source technologies. All dependencies are open-source.

## 🙏 Acknowledgments

- **LangGraph**: For workflow orchestration
- **LangChain**: For LLM integration
- **Groq**: For fast cloud-based LLM inference
- **Streamlit**: For the beautiful UI framework
- **DuckDuckGo**: For search capabilities

## 🐛 Known Issues

- PDF export requires additional packages (weasyprint or reportlab)
- Search results parsing may vary based on DuckDuckGo response format
- Large research topics may take longer to process

## 📧 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the configuration options
3. Ensure Ollama is running and models are available

---

**Built with ❤️ using LangGraph, Ollama, and Streamlit**
