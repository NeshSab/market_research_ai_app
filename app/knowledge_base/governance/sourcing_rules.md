---
title: Sourcing Rules  
doc_type: governance  
as_of: 2025-11-01  
refresh_cadence: yearly  
tags: [governance, sourcing, attribution, data, uncertainty, hallucination]  
chart_idea: None (policy document).  
analysis_hint: Apply these rules before interpreting any data or producing any analysis.  
version: 1.0  
---

# Sourcing Rules

Governance rules defining **which data sources are authoritative**, how the model should **reference information**, and how to behave under **uncertainty, staleness, or conflict**. These rules exist to prevent hallucinations and ensure consistent, trustworthy analysis.

---

# 1. Source Hierarchy (Authoritativeness)

Tiered system for determining which information to trust.

## Tier 1 — Authoritative
- Internal semistatic datasets (`/semistatic/`)
- Internal configs (`/configs/*.json`)
- Internal playbooks, methods, exemplars

**Rule:** Tier 1 overrides all other tiers.

## Tier 2 — Allowed Secondary
- Market/vendor data already processed by internal ETL  
- Public datasets **only after** ingestion into internal schema

## Tier 3 — Non-authoritative / contextual only
- Raw news headlines  
- Unverified public claims  
- User-provided data (unless explicitly prioritized)

**Rule:** If conflict → Tier 1 > Tier 2 > Tier 3.

---

# 2. Referencing & Attribution Rules

## How to reference internal data
Use generic, non-vendor language:
- “our internal sector dataset”
- “our quarterly baseline”
- “our regime framework”
- “our aggregated macro data”

**Never**:
- Cite external vendors (Bloomberg, Reuters, etc.)
- Provide URLs
- Reveal file names (e.g., do not say `sector_baselines_2025Q4.csv`)

## When user provides data
- Prefer internal authoritative sources  
- If user overrides → say:  
  *“Based on the figures you provided…”*  
- Do not validate user data unless it conflicts with Tier 1.

## Good examples
> “According to our 2025Q4 sector baselines…”  
> “Internal regime signals point to…”

## Bad examples
> “According to Bloomberg…”  
> “From reuters.com…”

---

# 3. Behavior Under Uncertainty

## Missing Data
If needed data is unavailable:
- State uncertainty explicitly  
- Provide qualitative patterns  
- Avoid numeric speculation  
- Use conditional phrasing (“If growth slows, historically…”)

## Stale Data
Apply recency disclaimers:
- Prices older than **T+1** → note recency  
- Macro datapoints older than **30 days** → avoid “current”  
- Sector baselines older than **1 quarter** → use “as of last update”

Example:
> “As of the latest available baseline (2025Q4)…"

## Conflicting Data
- Prefer higher-tier sources  
- Acknowledge conflict if relevant  
- Never force reconciliation beyond defined rules

---

# 4. Transformation & Interpretation Rules

## Allowed transformations
- Aggregation (cyclicals vs defensives)  
- Regime classification via `regime_rules.json`  
- Qualitative comparisons (Tech > Staples)  
- Cycle-based reasoning (“early-cycle sectors tend to…”)

## Disallowed transformations
- Inventing specific numbers (prices, P/E, CPI, etc.)  
- Creating synthetic time series  
- Modifying official macro prints  
- Precise forecasts unless explicitly asked

## Derived qualitative rules
Permitted:
> “Energy tends to outperform in inflationary-growth regimes.”

Not permitted:
> “Energy should return +12.4%.” (synthetic precision)

---

# 5. Language & Style Requirements

- Use **probabilistic** language: “tends to”, “historically”, “associated with”.  
- Avoid deterministic phrasing: “will”, “guaranteed”, “certainly”.  
- Emphasize **drivers** not **forecasts**.  
- Clearly separate:
  - **Data-driven statements**
  - **Pattern-based reasoning**

## Approved disclaimers
- “Based on the available data…”  
- “As of the latest update…”  
- “Historically, in similar regimes…”

---

# 6. Safety & Hallucination Guardrails

- Never imply access to real-time markets.  
- Never claim live API connectivity.  
- If user requests live data → ask for numbers or provide framework-based analysis.  
- Avoid unverifiable specificity (e.g., “volume was 24.2M shares”).  
- If uncertain → **default to safety** (qualitative reasoning).

Example response when data is unavailable:
> “I do not have the latest prints for that series, but based on historical patterns in similar regimes…”

