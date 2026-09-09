from __future__ import annotations

import os
from uuid import uuid4

from dotenv import load_dotenv

from .runtime import build_runtime_main_ai


def run_terminal() -> None:
    """Run the Main AI workflow as an interactive terminal application."""
    load_dotenv()
    conversation_id = os.getenv("CONVERSATION_ID", str(uuid4()))
    user_id = os.getenv("USER_ID", "local-user")

    print("Personal AI Computer Assistant")
    print("Type a request, /help for commands, or /exit to quit.")

    try:
        main_ai = build_runtime_main_ai()
    except Exception as error:
        print(f"Startup failed: {error}")
        print("Check OPENROUTER_API_KEY, N8N webhook URLs, and your Python environment.")
        return

    while True:
        try:
            query = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not query:
            continue
        if query.lower() in {"/exit", "/quit"}:
            break
        if query.lower() == "/help":
            print("Enter any request. Main AI selects mail, drive, calendar, file automation, or web search.")
            print("Document/RAG questions require an indexed attachment and will be enabled in the document workflow.")
            print("Commands: /help, /exit")
            continue

        try:
            response = main_ai.handle_message(
                user_id=user_id,
                conversation_id=conversation_id,
                content=query,
            )
            print(f"AI [{response.tool_name or 'general'}]> {response.message}")
            if response.error:
                print(f"  Error: {response.error}")
            if response.citations:
                for citation in response.citations:
                    if citation.get("url"):
                        print(f"  Source: {citation['url']}")
        except Exception as error:
            print(f"AI> Request failed: {error}")