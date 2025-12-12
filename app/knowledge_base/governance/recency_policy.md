---
title: Recency Policy  
doc_type: governance  
as_of: 2025-11-01  
refresh_cadence: yearly  
tags: [governance, recency, data-quality, uncertainty]
analysis_hint: Apply these rules whenever timestamps, freshness, or data age may affect interpretation.
version: 1.0  
---

# Recency Policy

Defines how to handle **stale, missing, or time-sensitive data**. 
Ensures outputs do not imply real-time access, avoid hallucinated values, 
and communicate uncertainty clearly.

---

# 1. Core Principles

- The model **does not** have real-time market access.  
- Always rely on **available internal data**, not assumed fresh values.  
- When data is older than its freshness threshold, **add a recency disclaimer**.  
- Never infer specific numeric values when the latest observation is unknown.  
- Prefer qualitative trends to synthetic precision.

---

# 2. Freshness Thresholds by Data Type

## High-Frequency Market Data
**Examples:** equities, FX, yields, commodities  
**Freshness threshold:** *1 business day*  
**If older:**  
- Use: “as of the latest available close”  
- Avoid: “currently trading,” “today,” “now”

---

## Macro Data
**Examples:** CPI, payrolls, GDP, PMIs  
**Freshness threshold:** *30 days after release*  
**If older:**  
- Use: “last published CPI reading…”  
- Avoid: “inflation is currently…”

---

## Sector Baselines / Quarterly Data
**Examples:** valuations, earnings revisions, factor metrics  
**Freshness threshold:** *1 quarter (~90 days)*  
**If older:**  
- Use: “as of the last quarterly baseline (YYYYQX)”  
- Avoid: implying up-to-date valuation levels

---

## Semistatic Datasets
**Examples:** sector constituents, holiday calendars  
**Freshness threshold:** *valid for the version period*  
**If older:**  
- Use: “based on the 2025Q4 constituent set”  
- Never imply dynamic/intraday updates

---

# 3. Behavior When Data Is Stale

When a dataset exceeds its freshness threshold:

### Required:
- Add explicit recency language:
  - “As of the latest available data…”
  - “As of the prior close…”
  - “According to the most recent release…”

### Allowed:
- Qualitative interpretations  
- Regime reasoning  
- Cross-sectional insights not reliant on exact timestamps  

### Not Allowed:
- Numeric guesses  
- Statements implying real-time access  
- “Current levels,” “today’s move,” etc.

---

# 4. Behavior When Data Is Missing

If no timestamp exists:

### Required:
- Acknowledge uncertainty:
  - “Data is not available for the latest period…”  
  - “We do not have the most recent print…”  

### Allowed:
- Historical analogs  
- Framework-based explanations  

### Not Allowed:
- Reconstructed values  
- Synthetic prints  
- Implied precision

---

# 5. Conflicting or Ambiguous Timestamps

If timestamps differ across sources:

### Required:
- Default to **conservative** interpretation  
- Use: “Timestamp unclear; using last verifiable observation.”

### Allowed:
- Directional insights (“higher/lower than last known")  

### Not Allowed:
- Forced reconciliation  
- Claiming certainty where none exists

---

# 6. Forward-Looking or “Today” Requests

When users ask for current or future values:

### Allowed:
- Describe drivers, sensitivities  
- Offer historical behavior  

### Required:
- Clarify limits:
  - “I do not have access to real-time prices or future prints.”

### Not Allowed:
- Live quotes  
- Implied intraday movements  
- Exact forecasts unless explicitly requested

---

# 7. Language Rules

### Approved phrasing:
- “As of the latest available data…”  
- “As of the last release…”  
- “According to the most recently published figures…”  
- “Historically, in similar regimes…”  
- “Based on the latest internal dataset…”

### Forbidden phrasing:
- “Currently trading at…”  
- “Real-time data shows…”  
- “Today’s move is…”  
- Vendor references: “Bloomberg shows…”

---

# 8. Implicit Decision Flow

1. **Is there a timestamp?**  
   - No → state uncertainty + fallback to patterns  
2. **Fresh enough?**  
   - Yes → normal usage  
   - No → add disclaimer  
3. **Missing values?**  
   - Yes → no numbers; qualitative patterns  
4. **Conflicting timestamps?**  
   - Yes → conservative path + note ambiguity  

