import os
import sys
from typing import TypedDict
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# =====================================================================
# 1. State Definition
# =====================================================================

class TransactionState(TypedDict):
    transaction_id: str
    amount: float
    recipient: str
    sql_command: str
    status: str  # pending_approval, executed, aborted
    user_approval: bool

# =====================================================================
# 2. Database Action Node
# =====================================================================

def execute_transaction(state: TransactionState) -> dict:
    """Destructive database write command execution (runs after approval)."""
    print("\n💾 [Database Node] Executing query in production database...")
    print(f"   SQL >> {state['sql_command']}")
    print("   [DB Info] 1 row affected. Transaction committed.")
    return {"status": "executed"}

# =====================================================================
# 3. Agent Planner Node
# =====================================================================

def run_agent_planner(state: TransactionState) -> dict:
    """Agent prepares the SQL write command based on transaction details."""
    print("🤖 [Node: Agent Planner] Preparing database command...")
    recipient = state["recipient"]
    amount = state["amount"]
    
    # Formulate database modification query
    sql = f"UPDATE accounts SET balance = balance - {amount} WHERE username = '{recipient}';"
    
    print(f"   [Planned Action] Write Query generated: {sql}")
    # Return updates containing the planned query and pause status
    return {
        "sql_command": sql,
        "status": "pending_approval"
    }

# =====================================================================
# 4. Human Approval Interface
# =====================================================================

def request_human_approval(state: TransactionState) -> bool:
    """Pauses the execution thread and prompts the developer for approval."""
    print("\n" + "🛑" * 15)
    print("⚠️  BREAKPOINT INTERRUPT: SENSITIVE TRANSACTION DETECTED")
    print(f"   Transaction ID: {state['transaction_id']}")
    print(f"   Recipient:      {state['recipient']}")
    print(f"   Amount:         ${state['amount']:.2f}")
    print(f"   Target Query:   {state['sql_command']}")
    print("" + "🛑" * 15)
    
    # Prompt user in terminal console
    try:
        user_input = input("\n👉 Approve execution? (y/n): ").strip().lower()
        if user_input == 'y' or user_input == 'yes':
            print("🟢 Human Approved. Resuming execution thread...")
            return True
        else:
            print("🔴 Human Rejected. Aborting execution thread...")
            return False
    except EOFError:
        # Fallback if run in non-interactive environment (CI, test runs)
        print("ℹ️ Non-interactive run detected. Auto-approving for demo...")
        return True

# =====================================================================
# 5. Stateful Pipeline
# =====================================================================

def run_human_in_the_loop_demo(recipient: str, amount: float):
    print("=" * 70)
    print("🚀 Initializing Human-in-the-Loop Safeguard Workflow...")
    print("=" * 70)
    
    # 1. Initialize State
    state: TransactionState = {
        "transaction_id": "TXN-902184",
        "amount": amount,
        "recipient": recipient,
        "sql_command": "",
        "status": "initialized",
        "user_approval": False
    }
    
    # 2. Run Planner Node
    updates = run_agent_planner(state)
    state.update(updates)
    
    # 3. Trigger Breakpoint Safeguard
    # Check if transaction needs approval (any transaction > $100 or write query)
    if "pending_approval" in state["status"]:
        # Pause graph execution and request human input
        approved = request_human_approval(state)
        state["user_approval"] = approved
        
        if approved:
            # 4a. Resume and run database executor node
            db_updates = execute_transaction(state)
            state.update(db_updates)
        else:
            # 4b. Terminate with abort status
            state["status"] = "aborted"
            print("\n❌ Transaction Aborted by human administrator.")
            
    print("\n🎉 Safeguard Loop Complete!")
    print(f"👉 Final State: {state['status'].upper()}\n")
    print("=" * 70)

if __name__ == "__main__":
    recipient = "Bob"
    amount = 550.00
    
    if len(sys.argv) > 2:
        recipient = sys.argv[1]
        amount = float(sys.argv[2])
        
    run_human_in_the_loop_demo(recipient, amount)
