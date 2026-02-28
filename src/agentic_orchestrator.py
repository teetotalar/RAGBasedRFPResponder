# src/agentic_orchestrator.py

from src.rag_engine import retrieve_context, generate_answer, FALLBACK_RESPONSE


def agentic_rfp_answer(question, mode="answer", provider="ollama", retries=2):
    """
    Orchestrates retrieval and generation for a single RFP question.

    Supports:
    - mode="compliance" → YES/NO/PARTIAL response
    - mode="proposal"   → structured proposal section
    - mode="answer"     → general answer (same as proposal)

    Retries on empty or fallback responses up to `retries` times.
    """

    for attempt in range(1, retries + 2):  # attempts = retries + 1

        try:
            print(f"      → [Agentic] Retrieving context (attempt {attempt})...")
            context = retrieve_context(question, mode)

            if not context.strip():
                print("      → [Agentic] ⚠ No context retrieved from knowledge base.")

            print(f"      → [Agentic] Drafting response...")
            response = generate_answer(context, question, mode, provider)

            # If a valid non-fallback response is returned, use it
            if response and response.strip() != FALLBACK_RESPONSE:
                return response

            print(f"      → [Agentic] ⚠ Fallback response received on attempt {attempt}.")

        except Exception as e:
            print(f"      → [Agentic] ⚠ Error on attempt {attempt}: {e}")

    # All attempts exhausted
    print("      → [Agentic] All attempts exhausted. Returning fallback.")
    return FALLBACK_RESPONSE