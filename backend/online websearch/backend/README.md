# Personal AI Computer Assistant: Terminal Web Search

Terminal-only backend workflow: your question is sent to Gemini 3.6 Flash to create an optimized search query, the top five DuckDuckGo results are collected, and Gemini uses those results plus your original question to write the answer. Gemini 2.5 Flash is unavailable to new users with the current API access.

## Setup

From the `backend` directory:

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `GEMINI_API_KEY` in `.env`. The key is never logged or returned by the API.

## Run the assistant

```bash
python -m app.main
```

Enter a question at the `You:` prompt. Type `exit` or `quit` to stop.

## Tests and checks

```bash
pytest -q
python -m compileall app tests
```

The program prints the generated search query, the final Gemini answer, and the five source URLs.
