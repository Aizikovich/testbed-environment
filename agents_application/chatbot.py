import os
from termcolor import cprint
from main import run

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the chatbot header"""
    header = """
    ┌───────────────────────────────────────────────┐
    │           O-RAN NETWORK MONITORING            │
    │                  CHATBOT                      │
    └───────────────────────────────────────────────┘
    """
    cprint(header, 'cyan', attrs=['bold'])
    print("Type 'exit' to quit, 'help' for example queries")
    print("Default query: \"Which users have poor signal quality in step 3?\"")
    print("Please enter your O-RAN network query:")


def print_help():
    """Print help with example queries"""
    cprint("\nExample queries you can ask:", 'cyan')
    examples = [
        "What is the most loaded cell in step 3?",
        "Which users are connected to cell 2 in step 3?",
        "Find users with poor signal quality in step 3",
        "Are there any users with anomalies in step 3?",
        "Which cell has the best coverage in step 3?",
        "Are there any users at risk of handover in step 3?"
    ]
    for example in examples:
        cprint(f"  • {example}", 'yellow')
    print()

def run_chatbot():
    """Run the interactive O-RAN monitoring chatbot"""
    clear_screen()
    print_header()
    
    while True:
        # Get user query
        cprint("\n[You] ", 'yellow', end='')
        query = input()
        
        # Check for exit command
        if query.lower() in ['exit', 'quit', 'q']:
            cprint("\nThank you for using the O-RAN Network Monitoring Chatbot!", 'cyan')
            break
            
        # Check for help command
        if query.lower() in ['help', '?']:
            print_help()
            continue
            
        # Process the query
        cprint("\nAnalyzing your query...", 'cyan')
        try:
            result = run(query)
            
            # Print the answer
            cprint("\n[O-RAN Bot] ", 'green', attrs=['bold'], end='')
            print()
            cprint(result, 'green')
            
        except Exception as e:
            cprint(f"\nError processing your query: {str(e)}", 'red')
            cprint("Please try again with a different query.", 'red')

if __name__ == "__main__":
    run_chatbot()