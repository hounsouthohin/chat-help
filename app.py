from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, BaseMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from typing import Sequence
from typing_extensions import Annotated, TypedDict

from tools.web_search import DuckDuckGoSearchTool


# --- Initialize the custom tool
web_tool_instance = DuckDuckGoSearchTool(max_results=5)

# --- Functional wrapper for compatibility
def web_search(query: str) -> str:
    """
    Perform a DuckDuckGo search via the custom tool.
    """
    return web_tool_instance.forward(query)


# --- Prompt template
prompt_template = ChatPromptTemplate.from_template("""
You are **Chatbot IA**, an AI conversational assistant.

## Your role
- You are helpful, friendly, and conversational.
- You primarily answer using your internal knowledge and reasoning.
- If the answer is not available in your knowledge, you may use available tools (like WebSearch).

## Tools available
1. **Knowledge Base** (your trained or stored knowledge).
2. **Web Search** (use only if the user explicitly asks for current information, recent events, scores, news, weather, or if you cannot answer confidently).

## Behavior rules
- If the user greets (hello, hi, salut, bonjour, hey, etc.), respond quickly and politely. Do NOT perform a web search.
- If the user asks about factual, general knowledge → answer directly from your knowledge base.
- If the user asks about **recent events or dynamic information** (sports results, weather, news, stock prices, "yesterday", "today", "now") and you don't know → trigger WebSearch.
- Always keep answers clear, concise, and conversational.
- Never make up results if you don’t know; instead, say you will check with WebSearch.
- When using WebSearch, cite information from search results.

## Conversation
Language: {language}
Conversation so far:
{messages}

Your task: 
Provide the best possible reply to the latest user message, using the rules above.
""")


# --- Typing for LangGraph state
class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str


# --- Initialize Ollama and bind tool
model = init_chat_model("llama3.2:latest", model_provider="ollama")
model_with_tools = model.bind_tools([web_search])


# --- Message trimmer
trimmer = trim_messages(
    max_tokens=300,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)


# --- Main model call function
def call_model(state: State):
    trimmed_messages = trimmer.invoke(state["messages"])

    # Build prompt
    final_prompt = prompt_template.invoke(
        {"messages": trimmed_messages, "language": state["language"]}
    )

    # Call the model
    response = model_with_tools.invoke(final_prompt)

    # If the model calls a tool
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_call = response.tool_calls[0]
        if tool_call["name"] == "web_search":
            query = tool_call["args"].get("query", "")
            try:
                tool_result = web_search(query)  # <-- wrapper used here
            except Exception as e:
                tool_result = f"⚠️ Web search failed: {str(e)}"

            # Feed tool result back to the model
            follow_up = model.invoke([
                *trimmed_messages,
                HumanMessage(content=f"Search results for '{query}':\n{tool_result}")
            ])
            return {"messages": [follow_up]}

    return {"messages": [response]}


# --- LangGraph workflow
workflow = StateGraph(state_schema=State)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)
app = workflow.compile(checkpointer=MemorySaver())


# --- Helper: decide when to use WebSearch
def should_use_websearch(user_input: str) -> bool:
    """Check if a web search is needed based on the user input."""
    greetings = ["hi", "hello", "hey", "salut", "bonjour"]
    if any(user_input.lower().startswith(g) for g in greetings):
        return False

    realtime_keywords = ["today", "yesterday", "now", "latest", "score", "news", "weather", "current"]
    if any(word in user_input.lower() for word in realtime_keywords):
        return True

    # Default → no web search
    return False


# --- CLI
def main():
    print("=== Chatbot IA (Ollama + LangGraph + WebSearch Auto) ===")
    language = "english"

    while True:
        question = input("\n👤 You: ")
        if question.lower() in ["quit", "exit"]:
            print("👋 Bye!")
            break

        config = {"configurable": {"thread_id": "1"}}
        input_messages = [("user", question)]

        if should_use_websearch(question):
            # Use the agent with web search
            response = app.invoke(
                {"messages": input_messages, "language": language},
                config=config,
            )
            last_message = response["messages"][-1]
            print(f"\n🤖 Bot: {last_message.content}")
        else:
            # Use direct model only (faster for greetings/general knowledge)
            response = model.invoke([HumanMessage(content=question)])
            print(f"\n🤖 Bot: {response.content}")


if __name__ == "__main__":
    main()
