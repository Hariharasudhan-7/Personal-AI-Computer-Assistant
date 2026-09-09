from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from backend.RAG.chunking import split_documents
from backend.RAG.embeddings import get_huggingface_embeddings
from backend.RAG.loader import load_documents_from_paths
from backend.RAG.retriever import get_retriever
from backend.RAG.rag_pipeline import generate_answer
from backend.RAG.vectorstore import create_and_save_vectorstore


class AttachmentRAG:
    def __init__(self) -> None:
        self._retrievers: dict[str, Any] = {}
        self._embeddings: Any | None = None

    def register(self, attachment_id: str, file_path: str | Path) -> None:
        documents = load_documents_from_paths([str(file_path)], extract_images=False)
        if not documents:
            raise ValueError("The uploaded PDF contains no readable text.")

        chunks = split_documents(documents, strategy="B")
        if self._embeddings is None:
            self._embeddings = get_huggingface_embeddings()
        vectorstore = create_and_save_vectorstore(
            chunks,
            self._embeddings,
            index_path=str(Path(file_path).with_suffix(".faiss")),
        )
        self._retrievers[attachment_id] = get_retriever(vectorstore, strategy="similarity", top_k=3)

    def retriever_for_attachment(self, attachment_id: str) -> Any | None:
        return self._retrievers.get(attachment_id)

    def answer_question(self, **kwargs: Any) -> tuple[str, list[Any]]:
        return generate_answer(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model_name=os.getenv("RAG_MODEL", "gemini-2.5-flash"),
            provider=os.getenv("RAG_PROVIDER", "gemini"),
            **kwargs,
        )