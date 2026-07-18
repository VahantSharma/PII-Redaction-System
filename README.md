# DOCX PII Redaction System

A Python system that detects and redacts Personally Identifiable Information (PII) from Microsoft Word (.docx) documents, replacing every detected entity with a realistic fake alternative that preserves the original format.

---

## Problem Statement

Organizations handle documents containing sensitive personal data — names, addresses, phone numbers, email addresses, financial identifiers, and more. This tool automates the redaction of all such PII from .docx files while preserving document formatting, producing a sanitized output suitable for safe sharing.

---

## Features

**Detects and redacts 10 types of PII:**

| PII Type | Detection Method | Example |
|----------|-----------------|---------|
| Person Names | spaCy NER + heuristic promotion | Rahul Sharma |
| Company Names | spaCy NER + suffix heuristics | Infosys Limited |
| Physical Addresses | Structured entity extraction | 42 MG Road, Mumbai 400001 |
| Email Addresses | Regex with validation | user@example.com |
| Phone Numbers | Regex (Indian formats) | +91 98765 43210 |
| Dates of Birth | strptime with 12 format variants | 15 March 1990 |
| Credit Card Numbers | Luhn validation + brand detection | 4111-1111-1111-1111 |
| National IDs | Regex (SSN formats) | 123-45-6789 |
| IPv4 Addresses | ipaddress stdlib validation | 192.168.1.1 |
| IPv6 Addresses | ipaddress stdlib validation | 2001:db8::1 |

---

## Architecture

```
DOCX Input
    │
    ▼
┌─────────────────────────────┐
│  Parser (parser.py)         │  Extract paragraphs + table runs
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Detector Layer             │  10 parallel detectors per run
│  (detectors/*.py)           │  → list[Detection]
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Overlap Resolution         │  Longest match wins
│  (replacement.py)           │  → non-overlapping detections
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Replacement Engine         │  EntityRegistry tracks real→fake
│  (replacer.py)              │  Deterministic: same input = same output
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Document Mutation          │  Run-level edits preserve formatting
│  (apply_edits)              │  Sole mutation point
└─────────────┬───────────────┘
              │
              ▼
        DOCX Output
```

### Key Design Principles

- **Single source of truth**: EntityRegistry ensures one real value maps to one fake value
- **Deterministic output**: Same input always produces the same redacted output
- **Formatting preservation**: Edits operate on runs, preserving bold/italic/font styling
- **Explicit stage boundaries**: Detection, planning, and mutation are strictly separated
- **Validate before output**: All replacements pass through overlap resolution

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Redact a document
python -m pii_redactor input.docx output.docx

# Run the web demo
uvicorn app:app --reload
# Open http://localhost:8000
```

---

## Evaluation

Validated against 10 synthetic documents and 10 blind validation documents covering resumes, bank statements, legal agreements, invoices, meeting minutes, employment contracts, medical reports, vendor agreements, tax notices, and partnership deeds.

### Results

| Metric | Synthetic (5 docs) | Blind (5 docs) |
|--------|-------------------|----------------|
| **Macro Precision** | 0.76 | 0.87 |
| **Macro Recall** | 0.87 | 0.87 |
| **Macro F1** | **0.79** | **0.83** |

### Per-Detector F1 Scores (Blind)

| Detector | F1 | Notes |
|----------|-----|-------|
| Email | 1.00 | Perfect detection |
| Date | 1.00 | Perfect detection |
| Company | 0.92 | Strong NER + suffix heuristics |
| Phone | 0.80 | All prefixed formats detected |
| Person | 0.73 | Limited by spaCy NER ambiguity |
| Address | 0.55 | Limited by cross-paragraph formatting |

### Test Suite

- **162 tests passing** across unit tests, corpus tests, and stress tests
- Corpus tests validate detection against known valid/invalid/edge-case inputs
- Stress tests validate adversarial inputs, determinism, and offset correctness

---

## Project Structure

```
.
├── app.py                   # FastAPI web demo
├── requirements.txt         # Dependencies
├── README.md                # This file
├── FAILURE_LOG.md           # Issues found, fixed, and known limitations
├── sample_input.docx        # Example input document
├── sample_output.docx       # Example redacted output
└── pii_redactor/            # Main package
    ├── __main__.py          # CLI entry point
    ├── main.py              # Pipeline: process_run, redact_document
    ├── parser.py            # DOCX I/O (load, save, extract runs)
    ├── replacement.py       # Overlap resolution, ReplacementPlan, apply_edits
    ├── replacer.py          # EntityRegistry, fake data generation
    ├── detectors/
    │   ├── detection.py     # Detection NamedTuple
    │   ├── email.py         # Email detector
    │   ├── phone.py         # Phone detector (7 Indian formats)
    │   ├── person.py        # Person detector (spaCy NER + heuristics)
    │   ├── company.py       # Company detector (spaCy NER + suffixes)
    │   ├── address.py       # Address detector (structured extraction)
    │   ├── date.py          # Date detector (12 strptime formats)
    │   ├── credit_card.py   # Credit card detector (Luhn + brand)
    │   ├── national_id.py   # National ID detector (SSN formats)
    │   ├── ipv4.py          # IPv4 detector (ipaddress stdlib)
    │   └── ipv6.py          # IPv6 detector (ipaddress stdlib)
    └── tests/
        ├── test_corpus.py   # Corpus-based detection tests
        ├── test_stress.py   # Adversarial/edge-case tests
        ├── test_evaluation.py  # P/R/F1 evaluation framework
        ├── test_roundtrip.py   # Format preservation tests
        ├── test_*.py        # Per-detector unit tests
        ├── samples/         # 10 PII corpus files
        └── documents/       # Synthetic + blind test documents
```

---

## Known Limitations

1. **NER ambiguity**: spaCy NER misclassifies some proper nouns (programming languages, abbreviations, geographic names) as person names. This is a statistical model limitation, not an implementation defect.

2. **Cross-paragraph addresses**: Addresses spanning multiple paragraphs with complex formatting may not be fully detected. The structured extraction relies on postal codes as anchor points.

3. **Phone sub-span overlap**: The phone detector generates both `+91 98765 43210` and `98765 43210` as separate detections. The pipeline's overlap resolution correctly eliminates the shorter match, but raw detector output includes both.

4. **Isolated names**: spaCy NER requires document context. Names in sparse documents may be missed.

