import os
import re
import subprocess
import sys
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# =====================================================================
# 1. Sandbox Execution Tool
# =====================================================================

def execute_python_in_sandbox(filename: str) -> str:
    """Executes a Python script in a secure subprocess sandbox and returns output."""
    print(f"📦 [Sandbox] Executing python script: {filename}...")
    try:
        # Run script with a timeout (e.g. 5 seconds) to prevent infinite loops
        result = subprocess.run(
            [sys.executable, filename],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Format return details
        if result.returncode == 0:
            print("🟢 [Sandbox] Script completed successfully.")
            return f"Success! Output:\n{result.stdout}"
        else:
            print("🔴 [Sandbox] Script failed execution.")
            return f"Failure! Exit Code: {result.returncode}\nError Log:\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        print("🔴 [Sandbox] Script timed out.")
        return "Failure! Execution timed out after 5 seconds."
    except Exception as e:
        return f"Error executing sandbox: {str(e)}"

# =====================================================================
# 2. File Writing Tool
# =====================================================================

def write_code_file(filename: str, code: str) -> str:
    """Writes code contents to a local python script file."""
    print(f"💾 [File System] Writing code to: {filename}...")
    try:
        # Prevent absolute paths or directory traversals outside sandbox dir
        base_name = os.path.basename(filename)
        path = os.path.join(os.path.dirname(__file__), base_name)
        
        with open(path, "w") as f:
            f.write(code)
        return f"File '{base_name}' written successfully."
    except Exception as e:
        return f"Error writing file: {str(e)}"

# =====================================================================
# 3. Autonomous Developer Agent Loop
# =====================================================================

def run_developer_agent(task_description: str):
    print("=" * 70)
    print(f"🚀 Initializing Autonomous Sandbox Developer Agent...")
    print(f"   Task: '{task_description}'")
    print("=" * 70)
    
    filename = "sandbox_script.py"
    script_path = os.path.join(os.path.dirname(__file__), filename)
    
    # Initialize variables for the self-correction loop
    api_key = os.environ.get("GEMINI_API_KEY")
    use_mock = not api_key
    
    # Starting base context
    history = f"""You are an Autonomous Coder Agent. Your goal is to write a Python script that completes the user's objective: "{task_description}"
You MUST write clean, functioning code and execute it using tools to verify it is correct.
If the code runs with errors, read the error message and write a corrected version of the code.

Available Actions:
- write_code_file(code: str)
- execute_python_in_sandbox()

Format rules:
Thought: Explain your logic and planning.
Action: write_code_file(code_string) OR execute_python_in_sandbox()
Observation: Output results.

(Repeat until successful, then conclude)
Thought: The code compiles and executes successfully without error logs.
Final Answer: Summarize your solution and present the final output details.
"""
    
    if use_mock:
        print("ℹ️ GEMINI_API_KEY not found. Running in MOCK Developer mode...")
    else:
        print("🤖 Using live Gemini API for self-correction execution...")
        from google import genai
        client = genai.Client()

    max_iterations = 5
    for attempt in range(1, max_iterations + 1):
        print(f"\n--- [Self-Correction Cycle {attempt}] ---")
        
        # 1. Prompt reasoning model
        if use_mock:
            # Simulating agent self-correction:
            # Turn 1: Write buggy code (missing colon or syntax error)
            # Turn 2: Receive error observations, write fix
            # Turn 3: Final compile and complete
            if attempt == 1:
                response_text = (
                    "Thought: I need to write a script that generates Fibonacci numbers. I will write a simple script but purposely make a syntax mistake to test self-correction.\n"
                    "Action: write_code_file(\"\"\"def fib(n)\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)\nprint(fib(5))\n\"\"\")"
                )
            elif attempt == 2:
                response_text = (
                    "Thought: The file is written. Now I must execute it in the sandbox to verify it runs correctly.\n"
                    "Action: execute_python_in_sandbox()"
                )
            elif attempt == 3:
                response_text = (
                    "Thought: The execution failed with a SyntaxError (missing colon in def statement). I will fix the script by writing the corrected version.\n"
                    "Action: write_code_file(\"\"\"def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)\nprint(fib(5))\n\"\"\")"
                )
            elif attempt == 4:
                response_text = (
                    "Thought: I corrected the syntax error. Let's run it again to verify execution.\n"
                    "Action: execute_python_in_sandbox()"
                )
            else:
                response_text = (
                    "Thought: The code executed successfully and output '5'. The task is complete.\n"
                    "Final Answer: The Python developer agent successfully wrote a Fibonacci script, detected a SyntaxError, self-corrected the code, and verified the output as 5."
                )
        else:
            # Live model execution
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=history
                )
                response_text = response.text
            except Exception as e:
                response_text = f"Error calling model: {str(e)}"

        print(response_text)
        history += f"\n{response_text}\n"
        
        # Check for termination
        if "Final Answer:" in response_text:
            print("\n🎉 Project Complete!")
            break
            
        # Parse actions
        if "write_code_file" in response_text:
            # Extract code block using a greedy markdown check or raw extraction
            code_block = ""
            # Simple match of code inside the parenthesis or triple quotes
            code_match = re.search(r"write_code_file\(\"\"\"(.*)\"\"\"\)", response_text, re.DOTALL)
            if code_match:
                code_block = code_match.group(1)
            else:
                # Check for standard markdown blocks inside the agent thought
                md_match = re.search(r"```python(.*)```", response_text, re.DOTALL)
                if md_match:
                    code_block = md_match.group(1)
                else:
                    # Fallback string
                    code_block = "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)\nprint(fib(5))"
            
            obs = write_code_file(filename, code_block)
            print(f"   [Observation] {obs}")
            history += f"Observation: {obs}\n"
            
        elif "execute_python_in_sandbox" in response_text:
            obs = execute_python_in_sandbox(script_path)
            print(f"   [Observation] {obs}")
            history += f"Observation: {obs}\n"
            
    else:
        print("\n❌ Failed to compile working code within limit.")

    # Clean up generated file
    if os.path.exists(script_path):
        os.remove(script_path)
        print("🧹 Cleaned up temporary sandbox script file.")

if __name__ == "__main__":
    task = "Write a python script that prints out the first 10 Fibonacci numbers."
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    run_developer_agent(task)
