import os
import sys
from typing import TypedDict
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# =====================================================================
# 1. State Definition
# =====================================================================

class TeamState(TypedDict):
    task: str
    research_data: str
    code_solution: str
    final_report: str
    next_step: str

# =====================================================================
# 2. Specialized Workers
# =====================================================================

def run_researcher_agent(task: str) -> str:
    """Simulates a researcher agent searching the web for information."""
    print("🔎 [Worker: Researcher] Scraping search results and compiling data...")
    t = task.lower()
    if "market" in t:
        return "Market Research: AI Agent Market is projected to grow 45% CAGR, reaching $30B by 2030."
    elif "mcp" in t:
        return "Technical Research: Model Context Protocol (MCP) is an open-standard protocol released by Anthropic in late 2024."
    else:
        return f"Research facts compiled for general query: '{task}'."

def run_coder_agent(task: str, context: str) -> str:
    """Simulates a coder agent generating code based on researcher data."""
    print("💻 [Worker: Coder] Writing code solution...")
    return (
        "```python\n"
        "# Automatic Code Solution Generated based on: " + context + "\n"
        "def run_workflow():\n"
        "    print('Workflow initialized successfully')\n"
        "```"
    )

# =====================================================================
# 3. Supervisor Logic (Orchestrator)
# =====================================================================

def run_supervisor(state: TeamState) -> dict:
    """The Supervisor analyzes the state and directs the next worker agent."""
    print("👑 [Supervisor] Analyzing team progress...")
    task = state["task"]
    research = state["research_data"]
    code = state["code_solution"]
    
    # Check for actual API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Mock supervisor decision logic for local offline run
        if not research:
            print("   [Decision] Needs research ──> delegating to Researcher")
            return {"next_step": "researcher"}
        elif not code:
            print("   [Decision] Needs implementation ──> delegating to Coder")
            return {"next_step": "coder"}
        else:
            print("   [Decision] Sub-tasks complete ──> compiling final report")
            return {"next_step": "compile_report"}

    # Real LLM-based supervisor routing using google-genai
    try:
        from google import genai
        client = genai.Client()
        
        prompt = f"""You are the Supervisor of an AI Agent Team.
Your job is to solve this user task: "{task}"
Here is what the team has done so far:
- Research Data gathered: "{research}"
- Code Solution drafted: "{code}"

Choose the NEXT step for the team:
- If we do not have research data yet, output: "NEXT: researcher"
- If we have research data but no code solution yet, output: "NEXT: coder"
- If we have both, output: "NEXT: compile_report"
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        res_text = response.text.lower()
        
        if "researcher" in res_text:
            return {"next_step": "researcher"}
        elif "coder" in res_text:
            return {"next_step": "coder"}
        else:
            return {"next_step": "compile_report"}
            
    except Exception as e:
        print(f"⚠️ Error calling supervisor model ({str(e)}). Using local rule engine.")
        # Fallback to local rule logic
        if not research: return {"next_step": "researcher"}
        elif not code: return {"next_step": "coder"}
        else: return {"next_step": "compile_report"}

# =====================================================================
# 4. Main Multi-Agent Loop
# =====================================================================

def run_multi_agent_team(task_query: str):
    print("=" * 70)
    print(f"🚀 Initializing Supervisor Multi-Agent Team with task:\n   '{task_query}'")
    print("=" * 70)
    
    state: TeamState = {
        "task": task_query,
        "research_data": "",
        "code_solution": "",
        "final_report": "",
        "next_step": "supervisor"
    }
    
    max_turns = 6
    for turn in range(1, max_turns + 1):
        print(f"\n--- [Turn {turn}: Team State Machine] ---")
        
        # 1. Run Supervisor
        decisions = run_supervisor(state)
        state["next_step"] = decisions["next_step"]
        
        # 2. Execute Handoffs
        if state["next_step"] == "researcher":
            result = run_researcher_agent(state["task"])
            state["research_data"] = result
            print(f"   [Researcher Output] {result}")
            
        elif state["next_step"] == "coder":
            result = run_coder_agent(state["task"], state["research_data"])
            state["code_solution"] = result
            print(f"   [Coder Output]\n{result}")
            
        elif state["next_step"] == "compile_report":
            print("👑 [Supervisor] Compiling final project report...")
            state["final_report"] = (
                f"### Final Project Report\n"
                f"User Goal: {state['task']}\n\n"
                f"1. Findings:\n{state['research_data']}\n\n"
                f"2. Implementation Code:\n{state['code_solution']}\n\n"
                f"Status: Complete & Verified."
            )
            break
            
    print("\n🎉 Multi-Agent Collaboration Finished!")
    print(state["final_report"])
    print("=" * 70)

if __name__ == "__main__":
    task = "Build a market analytics tool for the emerging AI Agent space."
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    run_multi_agent_team(task)
