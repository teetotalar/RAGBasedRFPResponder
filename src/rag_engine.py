# src/rag_engine.py

import os
import requests
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from src.config_loader import load_config


# -------------------------------
# Load config
# -------------------------------

config = load_config()

TOP_K_EXCEL = config.get("top_k_excel", 1)
TOP_K_PDF = config.get("top_k_pdf", 3)

MAX_CONTEXT_EXCEL = config.get("max_context_excel", 800)
MAX_CONTEXT_PDF = config.get("max_context_pdf", 2000)

OLLAMA_EXCEL_MODEL = config.get("ollama_excel_model", "gemma:2b")
OLLAMA_PDF_MODEL = config.get("ollama_pdf_model", "llama3:8b-instruct-q4_K_M")

GEMINI_EXCEL_MODEL = config.get("excel_model")
GEMINI_PDF_MODEL = config.get("pdf_model")

LLM_ENDPOINT = "http://localhost:11434/api/generate"

# Single fallback constant — used across all generation paths
FALLBACK_RESPONSE = "Based on the current knowledge base, limited information is available."


# -------------------------------
# Lazy-loaded singletons
# Avoids loading model on every import
# -------------------------------

_embedding_model = None
_qdrant_client = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("   → Loading embedding model...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(path="qdrant_storage")
    return _qdrant_client


# -------------------------------
# Retrieval
# -------------------------------

def retrieve_context(query, mode="answer"):
    """
    Retrieves relevant context chunks from the vector store.

    mode="compliance"  → uses Excel top_k and context limits
    mode="proposal"    → uses PDF top_k and context limits
    mode="answer"      → same as proposal (PDF settings)
    """
    embedding_model = get_embedding_model()
    qdrant = get_qdrant_client()

    query_embedding = embedding_model.encode(query).tolist()

    # compliance uses tighter retrieval; proposal/answer uses broader
    top_k = TOP_K_EXCEL if mode == "compliance" else TOP_K_PDF
    max_context = MAX_CONTEXT_EXCEL if mode == "compliance" else MAX_CONTEXT_PDF

    results = qdrant.query_points(
        collection_name="knowledge_base",
        query=query_embedding,
        limit=top_k
    ).points

    # Truncate each chunk cleanly at sentence boundary before joining
    chunks = []
    for point in results:
        chunk = point.payload.get("text", "").strip()
        if chunk:
            chunks.append(_truncate_at_sentence(chunk, max_context // top_k))

    context = "\n".join(chunks)

    # Final safety truncation at sentence boundary
    return _truncate_at_sentence(context, max_context)


def _truncate_at_sentence(text, max_chars):
    """
    Truncates text to max_chars at the last full stop to avoid mid-sentence cuts.
    """
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    last_period = truncated.rfind(".")

    if last_period != -1:
        return truncated[:last_period + 1]

    return truncated  # No period found, return hard truncation


# -------------------------------
# Generation
# -------------------------------

def generate_answer(context, query, mode="answer", provider="ollama"):
    """
    Generates an LLM response using either Gemini or Ollama.

    mode="compliance" → YES/NO/PARTIAL + justification
    mode="proposal"   → structured enterprise proposal section
    mode="answer"     → same prompt template as proposal
    """

    if mode == "compliance":
        system_prompt = """
You are a senior enterprise presales consultant responding to an RFP compliance sheet.

First line must be exactly one of:
YES
NO
PARTIAL

Then provide 4–6 lines of technical justification.
No fluff. No marketing language.
"""
    else:
        # Handles both "proposal" and "answer" modes
        system_prompt = """
You are an enterprise presales architect preparing a formal RFP response.

REQUIREMENTS:
- 2–4 structured paragraphs.
- Cover all listed requirements explicitly.
- Professional enterprise tone.
- No placeholders.
- No one-line answers.
- No marketing exaggeration.
"""

    prompt = f"""
{system_prompt}

Context:
{context}

Requirement:
{query}
"""

    # -------------------------
    # GEMINI PROVIDER
    # -------------------------

    if provider == "gemini":

        model_name = GEMINI_EXCEL_MODEL if mode == "compliance" else GEMINI_PDF_MODEL

        try:
            model = genai.GenerativeModel(model_name)

            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 900
                }
            )

            if response and response.text:
                return response.text.strip()

            return FALLBACK_RESPONSE

        except Exception as e:
            print(f"⚠ Gemini error: {e}")
            return FALLBACK_RESPONSE

    # -------------------------
    # OLLAMA PROVIDER
    # -------------------------

    else:

        model_name = OLLAMA_EXCEL_MODEL if mode == "compliance" else OLLAMA_PDF_MODEL

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 180,
                "temperature": 0.3
            }
        }

        try:
            response = requests.post(
                LLM_ENDPOINT,
                json=payload,
                timeout=400
            )

            if response.status_code == 200:
                return response.json().get("response", "").strip()

            print(f"⚠ Ollama returned status {response.status_code}")
            return FALLBACK_RESPONSE

        except Exception as e:
            print(f"⚠ Ollama error: {e}")
            return FALLBACK_RESPONSE