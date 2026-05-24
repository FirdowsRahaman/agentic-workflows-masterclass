import os
import sys
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# =====================================================================
# 1. Ground Truth Dataset Definition
# =====================================================================

TEST_DATASET = [
    {
        "id": "TC-01",
        "input": "Calculate tax for a $50 purchase in California",
        "expected_tool": "calculate_tax",
        "ground_truth_keyword": "$54.13"  # 50 + 50 * 8.25% CA tax
    },
    {
        "id": "TC-02",
        "input": "What is the weather in London right now?",
        "expected_tool": "get_weather",
        "ground_truth_keyword": "london"
    },
    {
        "id": "TC-03",
        "input": "Send a newsletter template to user 102",
        "expected_tool": "send_email",
        "ground_truth_keyword": "newsletter"
    }
]

# =====================================================================
# 2. Agent Runner Simulator
# =====================================================================

def run_agent_on_query(query: str) -> dict:
    """Simulates agent run returning tool call list and final answer text."""
    q = query.lower()
    
    # Simulated execution outcomes based on keywords
    if "tax" in q:
        return {
            "selected_tool": "calculate_tax",
            "final_answer": "The tax has been calculated. The total including California sales tax is $54.13.",
            "latency_seconds": 1.2
        }
    elif "weather" in q:
        return {
            "selected_tool": "get_weather",
            "final_answer": "The current weather in London is 52 degrees with light drizzle.",
            "latency_seconds": 0.8
        }
    else:
        # Fails to call target tool
        return {
            "selected_tool": "none",
            "final_answer": "I don't know how to send emails, sorry.",
            "latency_seconds": 0.4
        }

# =====================================================================
# 3. LLM-as-a-Judge Evaluation Logic
# =====================================================================

def run_llm_judge(query: str, output: str, ground_truth: str) -> float:
    """Grades the semantic correctness of the answer from 0.0 to 1.0."""
    # Check if API Key is available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Local mock grading logic if offline
        o = output.lower()
        gt = ground_truth.lower()
        if gt in o:
            return 1.0
        return 0.0

    try:
        from google import genai
        client = genai.Client()
        
        prompt = f"""You are a professional LLM Evaluation Judge.
Evaluate the semantic correctness of the assistant's output compared to the ground truth key value.

User Query: "{query}"
Assistant Output: "{output}"
Ground Truth Expected: "{ground_truth}"

Respond with a single float score between 0.0 (completely incorrect) and 1.0 (perfectly matches ground truth facts).
Score:"""
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        score_text = response.text.strip()
        # Parse score
        import re
        match = re.search(r"([0-9.]+)", score_text)
        if match:
            return float(match.group(1))
        return 0.0
    except Exception:
        # Fallback to local string validation
        return 1.0 if ground_truth.lower() in output.lower() else 0.0

# =====================================================================
# 4. Evaluation Suite Pipeline Runner
# =====================================================================

def run_evaluation_suite():
    print("=" * 70)
    print("🚀 Initializing Automated Agent Evaluation Suite...")
    print("=" * 70)
    
    results = []
    passed_tests = 0
    
    for case in TEST_DATASET:
        print(f"\nEvaluating {case['id']}: '{case['input']}'...")
        
        # 1. Run the agent
        agent_out = run_agent_on_query(case["input"])
        
        # 2. Evaluate tool routing accuracy (deterministic assertion)
        tool_matches = agent_out["selected_tool"] == case["expected_tool"]
        tool_score = 1.0 if tool_matches else 0.0
        
        # 3. Evaluate answer accuracy using LLM-as-a-judge
        judge_score = run_llm_judge(
            case["input"], 
            agent_out["final_answer"], 
            case["ground_truth_keyword"]
        )
        
        # Overall pass criteria
        test_passed = tool_matches and (judge_score >= 0.8)
        if test_passed:
            passed_tests += 1
            status = "PASSED ✅"
        else:
            status = "FAILED ❌"
            
        print(f"   [Tool Selection] Expected: {case['expected_tool']} | Selected: {agent_out['selected_tool']} ({'OK' if tool_matches else 'FAIL'})")
        print(f"   [Judge Score]    Semantic Accuracy: {judge_score*100:.1f}%")
        print(f"   [Status]         {status}")
        
        results.append({
            "id": case["id"],
            "passed": test_passed,
            "latency": agent_out["latency_seconds"],
            "accuracy": judge_score
        })
        
    print("\n" + "=" * 70)
    print("📊 Evaluation Summary Report")
    print("=" * 70)
    total_tests = len(TEST_DATASET)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"Total Tests Run: {total_tests}")
    print(f"Tests Passed:   {passed_tests}")
    print(f"Success Rate:   {success_rate:.1f}%")
    
    # Assert pipeline status
    if success_rate >= 66.0:
        print("\n🟢 Pipeline Status: PASSED (Accuracy meets minimum requirements)")
        sys.exit(0)
    else:
        print("\n🔴 Pipeline Status: FAILED (Accuracy below build threshold)")
        sys.exit(1)

if __name__ == "__main__":
    run_evaluation_suite()
