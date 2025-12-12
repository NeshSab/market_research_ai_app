"""Central registry for all tools in LangChain @tool format."""

from .web_search import web_search
from .market_regime import market_regime_analyzer
from .sector_strength import sector_strength_analyzer
from .market_holiday import market_holiday_checker
from .wikipedia_load import search_wikipedia
from .rag_search import search_knowledge_base
from .web_load import web_load
from .ticker_analysis import ticker_analyzer


def get_functions_for_openai(enable_web_search: bool = False) -> dict:
    """
    Return tool mapping for LangChain function calling.
    
    Parameters
    ----------
    enable_web_search : bool, default False
        Whether to include web search tool in the registry
        
    Returns
    -------
    dict
        Mapping of function names to LangChain tool functions
    """
    available_tools = [
        search_knowledge_base,
        market_regime_analyzer,
        sector_strength_analyzer,
        ticker_analyzer,
        market_holiday_checker,
        search_wikipedia,
        web_load,
    ]

    if enable_web_search:
        available_tools.append(web_search)

    tool_map = {func.name: func for func in available_tools}

    return tool_map
