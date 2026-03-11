# Phase 1 Research Summary — Systematic Literature Collection

**Date completed:** 2026-03-07
**Domains:** 54/54 complete
**Total papers (raw):** 534
**Total papers (deduplicated by DOI):** 481
**Duplicates removed:** 53

---

## Papers by Study Type

| Study Type | Count | % |
|-----------|------:|--:|
| Review (narrative) | 130 | 27.0% |
| Meta-analysis | 88 | 18.3% |
| Cross-sectional | 69 | 14.3% |
| Systematic review | 65 | 13.5% |
| RCT | 61 | 12.7% |
| Cohort | 48 | 10.0% |
| Consensus | 8 | 1.7% |
| Expert consensus | 7 | 1.5% |
| Position statement | 3 | 0.6% |
| Case series | 2 | 0.4% |

**Evidence quality:** 153 papers (31.8%) are meta-analyses or systematic reviews — the highest tiers of evidence. Another 61 (12.7%) are RCTs. Over 44% of the collection is Level 1-2 evidence.

---

## Papers by Population

| Population | Count |
|-----------|------:|
| Mixed | 124 |
| Recreational | 123 |
| General | 92 |
| Elite | 74 |
| Endurance Athletes | 13 |
| Athletes | 13 |
| Recreational Runners | 11 |
| Female Athletes | 9 |
| Elite Runners | 8 |
| Masters Athletes | 7 |
| Male Athletes | 7 |
| Youth Athletes | 6 |
| Female General | 5 |
| Masters Runners | 5 |
| Physically Active | 5 |

**Running-specific populations** (recreational runners, elite runners, recreational, masters runners, novice runners, competitive runners, beginner runners, marathon runners) dominate. General/mixed populations appear where running-specific evidence is limited (e.g., tendon health, concurrent training).

---

## Papers by Sport

| Sport | Count | % |
|------|------:|--:|
| Running | 265 | 55.1% |
| General Endurance | 105 | 21.8% |
| Mixed | 95 | 19.8% |
| Cycling | 36 | 7.5% |
| Endurance | 27 | 5.6% |
| Mixed Endurance | 9 | 1.9% |
| Mixed Sports | 7 | 1.5% |
| Mixed Youth Sport | 7 | 1.5% |
| Triathlon | 6 | 1.2% |
| Swimming | 6 | 1.2% |
| Team Sport | 4 | 0.8% |
| Team Sports | 2 | 0.4% |
| Rowing | 2 | 0.4% |
| General | 1 | 0.2% |
| Military | 1 | 0.2% |

**Running-specific:** 265 papers (55.1%) study running populations directly.

---

## Domains with Strongest Coverage

| Domain | Papers |
|--------|-------:|
| Half Marathon & 10K Training | 14 |
| Supplements — Evidence Base | 14 |
| Masters & Senior Runners (40+) | 13 |
| Tendon Health & Loading | 13 |
| Warm-Up & Cool-Down | 13 |
| Female-Specific Physiology | 12 |
| Foot — Plantar Fasciitis & Other | 12 |
| Interval Training Science | 12 |
| Iron, Bone Health & Micronutrients | 12 |
| Marathon-Specific Training | 12 |
| Training Load & ACWR | 12 |
| Training Zone Systems — Comparison & Validity | 12 |

---

## Domains with Thinnest Coverage

| Domain | Papers |
|--------|-------:|
| 5K & Track Training | 8 |
| Altitude Training | 8 |
| Beginner Running & Couch to 5K | 8 |
| Body Composition & Running Performance | 8 |
| Cross-Training & Transfer | 8 |
| Detraining & Fitness Retention | 8 |
| Easy & Recovery Running | 8 |
| Foam Rolling, Stretching & Mobility | 8 |
| Heart Rate Training & Zones | 8 |
| Heat, Cold & Environmental Performance | 8 |
| HRV Monitoring | 8 |
| Hydration & Sodium | 8 |
| Knee Injuries — PFPS & ITB | 8 |
| Lower Leg — Achilles, Shin Splints, Calf | 8 |
| Bone Stress Injuries & Stress Fractures | 8 |
| Pacing Strategy | 8 |
| Protein for Endurance Runners | 8 |
| Race Prediction Models | 8 |
| Return to Running After Injury | 8 |

---

## Unverified DOIs (11 papers)

These papers have `doi: null` — they are older foundational works or papers where DOIs could not be confirmed. They should be verified manually in Phase 2.

| Paper ID | Domain |
|----------|--------|
| `knechtle_2014_anthropometric_endurance` | body_composition |
| `hickson_1981_reduced_frequency` | detraining |
| `cheatham_2015_smr_systematic` | foam_rolling_mobility |
| `moir_2019_marathon_genes_sr` | genetics_individual_response |
| `gomez_molina_2017_hm_predictive_variables` | half_marathon_training |
| `holloszy_1967_mitochondrial_exercise` | long_run_physiology |
| `issurin_2008_block_vs_traditional` | periodisation |
| `riegel_1981_athletic_records_endurance` | race_prediction |
| `conley_1980_running_economy_performance` | running_economy |
| `sun_2020_footwear_constructions` | shoe_technology |
| `saltin_1992_cardiovascular_limitation` | vo2max_development |

---

## Output Files

| File | Description |
|------|-------------|
| `manifest.json` | Domain tracker — all 54 domains marked complete |
| `domains/{domain_id}.json` | One file per domain with full paper records |
| `all_papers.json` | Flat array of 481 unique papers, deduplicated by DOI |
| `log.txt` | One-line entry per domain completion |
| `SUMMARY.md` | This file |

---

## Phase 2 Recommendations

1. **Verify the 11 null-DOI papers** — these are mostly foundational pre-DOI-era works. Confirm via PubMed or library catalog.
2. **Consider adding domains** if gaps emerge during claim extraction: gut health/GI issues in runners, running form cues/coaching, trail vs road differences, treadmill vs outdoor equivalence.
3. **Begin claim extraction** — Phase 2 should systematically extract testable claims from meta-analyses and SRs first (153 papers), then RCTs (61 papers), then fill in with other study types.
