#!/usr/bin/env python
import warnings
import os
from termcolor import cprint
from oran_system.crew import OranSystem

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run(query=None):
    """
    Run the crew.
    """
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

        inputs = {
            'query': query if query is not None else "Which users have poor signal quality in step 3?"
        } 

        response = OranSystem().crew().kickoff(inputs=inputs)

        cprint("\n[O-RAN Bot] ", 'green', attrs=['bold'], end='')
        print()
        cprint(response, 'green')

    # inputs = {
    #     'query': query if query is not None else "Which users have poor signal quality in step 3?"
    # } 

    # try:
    #     result = OranSystem().crew().kickoff(inputs=inputs)
    #     return result
    # except Exception as e:
    #     raise Exception(f"An error occurred while running the crew: {e}")

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


# def train():
#     """
#     Train the crew for a given number of iterations.
#     """
#     inputs = {
#         "topic": "AI LLMs"
#     }
#     try:
#         OranSystem().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while training the crew: {e}")

# def replay():
#     """
#     Replay the crew execution from a specific task.
#     """
#     try:
#         OranSystem().crew().replay(task_id=sys.argv[1])

#     except Exception as e:
#         raise Exception(f"An error occurred while replaying the crew: {e}")

# def test():
#     """
#     Test the crew execution and returns the results.
#     """
#     inputs = {
#         "topic": "AI LLMs",
#         "current_year": str(datetime.now().year)
#     }
#     try:
#         OranSystem().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while testing the crew: {e}")
