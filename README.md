# Market Intelligence Companion

An AI-powered financial analysis companion that combines real-time market data, comprehensive sector analysis, and curated financial knowledge to provide professional-grade market insights. Built with Streamlit and powered by OpenAI's GPT models with RAG (Retrieval-Augmented Generation) capabilities.

<br>

## Table of Contents
- [Introduction](#introduction)
- [How to Navigate](#how-to-navigate-this-repository)
- [Features](#features)
- [How to Run](#how-to-run)
- [Project Structure](#project-structure)
- [Further Improvements](#further-improvements)
- [Get Help](#get-help)
- [Contribution](#contribution)
<br>

## Introduction
This application helps users analyze financial markets through AI-powered insights combining real-time market data with curated financial knowledge. The system provides market regime analysis, sector performance rankings, individual ticker analysis, and interactive chat capabilities. It's designed for investors, analysts, and finance professionals who need comprehensive market intelligence with proper citations and sources.
<br>

## How to Navigate This Repository
- `app/`: Main Streamlit application and all core modules
  - `app.py`: Main application entry point
  - `core/`: Business logic, AI services, and data processing
  - `ui/`: Streamlit user interface components
  - `knowledge_base/`: Curated financial analysis frameworks and playbooks
- `pyproject.toml`: Project dependencies and configuration
- `125.md`: Technical requirements and project specifications
<br>

## Features
- **Market & Sector Overview Tab:** Real-time market regime classification, sector performance rankings with interactive charts, and comprehensive market analysis using multiple timeframes (1 week to 1 year).
- **AI Desk Tab:** Interactive chat with financial AI assistant powered by OpenAI GPT models, with access to 8 specialized tools including market analysis, sector strength, ticker analysis, and knowledge base search.
- **RAG Knowledge Base:** Curated financial knowledge base with sector analysis playbooks, macroeconomic drivers, and market analysis frameworks that can be expanded with custom documents.
- **Real-Time Data Integration:** Live market data from Yahoo Finance, economic indicators from FRED API, and optional web search for current financial news.
- **Advanced Tool Calling:** 8 specialized AI tools including market regime analyzer, sector strength analyzer, ticker analyzer, web search, Wikipedia search, market holiday checker, and knowledge base search.
- **Multi-Language Support:** AI responses in English, Spanish, French, and German with configurable response styles (concise/detailed).
- **Security & Validation:** Input sanitization, PII redaction, prompt injection detection, and content moderation for safe AI interactions.
- **Cost Tracking:** Real-time token usage monitoring and cost estimation across different OpenAI models.
- **Export Capabilities:** Conversation export in JSON, CSV, and PDF formats for record-keeping and sharing.
- **Customizable Analysis:** Flexible time horizons (1wk, 1mo, 3mo, 6mo, 1y) and configurable model parameters (temperature, top-p).
<br>

## How to Run
1. Clone the repository:
    ```bash
    git clone https://github.com/NeshSab/market_research_ai_app
    ```
2. Navigate to the project directory:
    ```bash
    cd market_research_ai_app
    ```
3. (Optional) Create and activate a Python virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  
    - On Windows: .venv\Scripts\activate
    ```
4. Install dependencies using pip:
    ```bash
    pip install -e .
    ```
   Or using uv (faster):
    ```bash
    uv sync
    ```
5. Navigate to app folder and run the application:
    ```bash
    cd app
    streamlit run app.py
    ```
6. Configure API keys in the sidebar:
   - **Required**: OpenAI API Key
   - **Required**: FRED API Key (for economic data)
   - **Optional**: LangSmith API Key (for tracing)
7. Enable web search in sidebar for real-time news integration (optional)
<br>

## Project Structure
```
├── app.py                          # Main Streamlit application entry point
├── ui/                             # User interface components
│   ├── tabs/                       # Main application tabs
│   │   ├── about.py                # About tab with feature overview
│   │   ├── ai_desk.py              # AI chat interface
│   │   └── market_sector_overview.py # Market analysis dashboard
│   ├── widgets/                    # Reusable UI components
│   │   ├── charts.py               # Financial chart components
│   │   └── exports.py              # Export functionality
│   ├── sidebar.py                  # Configuration sidebar
│   ├── state.py                    # Session state management
│   ├── events.py                   # UI event handlers
│   └── utils.py                    # UI utility functions
├── core/                           # Business logic and AI services
│   ├── controller.py               # Main session orchestration
│   ├── models.py                   # Data classes and types
│   ├── interfaces.py               # Protocol definitions
│   ├── analyzers/                  # Market analysis modules
│   │   └── regime.py               # Market regime classification
│   ├── prompts/                    # AI prompt templates
│   │   ├── ai_desk.py              # Chat system prompts
│   │   ├── market_analysis.py      # Market analysis prompts
│   │   ├── ticker_analysis.py      # Stock analysis prompts
│   │   ├── rag_queries.py          # Knowledge base queries
│   │   ├── tools/                  # Tool-specific prompts
│   │   └── security/               # Security-related prompts
│   ├── services/                   # Core AI and data services
│   │   ├── llm_openai.py           # OpenAI API client wrapper
│   │   ├── rag_store.py            # Vector database management
│   │   ├── retrievers.py           # Semantic search and RAG fusion
│   │   ├── market_data.py          # Financial data integration
│   │   ├── security.py             # Input validation and safety
│   │   ├── pricing.py              # Token usage and cost tracking
│   │   ├── logging_setup.py        # Logging configuration
│   │   └── rate_limit.py           # API rate limiting
│   └── tools/                      # AI function calling tools
│       ├── registry.py             # Tool registration
│       ├── market_regime.py        # Market analysis tool
│       ├── sector_strength.py      # Sector performance tool
│       ├── ticker_analysis.py      # Stock analysis tool
│       ├── rag_search.py           # Knowledge base search
│       ├── web_search.py           # Real-time web search
│       ├── web_load.py             # Web content loading
│       ├── wikipedia_load.py       # Wikipedia integration
│       └── market_holiday.py       # Market calendar tool
├── knowledge_base/                 # Curated financial knowledge
│   ├── configs/                    # Configuration files
│   ├── examplars/                  # Analysis examples
│   ├── governance/                 # Usage policies
│   ├── playbooks/                  # Analysis frameworks
│   └── semistatic/                 # Static reference data
├── var/                            # Runtime data
│   └── faiss_index/                # Vector database storage
└── logs/                           # Application logs
```
<br>

## Further Improvements
- **Enhanced Export:** PDF export with nicer document formatting and professional layout
- **Security Enhancements:** Add security measures around user uploaded files/URLs and web content loading
- **Knowledge Base Analytics:** Return and display which knowledge chunks were used in responses for transparency
- **Market Regime Detection:** Implement more sophisticated market regime classification using trend analysis and multiple indicators instead of simple percentage differences
- **Full Multi-Language Support:** Adapt entire UI per chosen language, not just AI desk chat responses
- **Enhanced Charts:** Add real price values in chart tooltips for better user experience
- **Smart Sector Mapping:** Implement smarter sector ETF mapping to avoid defaulting to technology when sector doesn't match knowledge base
- **Sequential Tool Usage:** Enable tools to call other tools for more sophisticated analysis workflows
- **Configuration Management:** Centralize all hardcoded values in a config file, including default values in ui/state.py
- **Cost-Aware RAG:** Account for embedding and retrieval costs when building vector database and performing searches
- **Advanced RAG Strategies:** Implement RAPTOR hierarchical indexing, ColBERT retrieval, or A/B testing for different strategies
<br>

## Get Help
If you encounter any issues or have questions about this project, feel free to reach out:
- **Open an Issue**: If you find a bug or have a feature request, please open an issue on GitHub
- **Email**: For personal or specific questions: agneska.sablovskaja@gmail.com
- **Documentation**: Check the About tab in the application for detailed usage instructions
<br>

## Contribution
Contributions are welcome and appreciated! Here's how you can get involved:
1. **Reporting Bugs**: Open an issue with detailed information, steps to reproduce, and your environment details
2. **Suggesting Enhancements**: Describe your feature suggestion and provide context for why it would be useful
3. **Code Contributions**: 
   - Fork the repository
   - Create a feature branch
   - Follow the existing code style and documentation standards
   - Add type hints and comprehensive numpydoc-style documentation
   - Test your changes thoroughly
   - Submit a pull request with clear description of changes