# HR Assist — Resume RAG Pipeline

> Semantic candidate search over a 100k+ resume corpus — hitting **70–90% eval accuracy** against a hard-criteria benchmark, built as a Mercor engineering take-home.

---

## The Problem

Natural language hiring queries are messy. A recruiter asking for *"a US-trained physician with 2+ years as a GP, skilled in telemedicine"* needs a system that understands **mandatory constraints** (US medical degree, GP role) separately from **nice-to-haves** (telemedicine experience). Most retrieval systems treat everything as soft signal — and rank a brilliant Indian radiologist above a mediocre US GP for that query.

This pipeline was designed to fix that.

---

## Results

| Approach | Avg Eval Score |
|---|---|
| Baseline (vector search + RAG-Fusion + weighted param extraction) | ~50–60% |
| **This pipeline** | **70–90%** |

Evaluated against Mercor's benchmark across 10 candidate profiles (tax lawyers, radiologists, quant finance, mechanical engineers, and more) drawn from a corpus of **100,000+ candidates**.

---

## Architecture

```
Natural Language Query
        │
        ▼
┌───────────────────┐
│  Query Rewriter   │  GPT-4.1-nano — splits query into hard criteria
│  (Hard + Soft)    │  and soft criteria for downstream precision
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Filter Extractor │  GPT-4.1-nano — extracts structured metadata
│  (Country, YoE)   │  filters (country, years of experience ranges)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Voyage-3 Embed   │  Embeds the original + rewritten query together
│  (query_type)     │  for richer semantic representation
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Qdrant Search    │  Cosine similarity search with hard metadata
│  (hybrid filter)  │  pre-filters — returns top 50 candidate IDs
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  MongoDB Fetch    │  Retrieves full candidate documents (experience,
│                   │  education, skills, awards, prestige score)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  LLM Re-Ranker    │  Two-phase GPT-4.1-nano judge:
│  (2-phase)        │  Phase 1 → hard constraint pass/fail (0–15)
│                   │  Phase 2 → soft criteria scoring (20–100)
└────────┬──────────┘
         │
         ▼
   Ranked Candidates
   (with per-candidate
   constraint audit trail)
```

---

## What Makes It Work

### 1. Query Rewriting Before Embedding
Rather than embedding the raw user query, the pipeline first decomposes it into **hard criteria** (non-negotiable: degree, country, role) and **soft criteria** (preferred: awards, prestige, specialization). The combined rewritten query produces a far more discriminative embedding than the original prose.

### 2. Two-Phase LLM Re-Ranking
The re-ranker is an explicit constraint-checking system, not a vague "rank by relevance" prompt.

- **Phase 1 — Hard Constraints**: Each candidate is evaluated against a checklist. Fail *any* single hard criterion → score capped at 0–15. No exceptions.
- **Phase 2 — Soft Scoring**: Only candidates who pass all hard constraints are scored 20–100 on prestige, skills depth, and career progression.

The JSON schema output (`hard_constraints_passed`, `hard_constraints_failed`, `detailed_reason_for_ranking`) creates a full audit trail for every decision — explainable ranking, not a black box.

### 3. Metadata Pre-Filtering at the Vector Layer
Country and years-of-experience filters are applied *inside* Qdrant before cosine similarity is scored — reducing the candidate pool size and preventing spurious high-similarity matches from irrelevant geographies from polluting the top-50 shortlist.

### 4. Prestige Score as a Latent Signal
Each resume payload carries a `prestigeScore` computed upstream. This is used as an additional tiebreaker signal during retrieval ordering without overriding semantic relevance.

---

## Why This Beats RAG-Fusion + Weighted Params

RAG-Fusion generates multiple query variants and fuses ranked lists — great for recall, poor for precision on hard constraints. A candidate with an IIT degree and 10 years of ML experience can rank above a US-trained GP on a medical query just by semantic overlap.

This pipeline treats hard criteria as **filters**, not **signals** — which is how recruiters actually think.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM (query rewrite, filter extract, re-rank) | OpenAI GPT-4.1-nano |
| Embeddings | Voyage AI `voyage-3` |
| Vector Store | Qdrant (cloud) |
| Document Store | MongoDB |
| Proxy / Batching Server | FastAPI + priority queue |
| Data Ingestion | Python + multithreaded batch migration |

---

## Repository Structure

```
├── init.py            # Main search pipeline (end-to-end)
├── prompts.py         # All LLM prompts (query rewrite, re-ranking, filter extraction)
├── schema.py          # JSON schemas for structured LLM output
├── migration.py       # Parallel batch migration into Qdrant
└── proxy_server/
    └── proxy.py       # FastAPI priority-queue proxy for batched classification
```

---

## Domain Coverage

Pipeline tested and evaluated across 10 professional domains:

Tax Law · Corporate Law · Radiology · General Medicine · Biology · Anthropology · Mathematics · Quantitative Finance · Investment Banking · Mechanical Engineering

---

*Built as part of the Mercor Search Engineering challenge.*
