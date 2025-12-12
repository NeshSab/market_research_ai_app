"""
Market and sector overview tab for comprehensive market analysis visualization.

This module provides a comprehensive dashboard view of current market conditions,
sector performance analysis, and individual ticker deep-dive capabilities.
It integrates real-time market data with interactive charts and analysis tools.

The interface displays market regime indicators, sector strength rankings,
and provides comparative analysis tools for investment decision-making.
Users can explore market conditions across multiple timeframes and drill
down into specific sectors and individual securities.

Key features:
- Real-time market regime visualization
- Interactive sector performance charts
- Individual ticker analysis and comparison
- Multi-timeframe analysis capabilities
- Professional market dashboard interface
"""

import streamlit as st

from core.services.market_data import (
    get_index_snap,
    get_sector_perf,
    get_ticker_samples,
    load_sector_data,
)
from ui.widgets.charts import market_regime_chart, sector_bar, ticker_comparison_chart
from ui.state import ui_session_state


def render(index_path: str) -> None:
    ui_state = ui_session_state()
    market_analysis = ui_state.market_analysis_config
    analysis_period = market_analysis["default_period"].get("period", "1wk")
    analysis_period_name = market_analysis["default_period"].get("full_name", "1 Week")
    analysis_period_name_alt = market_analysis["default_period"].get(
        "alternative_name", "5 Trading Days"
    )
    market_indicators = market_analysis["core_indicators"].get("indicators", [])
    if not ui_state.api_key_set:
        st.info("Please initialize API keys in the sidebar first.")
        return

    if not ui_state.controller:
        st.error("Controller not initialized. Please reset session.")
        return

    st.header("📈 Market & Sector Overview")
    with st.expander("ℹ️ Analysis Method Explained", expanded=False):
        st.markdown(
            f"""
        ### **📊 All Analysis Uses {analysis_period_name} ({analysis_period_name_alt}) Data**
        
        **Market Regime Detection:**
        - SPX, VIX, DXY, 10Y Yield changes over
        - Captures genuine market momentum without daily noise
        
        **Sector Strength Rankings:**
        - All sectors compared on 1-week performance basis
        - Consistent timeframe for meaningful comparisons
        
        **Individual Stock Analysis:**
        - Ticker performance vs sector/market
        - Outperformance metrics on consistent time basis
        
        ### **📈 Chart Display Period (User Choice)**
        
        Select timeframe below to view price charts with broader context:
        - **1wk**: Focused view aligned with analysis
        - **1mo**: See recent trends and patterns
        - **3mo**: Quarterly perspective
        - **6mo**: Half-year trends
        - **1y**: Full year context
        
        **Analysis stays consistent ({analysis_period_name} data),
         charts provide context.**
        """
        )
    period = st.selectbox(
        "📈 Chart Display Period",
        ["1wk", "1mo", "3mo", "6mo", "1y"],
        index=2,
        key="chart_display_period",
        help=(
            f"Period for price charts only. All analysis uses "
            f"{analysis_period_name} data."
        ),
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        run_analysis = st.button("🔄 Run Analysis", type="primary", width="stretch")
    with col2:
        if ui_state.last_market_pulse:
            clear_analysis = st.button("🗑️ Clear", width="stretch")
        else:
            clear_analysis = False

    if run_analysis:
        with st.spinner(f"Analyzing {analysis_period_name} market trends..."):
            ctrl = ui_state.controller
            result = ctrl.run_market_pulse(
                index_path=index_path, period=analysis_period
            )

            ui_state.last_market_pulse = result
            ui_state.last_pulse_period = period

            idx_df = get_index_snap(tickers=market_indicators, period=period)
            ui_state.last_pulse_chart_data = idx_df[market_indicators].dropna()

            ui_state.last_sector_data = get_sector_perf(period=analysis_period)
            ui_state.show_ticker_dive = False

        st.rerun()

    if clear_analysis:
        ui_state.last_market_pulse = None
        ui_state.last_pulse_period = "3mo"
        ui_state.last_pulse_chart_data = None
        ui_state.last_sector_data = None
        ui_state.show_ticker_dive = False
        st.rerun()

    if ui_state.last_market_pulse:
        result = ui_state.last_market_pulse
        display_period = ui_state.last_pulse_period

        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("Analysis Period", f"{analysis_period_name}")
        with col2:
            st.metric("Chart Display", display_period)

        st.caption(
            f"All market analysis uses consistent {analysis_period_name_alt} data. "
            "Charts show broader context."
        )
        st.divider()

        # ========== MARKET PULSE SECTION ==========
        st.subheader(f"🌍 Market Regime: {result.detected_regime}")
        st.write(result.global_summary)

        if ui_state.last_pulse_chart_data is not None:
            chart_title = market_analysis.get("core_indicators", {}).get(
                "chart_name", "Market Indicators"
            )
            st.plotly_chart(
                market_regime_chart(
                    ui_state.last_pulse_chart_data,
                    chart_title,
                ),
                width="stretch",
            )

        st.divider()

        st.subheader("Sector Strength")
        st.caption(
            f"Top performing sector ETFs over the last {analysis_period_name_alt}"
        )
        st.markdown("**Top AI-Selected Sectors:**")
        for s in result.sectors:
            st.write(f"- **{s.sector}** ({s.change_pct:.1f}%) → {', '.join(s.tickers)}")
            if s.reasoning:
                st.caption(f"  _{s.reasoning}_")

        if ui_state.last_sector_data is not None:
            df = ui_state.last_sector_data
        else:
            df = get_sector_perf(period=analysis_period)
            ui_state.last_sector_data = df

        st.plotly_chart(sector_bar(df), width="stretch")

        samples = get_ticker_samples()
        sector_data = load_sector_data()
        with st.expander("📋 Representative Tickers by ETF Sector"):
            for _, r in df.iterrows():
                etf_symbol = r["sector"]
                tickers = samples.get(etf_symbol, [])
                sector_info = sector_data.get(etf_symbol, {})
                sector_name = sector_info.get("sector_name", etf_symbol)
                display_name = f"{etf_symbol} ({sector_name})"

                st.write(
                    f"**{display_name}** ({r['return']:.1%}): "
                    f"{', '.join(tickers) if tickers else 'N/A'}"
                )
        with st.expander("📚 Sources & Citations"):
            for c in result.citations:
                st.write(f"- {c}")

        st.divider()

        # ========== TICKER DEEP DIVE SECTION ==========
        if not ui_state.show_ticker_dive:
            if st.button("🔍 Ticker Deep Dive", type="secondary", width="stretch"):
                ui_state.show_ticker_dive = True
                st.rerun()

        if ui_state.show_ticker_dive:
            st.subheader("🔍 Ticker Deep Dive")
            st.caption(
                f"Analyze individual stock performance over the last "
                f"{analysis_period_name_alt}. More than one ticker supported. "
                f"Add and analyze one by one."
            )

            ticker_col1, ticker_col2 = st.columns([3, 1])
            with ticker_col1:
                ticker = (
                    st.text_input(
                        "Enter ticker symbol",
                        value="AAPL",
                        key="ticker_input",
                    )
                    .strip()
                    .upper()
                )

            with ticker_col2:
                st.write("")
                st.write("")
                analyze_ticker = st.button("Analyze", type="primary", width="stretch")

            if analyze_ticker and ticker:
                with st.spinner(f"Analyzing {ticker}..."):
                    ctrl = ui_state.controller
                    ticker_info = ctrl.run_ticker_deep_dive(
                        index_path=index_path, ticker=ticker, period=analysis_period
                    )
                    if ticker_info.analysis.startswith("Error:"):
                        st.error(f"⚠️ {ticker_info.analysis}")
                    else:
                        ui_state.ticker_analyses.append(
                            {"ticker": ticker, "info": ticker_info}
                        )
                        st.rerun()

            if ui_state.ticker_analyses:
                st.markdown("---")
                st.markdown("### Analyzed Tickers")

                for idx, analysis_item in enumerate(ui_state.ticker_analyses):
                    ticker_symbol = analysis_item["ticker"]
                    ticker_data = analysis_item["info"]

                    with st.expander(
                        f"**{ticker_symbol}** - {ticker_data.company_name}",
                        expanded=(idx == len(ui_state.ticker_analyses) - 1),
                    ):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                f"{ticker_symbol} Return",
                                f"{ticker_data.ticker_return:.2f}%",
                                f"{ticker_data.outperformance_vs_spx:+.2f}% vs S&P",
                            )
                        with col2:
                            st.metric(
                                f"{ticker_data.sector} Sector",
                                f"{ticker_data.sector_return:.2f}%",
                            )
                        with col3:
                            st.metric(
                                "S&P 500",
                                f"{ticker_data.spx_return:.2f}%",
                            )

                        ticker_sector = ticker_data.sector.capitalize()
                        if ticker_data.comparison_data is not None:

                            st.plotly_chart(
                                ticker_comparison_chart(
                                    ticker_data.comparison_data,
                                    f"{ticker_symbol} vs "
                                    f"{ticker_sector} Sector vs S&P 500",
                                ),
                                width="stretch",
                            )

                        st.markdown("**AI Analysis:**")
                        st.write(ticker_data.analysis)

                        if ticker_data.fundamentals:
                            with st.expander("📊 Fundamentals"):
                                fund = ticker_data.fundamentals
                                fcol1, fcol2 = st.columns(2)
                                with fcol1:
                                    st.metric("P/E Ratio", fund.get("pe_ratio", "N/A"))
                                    st.metric("Beta", fund.get("beta", "N/A"))
                                    st.metric(
                                        "Div Yield",
                                        f"{fund.get('dividend_yield', 'N/A')}",
                                    )
                                with fcol2:
                                    st.metric(
                                        "Market Cap",
                                        (
                                            f"${fund.get('market_cap', 0):,.0f}"
                                            if isinstance(
                                                fund.get("market_cap"), (int, float)
                                            )
                                            else "N/A"
                                        ),
                                    )
                                    st.metric("52W High", fund.get("52w_high", "N/A"))
                                    st.metric("52W Low", fund.get("52w_low", "N/A"))

                        if ticker_data.citations:
                            st.caption("**Citations:**")
                            for c in ticker_data.citations:
                                st.caption(f"- {c}")

    else:
        st.info("👆 Click **Run Analysis** to generate market insights")
