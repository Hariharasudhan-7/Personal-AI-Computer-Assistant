from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownTextSplitter

def split_documents(documents: List[Document], strategy: str = "B") -> List[Document]:
    if strategy == "A":
        chunk_size = 1200
        chunk_overlap = 200
    elif strategy == "B":
        chunk_size = 900
        chunk_overlap = 150
    else:
        chunk_size = 1000
        chunk_overlap = 180

    text_splitter = MarkdownTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    chunks = text_splitter.split_documents(documents)
    
    print(f"Split {len(documents)} documents into {len(chunks)} chunks using Strategy {strategy} ({chunk_size}/{chunk_overlap}).")
    return chunks
