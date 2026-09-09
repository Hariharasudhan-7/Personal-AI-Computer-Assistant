import logging

from app.config import get_settings
from app.services.web_search_agent import WebSearchAgent, WebSearchAgentError

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def main() -> None:
    """Read terminal queries and print Gemini's answer."""
    try:
        agent = WebSearchAgent(get_settings())
    except Exception as exc:
        print(f"Configuration error: {exc}")
        return

    print("Personal AI Computer Assistant - Online Web Search")
    print("Type a question, or type 'exit' to quit.\n")
    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return
        if query.lower() in {"exit", "quit"}:
            print("Goodbye!")
            return
        if not query:
            print("Please enter a question.\n")
            continue
        try:
            response = agent.run(query)
            print(f"\nSearch query: {response.search_query}")
            print("Sources:")
            for index, result in enumerate(response.results, start=1):
                print(f"{index}. {result.title} - {result.url}")
            print(f"\n===== FINAL ANSWER =====\n{response.answer}\n")
        except WebSearchAgentError as exc:
            print(f"Search error: {exc}\n")


if __name__ == "__main__":
    main()
