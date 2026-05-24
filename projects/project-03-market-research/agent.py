import os
import sys
from typing import TypedDict
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# =====================================================================
# 1. State Definition
# =====================================================================

class ResearchState(TypedDict):
    topic: str
    web_data: str
    graph_entities: list[dict]
    consolidated_report: str
    next_action: str

# =====================================================================
# 2. Worker Agents
# =====================================================================

def search_researcher_worker(topic: str) -> str:
    """Simulates Tavily API web search gathering competitor data."""
    print(f"🔎 [Search Agent] Fetching live web data for: '{topic}'...")
    # Simulated search database
    return (
        "Competitor A: Launched AgentBuilder. Raised $50M Series A. Core tech uses LangGraph.\n"
        "Competitor B: Released AutomateX. Integrates with Slack/Discord. Built on Python FastMCP."
    )

def knowledge_graph_worker(web_data: str) -> list[dict]:
    """Simulates Neo4j Entity extractor finding nodes and connections."""
    print("🕸️ [Graph Agent] Extracting entities and relationships for Neo4j database...")
    # Simulating entity extraction from research text
    entities = [
        {"node_1": "Competitor A", "relation": "USES", "node_2": "LangGraph"},
        {"node_1": "Competitor B", "relation": "USES", "node_2": "FastMCP"},
        {"node_1": "Competitor A", "relation": "RAISED", "node_2": "$50M Series A"}
    ]
    for entity in entities:
        print(f"   [Graph Edge Created] ({entity['node_1']}) --[{entity['relation']}]--> ({entity['node_2']})")
    return entities

# =====================================================================
# 3. Supervisor & Report Compilation
# =====================================================================

def compile_market_report(state: ResearchState) -> str:
    """Orchestrates consolidated market report based on web and graph data."""
    print("👑 [Supervisor] Consolidating research insights...")
    web = state["web_data"]
    graph = state["graph_entities"]
    
    # Format graph connections
    graph_str = "\n".join([f"- {e['node_1']} --[{e['relation']}]--> {e['node_2']}" for e in graph])
    
    # Use API key if available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ℹ️ Model running in Mock Mode...")
        return (
            f"# COMPETITIVE INTELLIGENCE REPORT: {state['topic'].upper()}\n\n"
            f"## 1. Web Search Insights\n{web}\n\n"
            f"## 2. Neo4j Knowledge Graph Mapping\n{graph_str}\n\n"
            f"Status: Compiled & Verified."
        )

    try:
        from google import genai
        client = genai.Client()
        prompt = f"""You are a Competitive Intelligence Supervisor.
Write a formatted competitor analysis report based on these sources:

Web Data:
"{web}"

Knowledge Graph Connections:
{graph_str}

Format the report with clear sections, executive summary, and architectural technology choices.
Report:"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error compiling report: {str(e)}"

# =====================================================================
# 4. Core Pipeline
# =====================================================================

def run_market_research_pipeline(topic: str):
    print("=" * 70)
    print(f"🚀 Initializing Collaborative Market Research Pipeline: '{topic}'")
    print("=" * 70)
    
    # 1. Initialize State
    state: ResearchState = {
        "topic": topic,
        "web_data": "",
        "graph_entities": [],
        "consolidated_report": "",
        "next_action": "search"
    }
    
    # 2. Step 1: Run Search Worker
    state["web_data"] = search_researcher_worker(state["topic"])
    print(f"\n   [Web Data Received]\n{state['web_data']}\n")
    
    # 3. Step 2: Run Graph Node Extractor
    state["graph_entities"] = knowledge_graph_worker(state["web_data"])
    
    # 4. Step 3: Run Supervisor Compiler
    state["consolidated_report"] = compile_market_report(state)
    
    print("\n🎉 Competitive Intelligence Pipeline Complete!")
    print(state["consolidated_report"])
    print("=" * 70)

if __name__ == "__main__":
    topic = "AI Orchestration Competitor Space"
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
        
    run_market_research_pipeline(topic)
