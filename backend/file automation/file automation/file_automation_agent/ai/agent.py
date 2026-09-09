from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from file_automation_agent.ai.openrouter_client import OpenRouterClient
from file_automation_agent.filesystem.path_manager import resolve_input_path, sanitize_filename
from file_automation_agent.memory.context import ContextMemory
from file_automation_agent.memory.history import HistoryLogger
from file_automation_agent.safety.validator import SafetyValidator
from file_automation_agent.tools.file_tools import append_file, copy_file, create_file, delete_file, move_file, open_file, read_file, rename_file, write_file
from file_automation_agent.tools.folder_tools import copy_folder, create_folder, delete_folder, list_directory, move_folder, rename_folder
from file_automation_agent.tools.intelligence_tools import analyze_file_content, detect_duplicates, generate_filename, organize_files
from file_automation_agent.tools.search_tools import get_file_metadata, search_file_content, search_files


TOOL_DEFS = [
    {"type": "function", "function": {"name": "open_file", "description": "Open a file using the operating system's default application. Supports any file type associated with an installed application.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "create_file", "description": "Create a new file with content.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a file's content.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Overwrite a file with content.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "append_file", "description": "Append text to a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "rename_file", "description": "Rename a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "new_path": {"type": "string"}}, "required": ["path", "new_path"]}}},
    {"type": "function", "function": {"name": "delete_file", "description": "Delete a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "copy_file", "description": "Copy a file to a destination.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "destination": {"type": "string"}}, "required": ["path", "destination"]}}},
    {"type": "function", "function": {"name": "move_file", "description": "Move a file to a destination.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "destination": {"type": "string"}}, "required": ["path", "destination"]}}},
    {"type": "function", "function": {"name": "create_folder", "description": "Create a folder.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "list_directory", "description": "List directory contents.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "rename_folder", "description": "Rename a folder.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "new_path": {"type": "string"}}, "required": ["path", "new_path"]}}},
    {"type": "function", "function": {"name": "delete_folder", "description": "Delete a folder.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "recursive": {"type": "boolean"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "copy_folder", "description": "Copy a folder.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "destination": {"type": "string"}}, "required": ["path", "destination"]}}},
    {"type": "function", "function": {"name": "move_folder", "description": "Move a folder.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "destination": {"type": "string"}}, "required": ["path", "destination"]}}},
    {"type": "function", "function": {"name": "search_files", "description": "Search for files by name or extension.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "name": {"type": "string"}, "extension": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "search_file_content", "description": "Search file contents for text.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "query": {"type": "string"}}, "required": ["path", "query"]}}},
    {"type": "function", "function": {"name": "get_file_metadata", "description": "Fetch metadata for a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "analyze_file_content", "description": "Analyze a file's content snippet.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "generate_filename", "description": "Generate a safe filename based on content or context.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "suggested_name": {"type": "string"}, "extension": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "organize_files", "description": "Organize files in a folder by extension.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "detect_duplicates", "description": "Detect duplicate files by hash.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
]


FUNCTION_MAP = {
    "open_file": open_file,
    "create_file": create_file,
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "rename_file": rename_file,
    "delete_file": delete_file,
    "copy_file": copy_file,
    "move_file": move_file,
    "create_folder": create_folder,
    "list_directory": list_directory,
    "rename_folder": rename_folder,
    "delete_folder": delete_folder,
    "copy_folder": copy_folder,
    "move_folder": move_folder,
    "search_files": search_files,
    "search_file_content": search_file_content,
    "get_file_metadata": get_file_metadata,
    "analyze_file_content": analyze_file_content,
    "generate_filename": generate_filename,
    "organize_files": organize_files,
    "detect_duplicates": detect_duplicates,
}


class FileAutomationAgent:
    def __init__(self, base_dir: str | Path, llm_client: OpenRouterClient | Any | None = None, memory: ContextMemory | None = None):
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.memory = memory or ContextMemory(self.base_dir)
        self.history_logger = HistoryLogger(self.base_dir)
        self.llm_client = llm_client or OpenRouterClient()

    def _build_prompt(self, user_input: str) -> list[dict[str, str]]:
        context = {
            "last_file": self.memory.last_file,
            "last_folder": self.memory.last_folder,
        }
        return [
            {"role": "system", "content": f"You are a safe filesystem automation agent. Use tools only through the provided function registry and validate outputs before claiming success. Current memory: {json.dumps(context)}"},
            {"role": "user", "content": user_input},
        ]

    def _normalize_tool_call(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        name = tool_call.get("function", {}).get("name")
        arguments = tool_call.get("function", {}).get("arguments", {})
        if not isinstance(arguments, dict):
            arguments = {}
        if "path" in arguments and arguments["path"]:
            arguments["path"] = str(resolve_input_path(self.base_dir, arguments["path"]))
        if "destination" in arguments and arguments["destination"]:
            arguments["destination"] = str(resolve_input_path(self.base_dir, arguments["destination"]))
        if "new_path" in arguments and arguments["new_path"]:
            arguments["new_path"] = str(resolve_input_path(self.base_dir, arguments["new_path"]))
        try:
            validator = SafetyValidator(self.base_dir)
            for key in ("path", "destination", "new_path"):
                if arguments.get(key):
                    validator.validate_path(arguments[key])
        except (OSError, ValueError) as exc:
            return {"name": name, "arguments": arguments, "error": str(exc)}
        if "path" in arguments and arguments["path"] and name == "read_file":
            self.memory.remember_file(arguments["path"])
        if "path" in arguments and arguments["path"] and name and "folder" in name.lower():
            self.memory.remember_folder(arguments["path"])
        return {"name": name, "arguments": arguments}

    def process_command(self, user_input: str) -> dict[str, Any]:
        messages: list[dict[str, Any]] = self._build_prompt(user_input)
        reference = self.memory.resolve_reference(user_input)
        if reference:
            messages[1]["content"] = f"User is referring to the recently active file/folder: {reference}. Context: {user_input}"

        tool_results = []
        response: dict[str, Any] = {"content": "", "tool_calls": []}
        previous_signature: str | None = None
        for _ in range(5):
            response = self.llm_client.complete(messages, tools=TOOL_DEFS)
            tool_calls = response.get("tool_calls", [])
            if not tool_calls:
                break

            signature = json.dumps(tool_calls, sort_keys=True, default=str)
            if signature == previous_signature:
                break
            previous_signature = signature

            assistant_tool_calls = []
            for index, tool_call in enumerate(tool_calls):
                call_id = tool_call.get("id") or f"call_{index}"
                candidate = self._normalize_tool_call(tool_call)
                assistant_tool_calls.append({
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": candidate["name"],
                        "arguments": json.dumps(candidate["arguments"]),
                    },
                })
                func = FUNCTION_MAP.get(candidate["name"])
                if candidate.get("error"):
                    result = {"ok": False, "error": candidate["error"]}
                elif not func:
                    result = {"ok": False, "error": "Unknown tool."}
                else:
                    result = func(**candidate["arguments"])
                entry = {"tool": candidate["name"], "ok": bool(result.get("ok", False))}
                entry.update(result)
                tool_results.append(entry)
                self._remember_result(candidate["name"], result)

            messages.append({
                "role": "assistant",
                "content": response.get("content") or None,
                "tool_calls": assistant_tool_calls,
            })
            for call, result in zip(assistant_tool_calls, tool_results[-len(assistant_tool_calls):]):
                messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": call["function"]["name"],
                    "content": json.dumps(result, ensure_ascii=True),
                })

        if user_input.lower().startswith("this filename is messy") or "rename it according to its content" in user_input.lower():
            file_path = None
            for item in tool_results:
                if item.get("tool") == "read_file":
                    file_path = item.get("path")
                    break
            if file_path:
                content = read_file(file_path)["content"]
                clean_name = sanitize_filename(content.splitlines()[0][:40])
                suggested = f"{clean_name}.txt" if not clean_name.endswith(".txt") else clean_name
                result = rename_file(file_path, str(Path(file_path).parent / suggested))
                tool_results.append({"tool": "rename_file", "ok": bool(result.get("ok", False)), **result})

        self.history_logger.log({
            "command": user_input,
            "response": response.get("content", ""),
            "tool_results": [self._history_summary(item) for item in tool_results],
        })
        return {"ok": all(item.get("ok", False) for item in tool_results) if tool_results else True, "tool_results": tool_results, "response": response.get("content", "")}

    def _remember_result(self, tool_name: str, result: dict[str, Any]) -> None:
        path = result.get("path") or result.get("destination")
        if not path:
            return
        if "folder" in tool_name:
            self.memory.remember_folder(path)
        elif tool_name in {"create_file", "read_file", "write_file", "append_file", "rename_file", "copy_file", "move_file"}:
            self.memory.remember_file(path)

    @staticmethod
    def _history_summary(result: dict[str, Any]) -> dict[str, Any]:
        fields = {key: result[key] for key in ("tool", "ok", "path", "source", "destination", "error") if key in result}
        return fields
