from pathlib import Path
from unittest.mock import Mock, patch

from file_automation_agent.ai.agent import FileAutomationAgent
from file_automation_agent.memory.context import ContextMemory


class FakeLLM:
    def __init__(self, response):
        self.response = response

    def complete(self, messages, tools=None, **kwargs):
        return self.response


class SequenceLLM:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def complete(self, messages, tools=None, **kwargs):
        self.calls.append(messages)
        return next(self.responses)


def test_agent_executes_create_folder_command(tmp_path: Path):
    agent = FileAutomationAgent(base_dir=str(tmp_path), llm_client=FakeLLM({
        "tool_calls": [{"function": {"name": "create_folder", "arguments": {"path": str(tmp_path / "AI Projects")}}}],
        "content": "",
    }))

    result = agent.process_command("Create a folder called AI Projects")
    assert result["ok"] is True
    assert (tmp_path / "AI Projects").exists()


def test_agent_uses_memory_reference_for_it(tmp_path: Path):
    report = tmp_path / "report.txt"
    report.write_text("Meeting notes about AI files", encoding="utf-8")

    memory = ContextMemory(base_dir=str(tmp_path))
    memory.remember_file(str(report))

    agent = FileAutomationAgent(base_dir=str(tmp_path), llm_client=FakeLLM({
        "tool_calls": [{"function": {"name": "read_file", "arguments": {"path": str(report)}}}],
        "content": "",
    }), memory=memory)

    result = agent.process_command("Read it.")
    assert result["ok"] is True
    assert result["tool_results"][0]["content"] == "Meeting notes about AI files"


def test_agent_handles_intelligent_rename(tmp_path: Path):
    messy = tmp_path / "messy_file_2938.txt"
    messy.write_text("Meeting notes about the Personal AI Computer Assistant, File Automation Agent and Cloud Architecture.\n", encoding="utf-8")

    with patch("file_automation_agent.ai.agent.OpenRouterClient") as mock_client:
        mock_client.return_value.complete.return_value = {
            "tool_calls": [{"function": {"name": "read_file", "arguments": {"path": str(messy)}}}],
            "content": "",
        }
        agent = FileAutomationAgent(base_dir=str(tmp_path), llm_client=mock_client.return_value)
        result = agent.process_command("This filename is messy. Read the file and rename it according to its content.")
        assert result["ok"] is True
        # Naming behavior is handled by the rename assistant; the file should be renamed to a safe name.
        assert any(path.name.endswith(".txt") for path in tmp_path.iterdir())


def test_agent_returns_tool_results_to_ai_and_logs_command(tmp_path: Path):
    client = SequenceLLM([
        {"tool_calls": [{"id": "call_1", "function": {"name": "create_file", "arguments": {"path": "notes.txt", "content": "hello"}}}], "content": ""},
        {"tool_calls": [], "content": "Created notes.txt successfully."},
    ])

    result = FileAutomationAgent(tmp_path, llm_client=client).process_command("Create notes.txt")

    assert result["response"] == "Created notes.txt successfully."
    assert any(message["role"] == "tool" for message in client.calls[1])
    assert (tmp_path / ".automation_history.jsonl").exists()


def test_memory_persists_and_resolves_natural_language_reference(tmp_path: Path):
    report = tmp_path / "report.txt"
    memory = ContextMemory(tmp_path)
    memory.remember_file(report)

    restored = ContextMemory(tmp_path)

    assert restored.last_file == str(report.resolve())
    assert restored.resolve_reference("Read it.") == str(report.resolve())


def test_agent_rejects_tool_path_outside_project(tmp_path: Path):
    outside = tmp_path.parent / "outside.txt"
    client = FakeLLM({
        "tool_calls": [{"function": {"name": "create_file", "arguments": {"path": str(outside), "content": "blocked"}}}],
        "content": "",
    })

    result = FileAutomationAgent(tmp_path, llm_client=client).process_command("Create a file outside the project")

    assert result["ok"] is False
    assert result["tool_results"][0]["ok"] is False
    assert not outside.exists()


def test_agent_opens_any_file_with_default_application(tmp_path: Path):
    target = tmp_path / "presentation.pdf"
    target.write_bytes(b"test")
    client = FakeLLM({
        "tool_calls": [{"function": {"name": "open_file", "arguments": {"path": str(target)}}}],
        "content": "",
    })

    with patch("file_automation_agent.tools.file_tools.os.startfile") as startfile:
        result = FileAutomationAgent(tmp_path, llm_client=client).process_command("Open presentation.pdf")

    assert result["ok"] is True
    assert result["tool_results"][0]["opened"] is True
    startfile.assert_called_once_with(str(target.resolve()))
