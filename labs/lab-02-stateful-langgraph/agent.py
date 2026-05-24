import os
import sys
from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load API keys
load_dotenv()

# =====================================================================
# 1. State Definition
# =====================================================================

# Define what state our graph will maintain across executions
class AgentState(TypedDict):
    # Running list of messages in the conversation thread
    messages: list[dict]
    # Current task details
    query: str
    # The calculated total cost or safety status
    is_authorized: bool

# =====================================================================
# 2. Tool Definition
# =====================================================================

def check_account_balance(user_id: str) -> str:
    """Checks the current account balance for a given user ID."""
    print(f"   [Tool Executing] check_account_balance for user {user_id}...")
    uid = user_id.strip()
    balances = {"102": 5420.50, "304": 120.00}
    balance = balances.get(uid, 0.0)
    return f"User ID {uid} has a current account balance of ${balance:.2f}."

# =====================================================================
# 3. Graph Nodes
# =====================================================================

def call_model_node(state: AgentState) -> dict:
    """The reasoning node: calls the LLM to decide the next step."""
    print("🤖 [Node: call_model_node] Reasoning...")
    messages = state["messages"]
    query = state["query"]
    
    # Check if API Key is available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Mock Response sequence for demo mode
        print("ℹ️ Running in Mock Mode...")
        if len(messages) == 0:
            ai_message = {
                "role": "assistant",
                "content": "Thought: I need to check the balance of user ID 102. I will call the check_account_balance tool.",
                "tool_calls": [{"name": "check_account_balance", "args": {"user_id": "102"}}]
            }
        else:
            ai_message = {
                "role": "assistant",
                "content": "Thought: I have retrieved the user's balance ($5,420.50). I can now provide the final answer.",
                "final_answer": "User 102 has a balance of $5,420.50."
            }
        return {"messages": [ai_message]}
    
    # Real Live LLM logic using google-genai
    try:
        from google import genai
        from google.genai import types
        client = genai.Client()
        
        # Format history for Gemini API
        contents = []
        for msg in messages:
            contents.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )
        # Add current query
        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=query)])
        )
        
        # Call Gemini model
        # Using a structured output or system instruction
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction="You are an account audit assistant. Determine if you need to check account balance using the tool check_account_balance(user_id: str)."
            )
        )
        
        # For simplicity in this lab code, we parse simulated tool-calls from text:
        content_text = response.text
        tool_calls = []
        if "check_account_balance" in content_text:
            tool_calls.append({"name": "check_account_balance", "args": {"user_id": "102"}})
            
        ai_message = {
            "role": "assistant",
            "content": content_text,
            "tool_calls": tool_calls
        }
        return {"messages": [ai_message]}
    except Exception as e:
        # Fallback error message
        return {"messages": [{"role": "assistant", "content": f"Error calling live LLM: {str(e)}", "tool_calls": []}]}

def execute_tools_node(state: AgentState) -> dict:
    """The action node: executes any pending tool calls."""
    print("🛠️ [Node: execute_tools_node] Executing tools...")
    last_message = state["messages"][-1]
    tool_calls = last_message.get("tool_calls", [])
    
    new_messages = []
    for call in tool_calls:
        name = call["name"]
        args = call["args"]
        
        if name == "check_account_balance":
            result = check_account_balance(args["user_id"])
            tool_msg = {
                "role": "tool",
                "content": result,
                "name": name
            }
            new_messages.append(tool_msg)
            
    # Return updates to append to the state message list
    return {"messages": new_messages}

# =====================================================================
# 4. Conditional Edges
# =====================================================================

def should_continue_edge(state: AgentState) -> str:
    """Decides whether to route to the tool node or terminate the graph."""
    last_message = state["messages"][-1]
    tool_calls = last_message.get("tool_calls", [])
    
    if len(tool_calls) > 0:
        print("🔗 [Edge] Tool calls pending ──> routing to 'execute_tools'")
        return "execute_tools"
    else:
        print("🔗 [Edge] No tool calls ──> routing to '__end__'")
        return "__end__"

# =====================================================================
# 5. Graph Construction
# =====================================================================

def run_stateful_agent(query: str):
    print("=" * 70)
    print(f"🚀 Running LangGraph workflow with query: '{query}'")
    print("=" * 70)
    
    # We construct a state graph manually to show how the state machine compiles
    # state_graph = StateGraph(AgentState)
    # state_graph.add_node("call_model", call_model_node)
    # state_graph.add_node("execute_tools", execute_tools_node)
    # state_graph.set_entry_point("call_model")
    # state_graph.add_conditional_edges("call_model", should_continue_edge)
    # state_graph.add_edge("execute_tools", "call_model")
    # compiled_graph = state_graph.compile()
    
    # For Lab 2 instruction without requiring compilation dependencies during setup,
    # we simulate the compiled graph's runtime loop using the exact state variables
    # and reducers to illustrate the architecture under the hood:
    
    state: AgentState = {
        "messages": [],
        "query": query,
        "is_authorized": True
    }
    
    # Simulate LangGraph Execution Loop
    current_node = "call_model"
    max_steps = 10
    
    for step in range(1, max_steps + 1):
        print(f"\n--- [Graph Step {step}] ---")
        
        if current_node == "call_model":
            # Run Model Node
            updates = call_model_node(state)
            # Apply Reducer (append messages)
            state["messages"].extend(updates["messages"])
            
            # Print state message logs
            last_msg = state["messages"][-1]
            print(f"   [Assistant Message] {last_msg['content']}")
            
            # Evaluate conditional edge
            next_step = should_continue_edge(state)
            if next_step == "__end__":
                break
            else:
                current_node = next_step
                
        elif current_node == "execute_tools":
            # Run Tools Node
            updates = execute_tools_node(state)
            # Apply Reducer (append messages)
            state["messages"].extend(updates["messages"])
            
            # Print observations
            for msg in updates["messages"]:
                print(f"   [Tool Response] {msg['content']}")
                
            # Route back to model
            current_node = "call_model"

    print("\n🎉 Graph Execution Finished!")
    final_message = state["messages"][-1]
    print(f"👉 Result: {final_message['content']}\n")

if __name__ == "__main__":
    test_query = "Please check the account balance for user 102."
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
    run_stateful_agent(test_query)
