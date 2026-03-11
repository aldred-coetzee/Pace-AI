# Pace-AI Research Phase 1 — Systematic Literature Collection

## Your Mission

Build a verified bibliography of running science literature. This is **data collection only**.

**YOU ARE NOT:**
- Extracting claims from papers
- Writing coaching implications
- Deciding what findings mean
- Summarising methodology

**YOU ARE:**
- Verifying that papers exist (DOI resolves)
- Capturing accurate metadata
- Noting what population each paper studied
- Flagging quality indicators (journal tier, citation count if visible, study type)
- Moving systematically through every domain until complete

Do not stop until all 52 domains in `manifest.json` have status `"complete"`.

---

## Working Directory

All files live in `research/`:
- `manifest.json` — domain tracker, update after every domain
- `domains/{domain_id}.json` — one file per domain with all papers found
- `log.txt` — append a one-line entry every time you complete a domain

---

## The Loop — Execute This Exactly

```
WHILE any domain has status != "complete":
  1. Read manifest.json
  2. Find the first domain with status "pending"
  3. Set its status to "in_progress", save manifest.json
  4. Run the search protocol for that domain (see below)
  5. Save results to domains/{domain_id}.json
  6. Update manifest.json: status="complete", papers_found=N
  7. Append to log.txt: "{timestamp} | {domain_id} | {N} papers found"
  8. Continue to next domain
```

**Never skip a domain. Never stop early. If a search returns few results, try alternative search terms before moving on.**

---

## Search Protocol for Each Domain

For each domain, do ALL of the following:

### Step 1 — Primary Searches
Run web searches using the `search_terms` in the manifest. Try at least 3 of the listed terms. For each, collect papers from:
- PubMed (pubmed.ncbi.nlm.nih.gov)
- Google Scholar
- SportDiscus references in other papers
- Reference lists of review papers (backward citation)

### Step 2 — Anchor Paper Expansion
Find 1-2 high-quality review papers or meta-analyses in the domain. Check their reference lists for additional papers to include.

### Step 3 — DOI Verification
For every paper:
- Confirm the DOI resolves (fetch the DOI URL or PubMed page)
- Confirm author names match
- Confirm journal and year match
- If DOI does not resolve → mark `doi_verified: false`, note the issue

### Step 4 — Record the Paper
Add to `domains/{domain_id}.json` using the schema below.

### Step 5 — Quality Check
Before marking the domain complete:
- Have you reached the `target_papers` count? If not, try more search terms.
- Do you have at least 1 systematic review or meta-analysis if one exists?
- Do you have papers covering different populations where relevant (elite, recreational, masters, youth)?
- Are papers from different decades where the field has evolved?

---

## Paper Record Schema

Each paper in `domains/{domain_id}.json` follows this exact structure:

```json
{
  "id": "author_year_keyword",
  "authors": ["Last FM", "Last FM"],
  "year": 2016,
  "title": "Full paper title",
  "journal": "Journal name",
  "volume": "43",
  "issue": "9",
  "pages": "773-781",
  "doi": "10.xxxx/xxxxx",
  "doi_verified": true,
  "pubmed_id": "12345678",
  "pmc_id": "PMC1234567",
  "study_type": "rct|meta_analysis|systematic_review|cohort|cross_sectional|case_series|review|book|consensus|practitioner",
  "population": ["elite", "recreational", "masters", "youth", "general", "mixed"],
  "sport": ["running", "cycling", "triathlon", "team_sport", "general_endurance", "mixed"],
  "n_subjects": 0,
  "abstract_available": true,
  "open_access": true,
  "notes": "One sentence: what this paper is specifically about. Nothing more."
}
```

**Rules:**
- `id` = first author surname + year + 1-2 word topic e.g. `"gabbett_2016_acwr"`
- `study_type` — pick exactly one from the list
- `population` — can be multiple
- `sport` — be honest: if it's a rugby study, say `team_sport`, not `running`
- `notes` — one sentence maximum. Describe what the study did, not what it found.
- Leave fields as `null` if unknown, not empty string

---

## Domain File Structure

`domains/{domain_id}.json`:

```json
{
  "domain_id": "interval_training",
  "domain_name": "Interval Training Science",
  "status": "complete",
  "papers_found": 11,
  "search_terms_used": ["interval training VO2max running", "high intensity interval training distance runners"],
  "search_terms_not_tried": ["repeated sprint endurance"],
  "coverage_notes": "Good coverage of VO2max-focused interval work. Limited studies on recreational runners specifically.",
  "papers": [
    { ...paper record... },
    { ...paper record... }
  ]
}
```

---

## Quality Priorities

Within each domain, prioritise in this order:

1. **Meta-analyses and systematic reviews** — highest priority
2. **RCTs** (randomised controlled trials)
3. **Prospective cohort studies**
4. **Cross-sectional studies with large N**
5. **Narrative reviews** from senior researchers
6. **Practitioner books/consensus statements** — include but flag clearly

Prefer:
- Running-specific populations over general endurance or team sports
- Recreational/trained runners over untrained controls (unless studying beginners)
- Papers from the last 15 years unless the older paper is foundational
- Higher-impact journals (BJSM, Med Sci Sports Exerc, Sports Medicine, Int J Sports Physiol Perform, J Appl Physiol)

---

## Domains Already Partially Covered

The following domains have some papers already in `references.md` in the main project. You still need to find additional papers to reach target counts — do not skip these domains.

- `training_load_acwr` — have: Gabbett 2016, Hulin 2014, Hulin 2016, Windt 2019, Impellizzeri 2020, Qin 2025
- `polarized_training` — have: Seiler 2006, Seiler 2010, Stöggl & Sperlich 2014
- `vo2max_development` — have: Bassett & Howley 2000, Joyner & Coyle 2008
- `running_economy` — have: Saunders 2004
- `lactate_threshold` — have: Faude 2009
- `taper_science` — have: Bosquet 2007, Smyth 2021
- `overtraining_recovery` — have: Meeusen 2013
- `detraining` — have: Mujika & Padilla 2000 (x2), Mujika & Padilla 2001, Iaia 2023
- `hrv_monitoring` — have: Plews 2013, Plews 2014
- `heat_cold_environment` — have: Ely 2007
- `red_s` — have: Mountjoy 2014, 2018, 2023
- `masters_running` — have: Rogers 1990, Zampieri 2022
- `youth_running` — have: Casado 2022, Varghese 2021, Coel 2022
- `strength_training_runners` — have: Blagrove 2018
- `altitude_training` — have: Levine & Stray-Gundersen 1997
- `injury_prevention_general` — have: van Gent 2007
- `periodisation` — have: Issurin 2010
- `sleep_recovery` — have: Halson 2014, Milewski 2014
- `nutrition_general` — have: Thomas 2016

---

## Error Handling

**If a DOI doesn't resolve:**
- Try fetching the PubMed page directly
- Try the journal website
- If still unverified: set `doi_verified: false` and `notes: "DOI unverified — paper may exist but could not confirm"`
- Include the paper anyway with the caveat

**If you can't reach target_papers for a domain:**
- Note in `coverage_notes` what's missing and why
- Mark complete anyway if you've exhausted reasonable search terms
- Minimum acceptable: 5 papers per domain

**If a search returns irrelevant results:**
- Try the next search term in the list
- Try PubMed directly with MeSH terms
- Note which terms were unproductive

---

## Progress Tracking

After every domain, update `manifest.json`:
- Set `status: "complete"`
- Set `papers_found: N`
- Set `last_updated: "2026-MM-DD"`

After every 10 domains, also write a `progress_snapshot.txt` with:
- Domains complete / total
- Total papers found so far
- Any domains where coverage was weak
- Any recurring DOI issues

---

## Final Output

When all 52 domains are complete:
1. Write `manifest.json` with all statuses `"complete"`
2. Write `SUMMARY.md` with:
   - Total papers found
   - Papers by study type (meta-analysis, RCT, review, etc.)
   - Papers by population (running-specific vs general endurance vs team sport)
   - Domains with strongest coverage
   - Domains where coverage is weakest (flag for human follow-up)
   - List of any unverified DOIs
3. Write `all_papers.json` — flat array of every paper across all domains, deduplicated by DOI

---

## Reminders

- This is Phase 1 only. Do not extract claims. Do not write "key content" summaries.
- The `notes` field is one sentence about what the study DID, not what it FOUND.
- Be honest about population: if it's a cycling study, say so. We need to know later.
- Verify DOIs. An unverified DOI is worse than no paper at all.
- Keep going. 100+ rounds of research. Do not stop until the manifest is complete.
