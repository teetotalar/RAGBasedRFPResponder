# RAG-Based Agentic RFP Responder

An agentic AI framework that automates RFP (Request for Proposal) responses using Retrieval-Augmented Generation (RAG).

This system supports:

- Excel-based compliance sheet automation (YES / NO / PARTIAL generation)
- PDF-based structured proposal generation
- Dynamic LLM provider switching (Gemini / Ollama)
- Local vector storage using Qdrant
- Knowledge base ingestion and chunking
- Context-aware response generation

---

##  Architecture Overview

RFP Input (Excel / PDF)
        ↓
Section Parser
        ↓
Agentic Orchestrator
        ↓
RAG Retrieval (Qdrant Vector DB)
        ↓
LLM Provider (Gemini or Ollama)
        ↓
Structured Enterprise Response
        ↓
Output Document

---

##  Features

- Model-agnostic (Gemini / Ollama)
- Config-driven model selection
- Runtime provider switching
- Resume-safe proposal generation
- Context-limited retrieval control
- Excel compliance automation
- Secure environment variable handling

---

## 📂 Folder Structure

fp_ai_framework/
│
├── main.py
├── ingest.py
├── config.yaml
├── requirements.txt
│
├── src/
│ ├── agentic_orchestrator.py
│ ├── batch_processor.py
│ ├── config_loader.py
│ ├── ingest_kb.py
│ ├── pdf_section_parser.py
│ ├── proposal_generator.py
│ └── rag_engine.py
│
├── knowledge_base_docs/
├── rfp_inputs/
└── rfp_outputs/