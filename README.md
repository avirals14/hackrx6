
# 🔍 PolicyLens — AI-Powered Insurance Query Engine

**PolicyLens** is an intelligent backend system that uses Large Language Models (LLMs) to process natural language queries against complex, unstructured insurance documents and deliver reliable, clause-anchored, audit-grade decisions with confidence scoring.

---

## 🚀 Key Features

- 📄 **Supports Diverse Input Docs**: Upload PDFs, Word files, and emails (like insurance policies or benefit tables)
- 🧠 **LLM-Powered Reasoning**: Uses OpenAI GPT-4o, Gemini Pro, and local models (Ollama: LLaMA3/Gemma) to reason over retrieved clauses with strict clause anchoring and confidence scoring
- 🔁 **Multi-Model Inference Flow**: Automatically falls back between OpenAI → Gemini → Ollama for high availability and flexibility
- 🧾 **Semantic Clause Retrieval**: Embeds document chunks and fetches only the most relevant policy clauses
- 🛠️ **Robust JSON Repair Engine**: Repairs malformed LLM output using regex, demjson3, rapidjson, or Gemini-based recovery
- 📦 **Audit-Grade Output**: Decision + Justification + Referenced Clause Numbers + User Summary + Confidence Score

---

## 📂 Folder Overview

```
/backend
  ├── main.py
  ├── llm.py               # Handles LLM prompting, strict audit-grade prompting, fallback, and JSON parsing
  ├── retriever.py         # Chunking and semantic search logic
  ├── parser.py            # Text extraction from PDFs/docs
  ├── .env                 # API keys for OpenAI & Gemini
/frontend
  └── (optional Next.js UI)
```

---

## ⚙️ Getting Started

### 1️⃣ Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate (Windows)
pip install -r requirements.txt
```

**.env Example**
```
OPENAI_API_KEY=sk-xxx
GEMINI_API_KEY=your-gemini-key
# Never commit this file! Add .env to .gitignore
```

Run locally:
```bash
uvicorn main:app --reload
```

---

### 2️⃣ Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Example Query

```
"46-year-old male, knee surgery in Pune, 3-month-old insurance policy"
```

**Output**
```json
{
  "decision": "denied",
  "amount": 0,
  "justification": "Clause 4.2 states knee surgery is covered only after a 24-month waiting period. The policy is only 3 months old.",
  "clauses_used": ["Clause 4.2"],
  "summary": "Claim denied due to 24-month waiting period for knee surgery.",
  "confidence": 0.95
}
```
*If the LLM cannot make a decision based on the provided clauses, it will return:*
```json
{
  "decision": "pending_info",
  "amount": 0,
  "justification": "The LLM response was incomplete or no clause could be definitively matched. Manual review required.",
  "clauses_used": [],
  "summary": "Unable to determine decision automatically.",
  "confidence": 0.0
}
```

---

## 🔐 Security & Traceability

- .env secrets never exposed (add `.env` to `.gitignore`)
- LLM decisions always tied to explicit clause references (no hallucinated clause numbers)
- Confidence score for every decision
- Designed for compliance, audit logs, and reliability

---

## 🎯 Use Cases

- Insurance underwriting and claims automation
- Legal & compliance document evaluation
- Smart contract understanding and interpretation
- HR or finance policy resolution bots

---

## 📌 Future Roadmap

- ✅ Document OCR (for scanned PDFs)
- ✅ Clause highlighting in frontend
- ✅ User feedback loop for LLM fine-tuning
- ✅ Claim submission dashboard

---

## 📃 License

MIT License

---

## 👨‍💻 Maintainer

**Project**: PolicyLens  
**Built by**: [Aviral Sharma] — [https://github.com/avirals14]  
Let’s improve document intelligence, one query at a time.
