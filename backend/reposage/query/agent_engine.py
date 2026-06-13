import os
import logging
from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from .rag_engine import CodeRAGEngine

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    repo_name: str
    
class CodeAgentEngine:
    """Agentic query engine using LangGraph and tool calling."""
    def __init__(
        self,
        repo_name: str,
        persist_dir: str = "./chroma_db",
        clone_dir: str = "./tmp/reposage",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5-coder:7b", # Best for tools
        ollama_embed_model: str = "nomic-embed-text",
    ):
        self.repo_name = repo_name
        self.persist_dir = persist_dir
        self.clone_dir = clone_dir
        
        self.rag_engine = CodeRAGEngine(
            repo_name=repo_name,
            persist_dir=persist_dir,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
            ollama_embed_model=ollama_embed_model,
        )
        
        self.llm = ChatOllama(
            base_url=ollama_base_url,
            model=ollama_model,
            temperature=0,
        )
        
        # Define Tools
        @tool
        def semantic_search(query: str) -> str:
            """Search the codebase for code snippets relevant to the query. Returns matching files and code."""
            result = self.rag_engine.query(query, k=5)
            return result["answer"] + "\n\nSources: " + ", ".join(result["sources"])

        @tool
        def read_file(file_path: str) -> str:
            """Read the full content of a specific file from the repository."""
            full_path = os.path.join(self.clone_dir, self.repo_name, file_path)
            if not os.path.exists(full_path):
                return f"Error: Could not read file {file_path}. It might not exist."
            
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"

        self.tools = [semantic_search, read_file]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build LangGraph
        workflow = StateGraph(AgentState)
        
        def call_model(state: AgentState):
            messages = state["messages"]
            response = self.llm_with_tools.invoke(messages)
            return {"messages": [response]}
            
        def call_tools(state: AgentState):
            messages = state["messages"]
            last_message = messages[-1]
            
            tool_messages = []
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                logger.info(f"Agent using tool: {tool_name} with {tool_args}")
                if tool_name == "semantic_search":
                    result = semantic_search.invoke(tool_args)
                elif tool_name == "read_file":
                    result = read_file.invoke(tool_args)
                else:
                    result = f"Unknown tool {tool_name}"
                    
                tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
                
            return {"messages": tool_messages}
            
        def should_continue(state: AgentState) -> str:
            messages = state["messages"]
            last_message = messages[-1]
            if not getattr(last_message, "tool_calls", None):
                return "end"
            return "continue"
            
        workflow.add_node("agent", call_model)
        workflow.add_node("action", call_tools)
        
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges("agent", should_continue, {"continue": "action", "end": END})
        workflow.add_edge("action", "agent")
        
        self.app = workflow.compile()
        
    def query(self, question: str, k: int = 6, chat_history: Optional[list[dict]] = None) -> dict:
        system_msg = SystemMessage(content=f"You are an autonomous code agent. You have access to tools to search and read the {self.repo_name} codebase. Always use `semantic_search` first. If you need more context, use `read_file`.")
        messages = [system_msg]
        
        if chat_history:
            for msg in chat_history[-6:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))
                    
        messages.append(HumanMessage(content=question))
        
        result = self.app.invoke({"messages": messages, "repo_name": self.repo_name})
        final_message = result["messages"][-1].content
        
        return {
            "answer": final_message,
            "sources": ["Agent Tool Execution"],
            "chunks_used": 0
        }
