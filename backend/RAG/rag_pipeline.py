import os
from typing import List, Dict, Tuple
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from langchain_ollama import ChatOllama
except ImportError:  # pragma: no cover - optional 
    ChatOllama = None

def format_docs(docs: List[Document]) -> str:
    formatted = []
    for i, doc in enumerate(docs):
        # We also pass the citation metadata to the model so it understands the source
        source = doc.metadata.get("source", "Unknown Source")
        page = doc.metadata.get("page", "Unknown Page")
        formatted.append(f"--- Document {i+1} [Source: {source}, Page: {page}] ---\n{doc.page_content}")
    return "\n\n".join(formatted)

def get_rag_chain(api_key: str, model_name: str = "gemini-3.1-flash-latest", retriever=None, provider: str = "gemini"):
    provider_name = (provider or "gemini").lower()

    if provider_name == "ollama" or model_name.startswith("ollama:"):
        if ChatOllama is None:
            raise ImportError("The 'langchain-ollama' package is required for Ollama support.")

        ollama_model = model_name.replace("ollama:", "", 1) if model_name.startswith("ollama:") else model_name
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
        llm = ChatOllama(
            model=ollama_model,
            base_url=base_url,
            temperature=0.0,
        )
    else:
        if not api_key:
            raise ValueError("Google Gemini API Key is missing.")

        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.0,
        )
    
    # Custom rules for explanation and external knowledge
    system_prompt = (
    "You are 'AnswerBOT', an AI assistant specialized in answering questions using only the provided research paper context.\n\n"

    "Instructions:\n"

    "1. Answers for the user's question using ONLY the provided context.\n"

    "2. If the answer exists in the provided context: - Return the answer.\n"

    "3. If the answer does not exist in the provided context: - Return ONLY: 'This is an irrelevant question to the current given source so please ask the relevant questions'\n"
    """- Do NOT add any explanation."
    "- Do NOT mention that the context is missing.
    - Do NOT include a Sources section or citations.
    - Do NOT prepend or append any other text.\n"""

    "4. Also if the user ask any other questions other than the provided content then just say 'This is the irrelavant question to the current given source so please ask the relavant questions' then also don't show any supporting citations or sources since the question is out of the provided content.\n"

    "5. No need of any extra explaination for the out of the content queries/questions just say 'This is the irrelavant question to the current given source so please ask the relavant questions'\n"

    "6. Do NOT use prior knowledge, assumptions, or external information. If the required information is not explicitly present in the provided context,you much answer as it was mentioned in below . Do not add explanations, guesses, or additional information.\n"

    "7. Base every statement in your answer on the retrieved context. Do not invent facts, references, equations, technical details, or any other content from out of the provided content.\n"

    "8. If multiple retrieved passages contain complementary information, combine them into a single coherent answer while remaining faithful to the source.\n"

    "9. If the retrieved context contains formatting issues caused by PDF extraction (such as missing spaces, broken words, merged code, misplaced line breaks, or inconsistent indentation), reconstruct the text naturally without changing its original meaning.\n"

    "10. Preserve all technical terminology, mathematical notation, variable names, function names, model names, and abbreviations exactly as they appear whenever possible. \n"

    "11. Provide clear, concise, and well-structured answers without introducing information that is not supported by the context.\n" 
    
    "12. Even through the query by the user is relavent to the training data you should never answer to those questions u need the answer as mentioned above you are never allowed to answer the general answers you are allowed to answer only from the provided content.\n"

    "13. Follow all the above instructions strictly\n"
    "\nContext:\n{context}"
)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])
    
    rag_chain = prompt | llm | StrOutputParser()
    
    return rag_chain


def generate_answer(query: str, retriever, api_key: str = "", model_name: str = "gemini-2.5-flash", chat_history: List[Dict] = None, provider: str = "gemini") -> Tuple[str, List[Document]]:
    provider_name = (provider or "gemini").lower()

    if provider_name != "ollama" and not api_key:
        raise ValueError("Google Gemini API Key is missing.")

    # 1. Rephrase query based on chat history to get accurate search results
    search_query = query
    lc_messages = []
    
    if chat_history and len(chat_history) > 1: # More than just the current user message
        # Convert local chat_history dicts to Langchain Message objects
        for msg in chat_history[:-1]: # Exclude the current query which is the last item
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
                
        
    retrieved_docs = retriever.invoke(search_query)
    
    # 3. Format Context
    context_str = format_docs(retrieved_docs)
    
    # 4. Generate Answer with Full Conversation History
    chain = get_rag_chain(api_key, model_name, provider=provider_name)
    answer = chain.invoke({
        "context": context_str,
        "chat_history": lc_messages, 
        "question": query
    })
    
    return answer, retrieved_docs
