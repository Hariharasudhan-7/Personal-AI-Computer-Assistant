from __future__ import annotations

from file_automation_agent.ai.agent import FileAutomationAgent


def run_cli(base_dir: str = ".") -> None:
    agent = FileAutomationAgent(base_dir=base_dir)
    print("========================================")
    print(" PERSONAL AI FILE AUTOMATION AGENT")
    print("========================================")

    while True:
        try:
            user_input = input("\nYou: ")
        except EOFError:
            print("\nGoodbye.")
            break

        if user_input.strip().lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        result = agent.process_command(user_input)
        print(f"\nAI: {result.get('response') or 'Done.'}")
        for tool_result in result.get("tool_results", []):
            if tool_result.get("ok"):
                print(f"- {tool_result['tool']}: success")
            else:
                print(f"- {tool_result['tool']}: {tool_result.get('error', 'failed')}")
