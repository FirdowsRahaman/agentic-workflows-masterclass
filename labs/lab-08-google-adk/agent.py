import os
import sys
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# =====================================================================
# 1. Tool Definition (Framework-Agnostic)
# =====================================================================

def competitor_web_search(query: str) -> str:
    """Searches the mock web database for competitor news and funding data.
    
    Args:
        query: The search query string.
        
    Returns:
        A text summary of matching competitor facts.
    """
    print(f"\n🔎 [Tool: competitor_web_search] Searching index for: '{query}'...")
    
    # Mock data lookup
    q = query.lower()
    if "orchestration" in q or "competitor" in q or "agent" in q:
        return (
            "Competitor A: Launched AgentBuilder. Raised $50M Series A. Core tech uses LangGraph for stateful graphs.\n"
            "Competitor B: Released AutomateX. Integrates with Slack/Discord. Built on Python FastMCP protocol."
        )
    return "No recent competitor updates found for the given search query."

# =====================================================================
# 2. Google ADK Live Definition
# =====================================================================

adk_imported = False
try:
    # Try importing the Google ADK packages
    from google import adk
    from google.adk import Agent, Workflow, Runner
    adk_imported = True
except ImportError:
    pass

# Helper to define the real ADK graph when library is present
def run_live_adk(topic: str):
    """Executes the collaborative team workflow using the real Google ADK SDK."""
    print("🔋 [ADK Live] Initializing Google Agent Development Kit runtime...")
    
    try:
        # Define the specialized research agent
        researcher = Agent(
            name="researcher_agent",
            instruction=(
                "You are an expert research analyst. Use the competitor_web_search tool "
                "to find facts, tech stacks, and funding data about competitors. "
                "Output your findings as structured notes."
            ),
            tools=[competitor_web_search]
        )
        
        # Define the writer agent (receives notes and compiles them)
        writer = Agent(
            name="writer_agent",
            instruction=(
                "You are a professional executive writer. Take the raw competitor research "
                "notes and compile them into a clean, executive Markdown report. "
                "Include a section for Executive Summary, Technical Architecture, and Market Strategy."
            )
        )
        
        # Define a sequential workflow (Researcher runs first, passes context to Writer)
        writing_workflow = Workflow(
            name="sequential_writing_team",
            edges=[("START", researcher, writer)]
        )
        
        # Execute the workflow using the Runner
        runner = Runner()
        print("🚀 [ADK Live] Running sequential_writing_team workflow...")
        result = runner.run(
            workflow=writing_workflow,
            input=f"Research topic: {topic}"
        )
        
        print("\n🎉 [ADK Live Workflow Complete]")
        print("-" * 70)
        print(result)
        print("-" * 70)
        
    except Exception as e:
        print(f"❌ Error during live ADK execution: {e}")
        print("Falling back to simulated run...")
        run_simulated_adk(topic)

# =====================================================================
# 3. Simulated ADK Runner (For local runs without API Keys or SDK)
# =====================================================================

def run_simulated_adk(topic: str):
    """Prints a structured trace showing how ADK handles task execution and delegation."""
    print("ℹ️ Model API Key or google-adk package missing. Running in Simulated Mode...")
    print("🔌 [ADK Initialization] Loading agents and tools...")
    print("   - Registered Tool: 'competitor_web_search'")
    print("   - Registered Agent: 'researcher_agent' (model: gemini-2.5-flash)")
    print("   - Registered Agent: 'writer_agent' (model: gemini-2.5-flash)")
    print("   - Registered Workflow: 'sequential_writing_team'")
    print("=" * 80)
    print(f"🚀 [ADK Workflow Start] Executing workflow: 'sequential_writing_team'")
    print(f"   Input: 'Research topic: {topic}'")
    print("=" * 80)
    
    # Step 1: Researcher agent starts
    print("\n👉 [ADK Execution] Activating Agent: 'researcher_agent'")
    print("   Instruction: 'You are an expert research analyst...'")
    
    # Tool execution
    search_output = competitor_web_search(topic)
    print(f"   [Tool Output Received]:\n   {search_output.replace(chr(10), chr(10)+'   ')}")
    
    research_notes = (
        "Here are the competitor research notes:\n"
        "- Competitor A has launched 'AgentBuilder' built on LangGraph, and secured $50M Series A.\n"
        "- Competitor B released 'AutomateX' built on FastMCP protocol with Slack/Discord support."
    )
    print(f"\n🤖 [Agent Output] 'researcher_agent' completed turn. Output:\n{research_notes}")
    print("-" * 80)
    
    # Step 2: Handoff
    print("\n👉 [ADK Context Handoff] Transferring context: 'researcher_agent' ──> 'writer_agent'")
    
    # Step 3: Writer agent starts
    print("\n👉 [ADK Execution] Activating Agent: 'writer_agent'")
    print("   Instruction: 'You are a professional executive writer...'")
    
    report = (
        f"# COMPETITOR REPORT: {topic.upper()}\n\n"
        f"## 1. Executive Summary\n"
        f"The AI orchestration competitor space is growing rapidly. We observe a bifurcation "
        f"between stateful cyclic frameworks and standardized communication protocols.\n\n"
        f"## 2. Technical Architecture Breakdown\n"
        f"*   **Competitor A**: Standardizing on **LangGraph** to support complex cyclic state machines and multi-agent teams.\n"
        f"*   **Competitor B**: Built using the **FastMCP** protocol, focusing on modular tool integrations with platforms like Slack.\n\n"
        f"## 3. Market & Funding Insights\n"
        f"*   Competitor A secured a $50M Series A round, signaling high investor interest in stateful enterprise platforms."
    )
    
    print(f"\n🤖 [Agent Output] 'writer_agent' completed turn. Output:\n{report}")
    print("-" * 80)
    print("\n🎉 [ADK Workflow Complete] Status: SUCCESS\n")

# =====================================================================
# 4. Main Entry Point
# =====================================================================

if __name__ == "__main__":
    test_topic = "AI Orchestration Competitor Space"
    if len(sys.argv) > 1:
        test_topic = " ".join(sys.argv[1:])
        
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if adk_imported and api_key:
        run_live_adk(test_topic)
    else:
        run_simulated_adk(test_topic)
