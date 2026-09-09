from datetime import datetime, timedelta, timezone
import json
from typing import Any

from .database import SQLiteDatabase


class ConversationRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def history(self, conversation_id: str, limit: int = 20) -> list[dict[str, str]]:
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?",
                (conversation_id, limit),
            ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def save_turn(
        self,
        *,
        user_id: str,
        conversation_id: str,
        message_id: str,
        query: str,
        tool_name: str | None,
        tool_arguments: dict[str, Any],
        tool_result: dict[str, Any],
        assistant_message_id: str,
        assistant_content: str,
    ) -> None:
        turn_started_at = datetime.now(timezone.utc)
        user_timestamp = turn_started_at.isoformat()
        assistant_timestamp = (turn_started_at + timedelta(microseconds=1)).isoformat()
        with self.database.connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO conversations (id, user_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conversation_id, user_id, user_timestamp, user_timestamp),
            )
            connection.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (message_id, conversation_id, "user", query, user_timestamp),
            )
            if tool_name:
                connection.execute(
                    "INSERT INTO tool_runs (id, conversation_id, message_id, tool_name, arguments, result, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"{message_id}:tool", conversation_id, message_id, tool_name,
                        json.dumps(tool_arguments), json.dumps(tool_result),
                        "succeeded" if tool_result.get("ok") else "failed", user_timestamp,
                    ),
                )
            connection.execute(
                "INSERT INTO messages (id, conversation_id, role, content, tool_name, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    assistant_message_id, conversation_id, "assistant", assistant_content, tool_name,
                    json.dumps({"success": bool(tool_result.get("ok", True))}), assistant_timestamp,
                ),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (assistant_timestamp, conversation_id),
            )
