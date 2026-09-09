from langchain_core.vectorstores import VectorStoreRetriever
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

def get_retriever(vectorstore: FAISS, strategy: str = "similarity", top_k: int = 3):   
# Base FAISS similarity retriever
    base_similarity = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )
    
# Base FAISS MMR retriever
    base_mmr = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": top_k, "fetch_k": 20}
    )

    if strategy == "hybrid":
# Hybrid Search: BM25 + FAISS
# We need all documents from the vectorstore docstore
        docs = list(vectorstore.docstore._dict.values())
        if not docs:
            print("Warning: No documents found in docstore for Hybrid Search. Falling back to similarity.")
            return base_similarity
            
        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = top_k
        
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, base_similarity],
            weights=[0.5, 0.5]
        )
        print(f"Configured Hybrid retriever (k={top_k})")
        return ensemble_retriever
        
    elif strategy == "reranker":
# Reranker: hybrid + Cross-Encoder
# Use a higher top_k for the base retriever so the reranker has candidates to re-order
        candidates_k = max(10, top_k * 3)

# Create BM25 retriever
        docs = list(vectorstore.docstore._dict.values())

        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = candidates_k

# FAISS similarity retriever
        faiss_retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": candidates_k}
            )

# Hybrid Retriever
        reranker_base = EnsembleRetriever(
            retrievers=[bm25_retriever, faiss_retriever],
            weights=[0.5, 0.5]
            )
        
        model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
        compressor = CrossEncoderReranker(model=model, top_n=top_k)
        
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=reranker_base
        )
        print(f"Configured Reranker retriever (k={top_k})")
        return compression_retriever
        
    elif strategy == "mmr":
        print(f"Configured MMR retriever (k={top_k})")
        return base_mmr
        
    else:
        # Default to similarity search
        print(f"Configured Similarity retriever (k={top_k})")
        return base_similarity

def retrieve_context(retriever, query: str):
    docs = retriever.invoke(query)
    return docs
