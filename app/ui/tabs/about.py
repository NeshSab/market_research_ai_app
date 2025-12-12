"""
About tab UI component for application information and setup.

This module renders the about page for the Market Intelligence Assistant,
providing users with application overview, getting started instructions,
and feature explanations.

Key content areas:
- Application overview and capabilities
- API key setup instructions
- Feature descriptions and use cases
- Version information and credits
"""

import streamlit as st


def render() -> None:
    """
    Render the About tab content.

    Displays application information, setup instructions, and
    feature overview for new and existing users.
    """

    st.header("📊 Market Intelligence Assistant")

    st.markdown(
        """
    **AI-powered financial analysis companion** that combines real-time
    market data, comprehensive sector analysis, and curated financial knowledge
    to provide professional-grade market insights.
    """
    )
    st.subheader("🔑 Getting Started")
    st.markdown(
        """
    **Required API Key:**
    - **OpenAI API Key**: For AI analysis and conversation (set in sidebar)
    - **FRED API Key**: For economic data access (set in sidebar)
    
    **Optional Enhancement:**
    - **Enable Web Search**: For real-time news and market updates (toggle in sidebar)
    """
    )
    st.subheader("🚀 What You Can Do")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        **📈 Market Analysis**
        - Real-time market regime classification
        - Sector performance rankings
        - Individual stock analysis
        
        **📊 Data Sources**
        - Live market data (SPX, VIX, DXY, Gold, UST)
        - Sector ETF performance tracking
        - Individual ticker fundamentals
        - Curated financial knowledge base
        """
        )

    with col2:
        st.markdown(
            """
        **🧠 AI Intelligence**
        - Professional financial analysis
        - Sector rotation insights
        - Market regime interpretation
        - Custom research queries
        
        **🔍 Knowledge Base**
        - Macro economic drivers
        - Sector analysis playbooks
        - Market indicators guide
        - Historical context & examples
        """
        )
    st.subheader("⏱️ Flexible Time Horizons")
    st.markdown(
        """
    Analysis tools support multiple timeframes: **1 week**, **1 month**,
    **3 months**, **6 months**, **1 year**
    """
    )

    st.subheader("💡 What to Ask Your AI Assistant")

    with st.expander("🔍 **Market Analysis Queries**", expanded=False):
        st.markdown(
            """
        - *"What's the current market regime and what does it mean for my portfolio?"*
        - *"Analyze sector performance over the past 3 months"*
        - *"Give me a complete analysis of AAPL over the last 6 months"*
        - *"Which sectors are outperforming and why?"*
        - *"What are the macro drivers affecting the market right now?"*
        """
        )

    with st.expander("📊 **Sector & Stock Research**", expanded=False):
        st.markdown(
            """
        - *"Compare technology vs healthcare sector performance this quarter"*
        - *"Why is the energy sector underperforming?"*
        - *"Analyze Tesla's recent performance vs the automotive sector"*
        - *"What's driving biotechnology sector strength?"*
        - *"Show me defensive sectors in the current market environment"*
        """
        )

    with st.expander("🌍 **Macro & Market Context**", expanded=False):
        st.markdown(
            """
        - *"How do rising interest rates affect different sectors?"*
        - *"What does a high VIX level mean for my investment strategy?"*
        - *"Explain the relationship between USD strength and commodity prices"*
        - *"What are the key economic events I should watch this month?"*
        - *"How does market regime classification work?"*
        """
        )

    with st.expander("📅 **Practical Trading/Investment**", expanded=False):
        st.markdown(
            """
        - *"What are the upcoming market holidays that might affect trading?"*
        - *"Give me a risk-on vs risk-off sector comparison"*
        - *"What should I know about current market conditions before investing?"*
        - *"Explain the current yield curve and its implications"*
        """
        )

    st.subheader("⚙️ Technical Features")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
        **🛠️ Analysis Tools:**
        - Market regime analyzer
        - Sector strength rankings
        - Individual ticker analysis
        - Knowledge base search
        - Wikipedia integration
        - Web search (optional)
        """
        )

    with col2:
        st.markdown(
            """
        **📋 Period Options:**
        - 1 week analysis
        - 1 month analysis
        - 3 month analysis
        - 6 month analysis
        - 1 year analysis
        """
        )

    st.subheader("🔒 Privacy & Security")
    st.markdown(
        """
    - **Local Session Storage**: All data stays in your browser session
    - **No Data Collection**: Your conversations and API keys are not stored server-side
    - **Secure API Usage**: Your OpenAI API key is used directly from your browser
    - **Real-time Analysis**: Fresh market data for every query
    """
    )

    st.subheader("🤝 Support")
    st.markdown(
        """
    This application provides professional-grade market intelligence for
    educational and research purposes.
    
    **Need Help?** Contact the developer for technical support.
    """
    )

    st.markdown("---")
    st.caption(
        "Market Intelligence Assistant • Built with Streamlit & OpenAI • "
        "Real-time Financial Data"
    )
