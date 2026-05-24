import os
import sys
from typing import TypedDict
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# =====================================================================
# 1. State Definition
# =====================================================================

class MemoryState(TypedDict):
    thread_id: str
    messages: list[dict]
    retrieved_memories: list[str]

# =====================================================================
# 2. Database Engines (Simulated SQLite & Vector DB)
# =====================================================================

# Simulated SQLite database for episodic conversation history
EPISODIC_DATABASE = {}

# Simulated Vector database for semantic long-term memory facts
SEMANTIC_DATABASE = {
    # Default facts matching semantic keywords
    "user_preference_language": "The user prefers programming in Python.",
    "user_location": "The user resides in San Francisco, CA.",
    "user_framework": "The user builds applications with FastAPI and LangGraph."
}

def query_semantic_memory(query: str) -> list[str]:
    """Simulates semantic vector search by keyword matching against facts."""
    print(f"🔎 [Vector DB] Querying long-term semantic memories for: '{query}'...")
    results = []
    q = query.lower()
    
    # Simple semantic similarity mapping based on keywords
    if "code" in q or "program" in q or "python" in q or "language" in q:
        results.append(SEMANTIC_DATABASE["user_preference_language"])
    if "location" in q or "live" in q or "city" in q or "weather" in q:
        results.append(SEMANTIC_DATABASE["user_location"])
    if "framework" in q or "graph" in q or "fastapi" in q:
        results.append(SEMANTIC_DATABASE["user_framework"])
        
    return results

def save_new_fact(key: str, fact: str):
    """Saves a new fact extracted by the write-behind background job."""
    print(f"💾 [Vector DB] Saving new semantic fact: {key} -> '{fact}'")
    SEMANTIC_DATABASE[key] = fact

# =====================================================================
# 3. Agent Memory Nodes
# =====================================================================

def retrieve_memory_node(state: MemoryState) -> dict:
    """Pre-run node: queries Vector DB to load context relevant to user query."""
    print("🧠 [Node: retrieve_memory_node] Querying long-term context...")
    
    # Retrieve the latest human query
    last_user_message = state["messages"][-1]["content"]
    
    # Query vector DB
    memories = query_semantic_memory(last_user_message)
    
    print(f"   [Context Found] Loaded {len(memories)} relevant long-term facts.")
    return {"retrieved_memories": memories}

def write_behind_job(state: MemoryState):
    """Background task simulating fact extraction at session end."""
    print("\n⏳ [Background Task] Running write-behind memory pipeline...")
    
    # Iterate through messages to extract key preferences
    text = " ".join([msg["content"] for msg in state["messages"]])
    
    # Simple simulated LLM fact extraction logic
    if "macbook" in text.lower():
        save_new_fact("user_device", "The user works on a MacBook Pro.")
    if "mcp" in text.lower() or "context" in text.lower():
        save_new_fact("user_protocol", "The user is teaching or learning Model Context Protocol.")

# =====================================================================
# 4. Agent Execution Loop
# =====================================================================

def run_memory_agent(thread_id: str, query: str):
    print("=" * 70)
    print(f"🚀 Running Memory Agent Thread: {thread_id} | Query: '{query}'")
    print("=" * 70)
    
    # Initialize State
    state: MemoryState = {
        "thread_id": thread_id,
        "messages": [{"role": "user", "content": query}],
        "retrieved_memories": []
    }
    
    # 1. Run Memory Retrieval Node
    retrieved = retrieve_memory_node(state)
    state.update(retrieved)
    
    # Construct System prompt with retrieved semantic memories
    memories_str = "\n".join([f"- {m}" for m in state["retrieved_memories"]])
    system_prompt = f"""You are a helpful assistant.
You have access to the following long-term facts about the user:
{memories_str if memories_str else "- No long-term facts found."}
"""
    
    print(f"\n⚙️ [System Prompt Configured]\n{system_prompt}")
    
    # 2. Call LLM (Reasoning Step)
    api_key = os.environ.get("GEMINI_API_KEY")
    response_text = ""
    
    if api_key:
        try:
            from google import genai
            client = genai.Client()
            prompt = f"{system_prompt}\nUser: {query}\nAssistant:"
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            response_text = response.text
        except Exception as e:
            response_text = f"Error calling model: {str(e)}"
    else:
        # Mock LLM response demonstrating that retrieved memories are utilized
        print("ℹ️ Running in Mock Mode...")
        if state["retrieved_memories"]:
            response_text = f"Hello! Since you are in San Francisco and prefer Python, I recommend using FastAPI for your project."
        else:
            response_text = "Hello! Tell me about where you live or what programming languages you like."
            
    print(f"🤖 [Assistant Response]\n{response_text}")
    
    # Append assistant message to history
    state["messages"].append({"role": "assistant", "content": response_text})
    
    # 3. Trigger write-behind background job to extract facts
    write_behind_job(state)
    
    print("\n🎉 Memory Pipeline Complete!")
    print(f"Current Semantic Database Keys: {list(SEMANTIC_DATABASE.keys())}\n")
    print("=" * 70)

if __name__ == "__main__":
    # First query - retrieves existing weather location memories
    run_memory_agent("thread-112", "What is the best city to live in for Python developer coding tools?")
    
    # Second query - introduces a new fact ('macbook') which is extracted at the end
    run_memory_agent("thread-113", "I just bought a new Apple Silicon MacBook Pro.")
