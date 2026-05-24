import os
import re
import sys
from dotenv import load_dotenv

# Load environment variables (API keys)
load_dotenv()

# =====================================================================
# 1. Tool Definitions
# =====================================================================

def get_weather(location: str) -> str:
    """Fetches the current weather for a given city location."""
    print(f"   [Tool Executing] get_weather('{location}')...")
    loc = location.lower().strip()
    if "san francisco" in loc:
        return "65°F, Partly Cloudy, 12mph Wind"
    elif "new york" in loc:
        return "78°F, Sunny, 5mph Wind"
    elif "london" in loc:
        return "52°F, Light Drizzle, 18mph Wind"
    else:
        return f"55°F, Overcast (Default weather data for {location})"

def calculate_tax(price: float, state: str) -> str:
    """Calculates sales tax based on price and a 2-letter US state code."""
    print(f"   [Tool Executing] calculate_tax({price}, '{state}')...")
    st = state.upper().strip()
    rates = {"CA": 0.0825, "NY": 0.08875, "TX": 0.0625}
    rate = rates.get(st, 0.05)  # Default 5%
    tax = price * rate
    total = price + tax
    return f"Subtotal: ${price:.2f}, Tax Rate: {rate*100}%, Calculated Tax: ${tax:.2f}, Total: ${total:.2f}"

# Map of tool names to Python functions
TOOL_REGISTRY = {
    "get_weather": get_weather,
    "calculate_tax": calculate_tax
}

# =====================================================================
# 2. System Instructions & ReAct Prompt Template
# =====================================================================

SYSTEM_PROMPT = """You are a helpful, autonomous AI Assistant. You solve tasks using a step-by-step loop.
You have access to the following tools:

- get_weather(location: str) -> str
  Description: Fetches the current weather for a given city location.
  
- calculate_tax(price: float, state: str) -> str
  Description: Calculates sales tax based on price and a 2-letter US state code.

To solve the task, you MUST use the following ReAct pattern format:

Thought: Write down what you need to do next, reason about your plan, and determine which tool is appropriate.
Action: tool_name(argument_value_1, argument_value_2)
Observation: The output of the tool will appear here. Do NOT write this line yourself; it is provided by the execution environment.

(Repeat the Thought -> Action -> Observation cycle as many times as needed)

Thought: I have retrieved all the information required.
Final Answer: Write the clear, concise final response resolving the user request.

IMPORTANT rules:
1. Only call tools that are listed in the registry.
2. Only output ONE Action call at a time.
3. Wait for the Observation before continuing with the next Thought.
"""

# =====================================================================
# 3. Mock LLM for local demonstration (if API Key is missing)
# =====================================================================

class MockGeminiClient:
    """Simulates Gemini responses to show the ReAct loop without API keys."""
    def __init__(self, query: str):
        self.query = query.lower()
        self.turn = 0

    def generate_content(self, prompt: str) -> str:
        self.turn += 1
        
        if "weather" in self.query and "tax" in self.query:
            # Multi-hop query: weather in SF and tax for $100 in CA
            if self.turn == 1:
                return (
                    "Thought: The user has two requests. First, I need to check the weather in San Francisco. "
                    "I will call get_weather for this.\n"
                    "Action: get_weather(San Francisco)"
                )
            elif self.turn == 2:
                return (
                    "Thought: I have the weather data for San Francisco (65°F). Now I need to calculate the sales tax "
                    "for a $100 purchase in California (CA). I will use the calculate_tax tool.\n"
                    "Action: calculate_tax(100.0, CA)"
                )
            else:
                return (
                    "Thought: I now have all necessary information. The weather in SF is 65°F and the total purchase price "
                    "after CA sales tax is $108.25. I am ready to compile the final answer.\n"
                    "Final Answer: The current weather in San Francisco is 65°F, Partly Cloudy. The total price for a $100.00 "
                    "purchase in California, including sales tax, is $108.25 (Calculated Tax: $8.25 at an 8.25% tax rate)."
                )
        elif "weather" in self.query:
            if self.turn == 1:
                return (
                    "Thought: The user wants to know the weather. I will use the get_weather tool.\n"
                    "Action: get_weather(London)"
                )
            else:
                return (
                    "Thought: I have the weather data for London. I can now provide the final answer.\n"
                    "Final Answer: The current weather in London is 52°F, Light Drizzle with an 18mph Wind."
                )
        else:
            return (
                "Thought: The request does not require any tool calls. I can answer directly.\n"
                "Final Answer: Hello! How can I assist you with weather forecasts or sales tax calculations today?"
            )

# =====================================================================
# 4. The Core ReAct Loop
# =====================================================================

def run_react_agent(query: str):
    print("=" * 70)
    print(f"🚀 User Query: '{query}'")
    print("=" * 70)
    
    # Check for actual API key
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = True
    llm_client = None
    
    if api_key:
        try:
            from google import genai
            llm_client = genai.Client()
            use_mock = False
            print("🤖 Using Live Gemini API for ReAct reasoning...")
        except ImportError:
            print("⚠️ 'google-genai' SDK not installed. Falling back to Mock Agent...")
    else:
        print("ℹ️ GEMINI_API_KEY not found in environment. Running in MOCK Mode...")
        llm_client = MockGeminiClient(query)

    # Initialize conversation history with the system prompt
    history = f"{SYSTEM_PROMPT}\n\nUser: {query}\n"
    
    max_turns = 8
    for turn in range(1, max_turns + 1):
        print(f"\n--- [Turn {turn}] ---")
        
        # 1. Call LLM to get the next step (Thought + Action or Final Answer)
        if use_mock:
            response_text = llm_client.generate_content(history)
        else:
            # Call live Gemini model (using gemini-2.5-flash as default)
            response = llm_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=history
            )
            response_text = response.text
            
        print(response_text)
        
        # Add response to history
        history += f"{response_text}\n"
        
        # 2. Check for Final Answer
        if "Final Answer:" in response_text:
            print("\n🎉 Mission Accomplished!")
            final_answer = response_text.split("Final Answer:")[-1].strip()
            print(f"👉 Result: {final_answer}\n")
            break
            
        # 3. Parse tool action call
        # Format matched: Action: tool_name(arg1, arg2)
        match = re.search(r"Action:\s*(\w+)\((.*?)\)", response_text)
        if match:
            tool_name = match.group(1)
            tool_args_str = match.group(2)
            
            # Simple argument parsing (splits by comma and strips quotes/whitespace)
            tool_args = [arg.strip().replace("'", "").replace('"', '') for arg in tool_args_str.split(',') if arg.strip()]
            
            # Find and execute tool
            if tool_name in TOOL_REGISTRY:
                tool_func = TOOL_REGISTRY[tool_name]
                try:
                    # Convert arguments types if needed (e.g. price to float)
                    if tool_name == "calculate_tax":
                        # Convert first arg to float
                        tool_args[0] = float(tool_args[0])
                    
                    # Execute tool
                    observation = tool_func(*tool_args)
                except Exception as e:
                    observation = f"Error executing tool: {str(e)}"
            else:
                observation = f"Error: Tool '{tool_name}' is not in the tool registry."
                
            print(f"   [Observation] {observation}")
            # Feed observation back into history for next turn
            history += f"Observation: {observation}\n"
        else:
            print("⚠️ Error: LLM response did not contain a valid Action or Final Answer. Terminating loop.")
            break
    else:
        print("\n❌ Terminated: Exceeded maximum plan iterations.")

if __name__ == "__main__":
    # Test queries
    # Multi-hop query: requires calling weather then tax
    test_query = "What is the weather in San Francisco, and what is the total cost of a $100 item there after CA sales tax?"
    
    # If query is passed from command line, use it
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
        
    run_react_agent(test_query)
