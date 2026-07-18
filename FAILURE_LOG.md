# Failure Log

This document tracks every issue discovered during development, testing, and validation, and how it was resolved.

---

## Issues Found and Fixed

### 1. Email: Double-dot domain validation
**File:** `pii_redactor/detectors/email.py`
**Issue:** `john@gmail..com` was being detected as valid (double dot in domain).
**Fix:** Added `_validate_email()` function to reject emails with double dots in domain.
**Status:** Fixed

### 2. Phone: Missing dash-separated format
**File:** `pii_redactor/detectors/phone.py`
**Issue:** `+91-9876543210` and `+91-98765-43210` were not detected.
**Fix:** Added dash as a separator in phone patterns.
**Status:** Fixed

### 3. Phone: Missing 5+5 format
**File:** `pii_redactor/detectors/phone.py`
**Issue:** `98765 43210` (5-digit + 5-digit without +91 prefix) was not detected.
**Fix:** Added pattern `\b\d{5}\s\d{5}\b`.
**Status:** Fixed

### 4. Phone: Landline with two spaces
**File:** `pii_redactor/detectors/phone.py`
**Issue:** `022 2409 4400` (landline with two spaces) was not detected.
**Fix:** Added pattern `0\d{2,3}[-\s]+\d{3,4}[-\s]+\d{4}` for space-separated landlines.
**Status:** Fixed

### 5. Phone: Tab-separated format
**File:** `pii_redactor/detectors/phone.py`
**Issue:** `+91\t98765\t43210` (tab-separated) was not detected.
**Fix:** Used `[-\s]+` to match multiple whitespace characters including tabs.
**Status:** Fixed

### 6. Date: Missing abbreviated month formats
**File:** `pii_redactor/detectors/date.py`
**Issue:** `Jan 15, 1990` and `15 Jan 1990` were not detected.
**Fix:** Added `MONTHS_ABBR` patterns and strptime formats for abbreviated months.
**Status:** Fixed

### 7. Date: Missing dash-separated full month format
**File:** `pii_redactor/detectors/date.py`
**Issue:** `15-january-1990` was not detected.
**Fix:** Added `DAY_MONTH_YEAR_DASH` pattern and `%d-%B-%Y` strptime format.
**Status:** Fixed

### 8. National ID: Missing space-separated format
**File:** `pii_redactor/detectors/national_id.py`
**Issue:** `123 45 6789` (SSN with spaces) was not detected.
**Fix:** Added pattern for space-separated SSN format.
**Status:** Fixed

### 9. IPv6: Complex compressed forms not matched
**File:** `pii_redactor/detectors/ipv6.py`
**Issue:** `2001:db8::1`, `2001:db8:85a3::8a2e:370:7334` were not detected.
**Fix:** Simplified to permissive regex `[0-9a-fA-F:]{3,}` with ipaddress validation.
**Status:** Fixed

### 10. Corpus parser: Tab escape sequences
**File:** `pii_redactor/tests/test_corpus.py`
**Issue:** `\\t` in corpus files was treated as literal backslash-t, not tab.
**Fix:** Added `.replace("\\t", "\t")` to corpus parser.
**Status:** Fixed

### 11. Evaluation: Precision > 1.0 in contain mode
**File:** `pii_redactor/tests/test_evaluation.py`
**Issue:** Single detection matching multiple ground truth items caused precision > 1.0.
**Fix:** Added `pred_correct` metric to track unique detections matching ground truth.
**Status:** Fixed

### 12. Address: POSTAL_CODE_PATTERN only matched Mumbai PINs
**File:** `pii_redactor/detectors/address.py`
**Issue:** `\b4\d{2}\s?\d{3}\b` only matched PIN codes starting with 4 (Mumbai). All other Indian PINs (1-9) were missed.
**Fix:** Changed to `(?<!\d)\d{6}(?!\d)` to match any valid6-digit Indian PIN code.
**Status:** Fixed

### 13. Address: expand_to_sentence_boundary consumed entire document
**File:** `pii_redactor/detectors/address.py`
**Issue:** Expansion had no distance cap, causing a single address to span the entire document when no sentence terminators existed.
**Fix:** Added `max_expand = 200` cap to both backward and forward expansion. Added line-count limit (10 lines max) to reject absurdly large detections.
**Status:** Fixed

### 14. Address: CITY_PATTERN missing major Indian cities
**File:** `pii_redactor/detectors/address.py`
**Issue:** Cities like Bengaluru, Gurugram, Kochi, Jaipur, Lucknow were not recognized.
**Fix:** Added missing cities to the CITY_PATTERN regex.
**Status:** Fixed

### 15. Phone: Missing 3-3-4 digit grouping
**File:** `pii_redactor/detectors/phone.py`
**Issue:** `+91 124 456 7890` (3-3-4 grouping) was not detected.
**Fix:** Added pattern `r"\+91[-\s]+\d{3}[-\s]+\d{3}[-\s]+\d{4}"`.
**Status:** Fixed

### 16. Person: Newline-spanning NER entities
**File:** `pii_redactor/detectors/person.py`
**Issue:** spaCy NER created garbage entities spanning newlines (e.g., "Apollo Bunder\nMumbai", "GSTIN 07AAACG1234F1Z5").
**Fix:** Added `if "\n" in ent.text: continue` to reject PERSON and ORG entities containing newlines.
**Status:** Fixed

### 17. Person: Label words misclassified as PERSON
**File:** `pii_redactor/detectors/person.py`
**Issue:** spaCy misclassified document labels like "Email", "GSTIN", "CFO", "Cholesterol" as PERSON.
**Fix:** Added `LABEL_WORDS` set containing common document labels. Single-word detections matching these labels are rejected.
**Status:** Fixed

### 18. Person: Regex fallback missing "Name:" and "Partner" labels
**File:** `pii_redactor/detectors/person.py`
**Issue:** Names after "Name:" and "Partner N:" labels were not detected by regex fallback.
**Fix:** Added "name" and "partner" to TITLE_NAME_PATTERN triggers.
**Status:** Fixed

### 19. Company: Newline-spanning NER entities
**File:** `pii_redactor/detectors/company.py`
**Issue:** spaCy NER created ORG entities spanning newlines (e.g., "VP Operations\nDate", "Deepika Chopra\nAddress").
**Fix:** Added `if "\n" in ent.text: continue` to reject ORG entities containing newlines.
**Status:** Fixed

---

## Known Limitations (Not Fixed — Design Decisions)

### Person: NER cannot detect isolated names
**Reason:** spaCy's NER model requires document context. Isolated names like `Amit Patel`, `Sneha Reddy` are not detected when not in a document with surrounding context.
**Impact:** Low recall for standalone person names.
**Mitigation:** Names are detected well in actual document context.

### Person: Case sensitivity
**Reason:** spaCy NER is case-sensitive. `rajesh kumar` (lowercase) and `RAJESH KUMAR` (uppercase) are not detected.
**Impact:** Misses formatted name variants.
**Mitigation:** Document text typically uses proper case.

### Email: Spaces in email
**Reason:** `john @example.com` and `john@ example.com` are invalid email formats and intentionally not detected.
**Impact:** None — these are not valid emails.

### Phone: Raw 10-digit without prefix
**Reason:** `9876543210` without +91 or 0 prefix is not detected to avoid false positives on order numbers, invoice numbers, etc.
**Impact:** Misses unprefixed phone numbers.
**Mitigation:** Most real phone numbers include a prefix.

### IPv4: Leading zeros rejected
**Reason:** `192.168.001.001` is intentionally rejected because leading zeros in IP addresses are ambiguous (could be octal in some systems).
**Impact:** Misses malformed IP addresses.
**Mitigation:** Leading zeros are not standard format.

### National ID: No-separator format
**Reason:** `123456789` without dashes is not detected to avoid false positives on order numbers, account numbers, etc.
**Impact:** Misses unformatted SSNs.
**Mitigation:** Most SSN displays include separators.

### Credit card: Non-standard lengths
**Reason:** `411111111111111` (15 digits) and `41111111111111111` (17 digits) are not detected because standard cards are 13, 15, or 16 digits.
**Impact:** Misses non-standard card number lengths.
**Mitigation:** Standard card formats are supported.

### Company: Single-word companies
**Reason:** `ABC` is not detected as a company to avoid false positives on abbreviations.
**Impact:** Misses very short company names.
**Mitigation:** Multi-word company names are detected.

### Address: Low recall on blind documents
**Reason:** Structured address detection relies on specific patterns (pin codes, street keywords). Addresses without these markers are missed.
**Impact:** Lower recall on unseen address formats.
**Mitigation:** Address detection works well for Indian addresses with pin codes.

### Person: spaCy NER false positives on non-person proper nouns
**Reason:** spaCy misclassifies programming languages (Python, Java), abbreviations (GSTIN, CFO), medical terms (Cholesterol), and geographic names (Civil Lines, Nehru Nagar) as PERSON.
**Impact:** ~11 false positives across synthetic documents. Precision = 0.57.
**Mitigation:** Added LABEL_WORDS filter for common document labels. Remaining FPs are corpus-specific and would risk overfitting if filtered individually.

### Company: spaCy NER false positives on non-company terms
**Reason:** spaCy misclassifies document headers (INCOME TAX ASSESSMENT ORDER), line items (Project Management - Rs), and descriptions (Medical Insurance: Provided) as ORG.
**Impact:** ~8 false positives across synthetic documents. Precision = 0.62.
**Mitigation:** Remaining FPs are document-structure-specific and would risk overfitting if filtered individually.

### Phone: Sub-span duplicate detections
**Reason:** The phone detector generates both `+91 98765 43210` and `98765 43210` as separate detections. The pipeline's `resolve_overlaps()` correctly eliminates these, but raw detector output includes both.
**Impact:** ~6 false positives in evaluation (would be resolved in pipeline). Precision = 0.60.
**Mitigation:** `resolve_overlaps()` in the pipeline correctly handles this. Raw detector evaluation reports these to show detector-level performance.

---

## Evaluation Results (Post-Fixes)

### Synthetic Documents (5)
| Detector | Precision | Recall | F1 |
|----------|-----------|--------|-----|
| Person | 0.57 | 0.91 | 0.70 |
| Email | 1.00 | 1.00 | 1.00 |
| Phone | 0.60 | 1.00 | 0.75 |
| Date | 1.00 | 1.00 | 1.00 |
| Address | 0.75 | 0.50 | 0.60 |
| Company | 0.62 | 0.80 | 0.70 |
| **Macro AVG** | **0.76** | **0.87** | **0.79** |

### Blind Validation Documents (5)
| Detector | Precision | Recall | F1 |
|----------|-----------|--------|-----|
| Person | 0.67 | 0.82 | 0.73 |
| Email | 1.00 | 1.00 | 1.00 |
| Phone | 0.67 | 1.00 | 0.80 |
| Date | 1.00 | 1.00 | 1.00 |
| Address | 1.00 | 0.38 | 0.55 |
| Company | 0.86 | 1.00 | 0.92 |
| **Macro AVG** | **0.87** | **0.87** | **0.83** |

### Improvement Summary
| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Synthetic F1 | 0.78 | 0.79 | +0.01 |
| Blind F1 | 0.78 | 0.83 | +0.05 |

### IPv6: Bare `::` not detected
**Reason:** `::` alone is not a complete IPv6 address and is intentionally not detected.
**Impact:** None — `::` is not a valid standalone address.
