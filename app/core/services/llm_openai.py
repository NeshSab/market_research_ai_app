"""
Purpose: Thin client wrapper around OpenAI (or other LLMs later).
One place for auth, retries, model options, response/usage normalization.

Extensibility:
- Add other providers (AnthropicLLM, LocalLLM) without touching controller.
- Add streaming support later (yield tokens) behind the same interface.

Testing: Mock SDK calls; assert it maps usage and errors correctly.
"""

from __future__ import annotations
from typing import Any, Optional, Union, Type
import tiktoken
import logging
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from pydantic import BaseModel

from core.models import LLMSettings
from core.interfaces import PromptFactory
from core.services.rate_limit import RateLimiter

session_store: dict[str, BaseChatMessageHistory] = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Get or create chat message history for a session.

    Parameters
    ----------
    session_id : str
        Unique identifier for the chat session

    Returns
    -------
    BaseChatMessageHistory
        Chat message history object for the session
    """
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]


class LLMClient:
    """
    OpenAI LLM client with rate limiting and caching.

    A thin wrapper around LangChain's ChatOpenAI that provides:
    - Centralized default settings and model selection
    - Plain text and structured response calls
    - Token usage metadata and estimates
    - Rate limiting integration
    - Response caching and session management
    - Tool calling and function routing capabilities

    The client supports multiple interaction patterns including simple
    prompts, structured output parsing, tool-enabled conversations,
    and session-based chat history.
    """

    def __init__(
        self,
        prompts: PromptFactory,
        default_settings: Optional[LLMSettings] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.prompts = prompts
        self._defaults = default_settings or LLMSettings()
        self._default_llm = ChatOpenAI(**self._defaults.as_kwargs())
        self._llm_cache: dict[str, ChatOpenAI] = {}
        self._rate_limiter = rate_limiter

    def _resolve_settings(self, settings: Union[LLMSettings, str, None]) -> LLMSettings:
        """
        Resolve settings parameter to LLMSettings object.

        Parameters
        ----------
        settings : Union[LLMSettings, str, None]
            Settings as object, model name string, or None for defaults

        Returns
        -------
        LLMSettings
        """
        if settings is None:
            return self._defaults
        if isinstance(settings, str):
            return LLMSettings(
                model=settings,
                temperature=self._defaults.temperature,
                top_p=self._defaults.top_p,
                max_tokens=self._defaults.max_tokens,
            )
        return settings

    def _get_or_create_llm(self, settings: LLMSettings) -> ChatOpenAI:
        """
        Get cached LLM or create new one if settings differ.
        """

        cache_key = (
            settings.model,
            settings.temperature,
            settings.top_p,
            settings.max_tokens,
        )

        if cache_key not in self._llm_cache:
            self._llm_cache[cache_key] = ChatOpenAI(**settings.as_kwargs())

        return self._llm_cache[cache_key]

    def _get_llm(self, settings: Optional[LLMSettings]) -> ChatOpenAI:
        """
        Get appropriate LLM instance with caching optimization.

        Returns default cached instance if settings match defaults,
        otherwise creates/caches instance for different settings.

        Parameters
        ----------
        settings : Optional[LLMSettings]
            LLM settings or None for defaults

        Returns
        -------
        ChatOpenAI
            Appropriate LLM instance (default or custom)
        """
        resolved_settings = self._resolve_settings(settings)
        if resolved_settings == self._defaults:
            return self._default_llm

        return self._get_or_create_llm(resolved_settings)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        settings: Union[LLMSettings, str, None] = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Perform basic chat completion with system and user prompts.

        Parameters
        ----------
        system_prompt : str
            System instruction prompt for AI behavior
        user_prompt : str
            User message or question
        settings : Union[LLMSettings, str, None], optional
            LLM settings, model name, or None for defaults

        Returns
        -------
        tuple[str, dict[str, Any]]
            Response text and metadata including token usage
        """
        if self._rate_limiter and not self._rate_limiter.allow():
            return (
                "Rate limit exceeded. Please wait before retrying.",
                {
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "model": "rate_limited",
                    "rate_limited": True,
                },
            )

        llm = self._get_llm(settings)
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", user_prompt),
            ]
        )
        captured_response = None

        def capture_response(ai_message) -> str:
            nonlocal captured_response
            captured_response = ai_message
            return ai_message.content or str(ai_message)

        chain = prompt_template | llm | RunnableLambda(capture_response)
        result_text = chain.invoke({})
        tokens_in, tokens_out = self._extract_token_usage(captured_response)

        meta = {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "model": llm.model_name,
        }
        return result_text, meta

    def chat_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[BaseModel],
        settings: Union[LLMSettings, str, None] = None,
    ) -> tuple[BaseModel, dict[str, Any]]:
        """
        Generate structured output using Pydantic schema validation.

        Parameters
        ----------
        system_prompt : str
            System instruction prompt for AI behavior
        user_prompt : str
            User message or question
        schema : Type[BaseModel]
            Pydantic model class for output structure validation
        settings : Union[LLMSettings, str, None], optional
            LLM settings, model name, or None for defaults

        Returns
        -------
        tuple[BaseModel, dict[str, Any]]
            Structured response object and metadata including token usage
        """
        if self._rate_limiter and not self._rate_limiter.allow():

            class RateLimitError(BaseModel):
                error: str = "Rate limit exceeded. Please wait a moment."

            return (
                RateLimitError(),
                {
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "model": "rate_limited",
                    "rate_limited": True,
                },
            )

        llm = self._get_llm(settings)
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", user_prompt),
            ]
        )

        captured_ai_message = None

        def capture_ai_message(ai_message) -> AIMessage:
            nonlocal captured_ai_message
            captured_ai_message = ai_message
            return ai_message

        raw_chain = prompt_template | llm | RunnableLambda(capture_ai_message)

        _ = raw_chain.invoke({})
        structured_llm = llm.with_structured_output(schema)
        structured_chain = prompt_template | structured_llm
        result = structured_chain.invoke({})

        tokens_in, tokens_out = self._extract_token_usage(captured_ai_message)

        meta = {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "model": llm.model_name,
        }
        return result, meta

    def chat_with_history(
        self,
        system_prompt: str,
        user_input: str,
        session_id: str,
        settings: Union[LLMSettings, str, None] = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Perform chat with persistent conversation history.

        Maintains conversation context across multiple interactions
        using session-based message history storage.

        Parameters
        ----------
        system_prompt : str
            System instruction prompt for AI behavior
        user_input : str
            Current user message or question
        session_id : str
            Unique identifier for conversation session
        settings : Union[LLMSettings, str, None], optional
            LLM settings, model name, or None for defaults

        Returns
        -------
        tuple[str, dict[str, Any]]
            Response text and metadata including session info and token usage
        """
        if self._rate_limiter and not self._rate_limiter.allow():
            return (
                "Rate limit exceeded. Please wait before retrying.",
                {
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "model": "rate_limited",
                    "session_id": session_id,
                    "rate_limited": True,
                },
            )

        llm = self._get_llm(settings)
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )
        chain = prompt_template | llm

        chain_with_history = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )
        captured_response = None

        def capture_and_extract_content(ai_message) -> str:
            nonlocal captured_response
            captured_response = ai_message
            return ai_message.content or str(ai_message)

        final_chain = chain_with_history | RunnableLambda(capture_and_extract_content)

        config = {"configurable": {"session_id": session_id}}
        result_text = final_chain.invoke(
            {"system_prompt": system_prompt, "input": user_input}, config=config
        )
        tokens_in, tokens_out = self._extract_token_usage(captured_response)

        meta = {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "model": llm.model_name,
            "session_id": session_id,
        }

        return result_text, meta

    def chat_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        settings: LLMSettings,
        tool_map: dict,
    ) -> tuple[str, dict]:
        """
        Perform chat with tool/function calling capabilities.

        Enables AI to call external tools and functions to gather
        information or perform actions. Uses current prompt only
        without conversation history for efficiency.

        Parameters
        ----------
        system_prompt : str
            System instruction prompt for AI behavior
        user_prompt : str
            User message or question
        settings : LLMSettings
            LLM configuration settings
        tool_map : dict
            Mapping of tool names to callable functions

        Returns
        -------
        tuple[str, dict]
            Final response text and metadata including tools used
        """
        if self._rate_limiter and not self._rate_limiter.allow():
            return (
                "Rate limit exceeded. Please wait before retrying.",
                {
                    "model": settings.model,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "tools_used": [],
                    "rate_limited": True,
                },
            )

        llm = self._get_llm(settings)
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", user_prompt),
            ]
        )

        tools_used = []
        tool_results = []
        captured_response = None

        def route_tools(ai_message) -> AIMessage:
            """Route to appropriate tool and collect results for final response"""
            nonlocal captured_response
            captured_response = ai_message

            if ai_message.tool_calls:
                for tool_call in ai_message.tool_calls:
                    function_name = tool_call["name"]
                    function_args = tool_call["args"]

                    if function_name not in tools_used:
                        tools_used.append(function_name)

                    if function_name in tool_map:
                        try:
                            tool_function = tool_map[function_name]
                            if isinstance(tool_function, BaseTool):
                                result = tool_function.run(function_args)
                            else:
                                result = tool_function(**function_args)
                            tool_results.append(
                                {
                                    "tool": function_name,
                                    "query": function_args,
                                    "result": result,
                                }
                            )

                        except Exception as e:
                            logging.error(f"Error executing tool {function_name}: {e}")
                            error_msg = f"Error executing {function_name}: {str(e)}"
                            tool_results.append(
                                {
                                    "tool": function_name,
                                    "query": function_args,
                                    "result": error_msg,
                                }
                            )
                    else:
                        error_msg = f"Error: Tool {function_name} not found"
                        tool_results.append(
                            {
                                "tool": function_name,
                                "query": function_args,
                                "result": error_msg,
                            }
                        )

                return self._generate_final_response(user_prompt, tool_results, llm)

            return ai_message.content or ""

        converted_tools = [
            convert_to_openai_function(func) for func in tool_map.values()
        ]
        model_with_tools = llm.bind_tools(converted_tools) if converted_tools else llm

        chain = prompt_template | model_with_tools | RunnableLambda(route_tools)
        try:
            result = chain.invoke({})
            tokens_in, tokens_out = self._extract_token_usage(captured_response)

            return result, {
                "model": settings.model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "tools_used": tools_used,
            }

        except Exception as e:
            return f"Error in tool execution: {str(e)}", {
                "model": settings.model,
                "tokens_in": 0,
                "tokens_out": 0,
                "tools_used": [],
            }

    def chat_with_tools_and_history(
        self,
        system_prompt: str,
        user_input: str,
        session_id: str,
        settings: LLMSettings,
        tool_map: dict,
    ) -> tuple[str, dict]:
        """
        Perform chat with both conversation history and tool calling.

        Combines persistent conversation context with tool/function
        calling capabilities for complex multi-turn interactions.

        Parameters
        ----------
        system_prompt : str
            System instruction prompt for AI behavior
        user_input : str
            Current user message or question
        session_id : str
            Unique identifier for conversation session
        settings : LLMSettings
            LLM configuration settings
        tool_map : dict
            Mapping of tool names to callable functions

        Returns
        -------
        tuple[str, dict]
            Response text and metadata including session info and tools used
        """
        if self._rate_limiter and not self._rate_limiter.allow():
            return (
                "Rate limit exceeded. Please wait before retrying.",
                {
                    "model": settings.model,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "tools_used": [],
                    "rate_limited": True,
                },
            )
        llm = self._get_llm(settings)
        converted_tools = [
            convert_to_openai_function(func) for func in tool_map.values()
        ]
        llm_with_tools = llm.bind_tools(converted_tools) if converted_tools else llm

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

        tools_used = []
        tool_results = []
        captured_response = None

        def route_tools(ai_message) -> AIMessage:
            nonlocal captured_response
            captured_response = ai_message

            if ai_message.tool_calls:
                for tool_call in ai_message.tool_calls:
                    function_name = tool_call["name"]
                    function_args = tool_call["args"]
                    tools_used.append(function_name)

                    try:
                        tool_fn = tool_map[function_name]
                        result = (
                            tool_fn.run(function_args)
                            if isinstance(tool_fn, BaseTool)
                            else tool_fn(**function_args)
                        )
                    except Exception as e:
                        result = f"Error: {str(e)}"

                    tool_results.append(
                        {
                            "tool": function_name,
                            "query": function_args,
                            "result": result,
                        }
                    )

                return self._generate_final_response(user_input, tool_results, llm)

            return ai_message.content or ""

        chain = prompt_template | llm_with_tools | RunnableLambda(route_tools)
        chain_with_history = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )

        final_chain = chain_with_history

        config = {"configurable": {"session_id": session_id}}

        try:
            result = final_chain.invoke(
                {"system_prompt": system_prompt, "input": user_input}, config=config
            )
            tokens_in, tokens_out = self._extract_token_usage(captured_response)

            return result, {
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "tools_used": tools_used,
                "model": llm.model_name,
                "session_id": session_id,
            }

        except Exception as e:
            logging.error(f"Error in tool + history execution: {e}")
            return f"Error: {str(e)}", {
                "tokens_in": 0,
                "tokens_out": 0,
                "tools_used": [],
                "model": llm.model_name,
                "session_id": session_id,
            }

    def _extract_token_usage(self, ai_message) -> tuple[int, int]:
        """
        Extract token usage statistics from AI response message.

        Attempts to extract real usage data from LangChain AIMessage,
        falls back to tiktoken estimation if metadata unavailable.

        Parameters
        ----------
        ai_message : Any
            LangChain AIMessage object with potential usage metadata

        Returns
        -------
        tuple[int, int]
            Input tokens and output tokens used (or estimated)
        """
        if ai_message is None:
            logging.warning("Warning: No AI response captured - LangChain issue")
            return 0, 0

        if hasattr(ai_message, "usage_metadata") and ai_message.usage_metadata:
            usage = ai_message.usage_metadata
            tokens_in = usage.get("input_tokens", 0)
            tokens_out = usage.get("output_tokens", 0)
            if tokens_in > 0 or tokens_out > 0:
                return tokens_in, tokens_out

        available_attrs = [attr for attr in dir(ai_message) if not attr.startswith("_")]
        logging.warning("Warning: No token usage metadata found in AI response")
        logging.warning(f"Available attributes: {available_attrs[:10]}...")

        try:
            content = getattr(ai_message, "content", "") or str(ai_message)
            if content:
                encoding = tiktoken.encoding_for_model("gpt-4o-mini")
                estimated_output = len(encoding.encode(content))
                return 0, estimated_output
        except Exception as e:
            logging.error(f"Tiktoken fallback failed: {e}")

        return 0, 0

    def _generate_final_response(
        self, user_question: str, tool_results: list[dict], llm: ChatOpenAI
    ) -> str:
        """
        Generate final response using tool results as context.
        """
        context_parts = []
        for tool_result in tool_results:
            tool_name = tool_result["tool"]
            result = tool_result["result"]
            result_str = str(result)

            if "Error" not in str(result):
                context_parts.append(f"{tool_name}: {result_str}")
            else:
                context_parts.append(f"Note: {result_str}")

        context = "\n\n".join(context_parts)

        system_prompt = self.prompts.final_response_system()
        user_prompt = self.prompts.final_response_user(user_question, context)

        final_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", user_prompt),
            ]
        )
        final_chain = final_prompt | llm | StrOutputParser()

        try:
            final_response = final_chain.invoke({})
            return final_response
        except Exception as e:
            logging.error(f"Error generating final response: {e}")
            return (
                f"Based on the available information:\n\n{context}\n\n"
                f"(Note: Unable to generate synthesized response: {e})"
            )

    def get_session_history_messages(self, session_id: str) -> list:
        """Get all messages from a session history."""
        history = get_session_history(session_id)
        return [msg for msg in history.messages]

    def clear_session_history(self, session_id: str) -> None:
        """Clear all messages from a session history."""
        history = get_session_history(session_id)
        history.clear()

    def add_user_message_to_session(self, session_id: str, message: str) -> None:
        """Add a user message to session history."""
        history = get_session_history(session_id)
        history.add_user_message(message)

    def add_ai_message_to_session(self, session_id: str, message: str) -> None:
        """Add an AI message to session history."""
        history = get_session_history(session_id)
        history.add_ai_message(message)
