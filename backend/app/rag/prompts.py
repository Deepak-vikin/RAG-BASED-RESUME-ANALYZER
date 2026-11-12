from typing import List
from langchain_core.documents import Document
from backend.app.schemas.chat import ChatMessage

SYSTEM_PROMPT = """You are an expert Document Intelligence Assistant. Your primary goal is to answer the user's questions truthfully, accurately, and concisely based ONLY on the provided document excerpts.

Strict Grounding Rules:
1. Grounding: Rely strictly on facts directly mentioned in the Context below. Do NOT assume, extrapolate, or invent details not present in the text.
2. Missing Information: If the context does not contain enough information to answer the question, state clearly: "I cannot find the answer to this question in the provided document." Do not try to make up an answer.
3. Citations: When answering, reference the document name and page number(s) if provided in the context (e.g. "[Source: resume.pdf, Page: 1]").
4. Tone & Style: Be professional, well-structured, objective, and clear. Format answers with markdown bullet points, tables, or bold headers where appropriate.
"""

def format_context_from_documents(docs: List[Document]) -> str:
    """
    Format retrieved LangChain documents into a clear context block for the prompt.
    """
    if not docs:
        return "No relevant document excerpts found."

    context_blocks = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown Document")
        page = doc.metadata.get("page", "N/A")
        header = f"--- Excerpt {i} [Source: {source} | Page: {page}] ---"
        context_blocks.append(f"{header}\n{doc.page_content.strip()}")

    return "\n\n".join(context_blocks)


def construct_rag_messages(
    question: str,
    context: str,
    history: List[ChatMessage] = None
) -> List[dict]:
    """
    Constructs OpenAI/OpenRouter compatible messages payload:
    - system prompt
    - optional past conversation turns
    - user message containing the grounded context and latest question
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # Include recent conversation turns (last 6 turns = 3 user/assistant pairs)
    if history:
        for msg in history[-6:]:
            if msg.role in ["user", "assistant"]:
                messages.append({"role": msg.role, "content": msg.content})

    user_content = (
        f"Context from uploaded document(s):\n"
        f"```\n{context}\n```\n\n"
        f"User Question: {question}\n\n"
        f"Provide your answer grounded strictly in the context above:"
    )

    messages.append({"role": "user", "content": user_content})
    return messages

