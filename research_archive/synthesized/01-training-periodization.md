
# Training Periodization Knowledge Base for AI Running Coach

## 1. Block vs. Linear Periodization

### 1.1 Definitions

**Linear (Traditional) Periodization** follows a progressive structure where training volume gradually decreases over time while intensity progressively increases, culminating in a taper before competition. This model was popularized by Soviet sport scientists (Matveyev) and remains the foundation of most recreational training plans.

**Block Periodization** (Issurin/Verkhoshansky model) concentrates training into specialized mesocycle blocks, each focusing on a narrow set of fitness qualities:

| Block | Focus | Typical Duration |
|-------|-------|-----------------|
| **Accumulation** | Aerobic capacity, muscular endurance, base volume | 2-6 weeks |
| **Transmutation** | Race-specific high-intensity work, anaerobic endurance | 2-4 weeks |
| **Realization** | Taper, speed, race-specific tactics, recovery | 1-3 weeks |

### 1.2 Evidence Comparison

The most comprehensive meta-analysis (Ronnestad et al., 2019, published in [Open Access Journal of Sports Medicine](https://pmc.ncbi.nlm.nih.gov/articles/PMC6802561/)) found:

- **Small favorable effect for block periodization** over traditional periodization for VO2max improvement (standardized mean difference = 0.40, 95% CI = 0.02-0.79)
- **Small favorable effect for Wmax** (power at VO2max): SMD = 0.28, 95% CI = 0.01-0.54
- Moderate to large effect sizes for endurance performance and workload at exercise thresholds
- **Caveat**: Studies were small with generally low methodological quality (mean PEDro score = 3.7/10)

### 1.3 Recommendations by Race Distance

| Distance | Recommended Model | Rationale |
|----------|------------------|-----------|
| **5K** | Block or Daniels 4-phase | Shorter accumulation needed; more time in transmutation (high-intensity). Speed residuals are short (~5 days), so frequent high-intensity exposure is critical. |
| **10K** | Block or Daniels 4-phase | Similar to 5K but with slightly longer accumulation. The aerobic contribution is ~90%, so base building matters more than for 5K. |
| **Half Marathon** | Linear or Reverse Linear | Heavily aerobic; reverse linear periodization (speed first, then build volume) may be most effective since race demands are primarily aerobic endurance. |
| **Marathon** | Reverse Linear Periodization | Volume peaks closest to race. Marathon uses virtually only aerobic energy pathways, so building aerobic volume closest to the race produces best results. |

### 1.4 Recommendations by Athlete Level

- **Elite/Advanced runners**: Block periodization shows promise for squeezing out additional gains since they are closer to genetic potential and struggle to develop multiple abilities simultaneously.
- **Recreational runners**: Linear or mixed-intensity approaches are sufficient and safer. Novice runners can develop multiple fitness factors simultaneously because they are far from their ceiling.

### 1.5 Training Residuals (Critical for Block Periodization)

Per Issurin's research, after stopping specific training for a quality, the residual effect persists for:

| Fitness Quality | Residual Duration | Implication |
|----------------|-------------------|-------------|
| **Maximal Speed** | 5 +/- 3 days | Must be refreshed frequently (strides, short sprints) |
| **Anaerobic Glycolytic Endurance** | 18 +/- 4 days | Can go 2-3 weeks without dedicated sessions |
| **Strength Endurance** | 15 +/- 5 days | Maintenance work needed every ~2 weeks |
| **Maximal Strength** | ~30 days | Longest muscular residual |
| **Aerobic Endurance** | 25-35 days | Longest overall residual; structural adaptations (mitochondria, capillary density) decay slowly |

**"Soon ripe, soon rotten" principle** (Zatsiorsky): Qualities developed over a longer period are retained longer. Neural adaptations (speed, power) decay fastest; structural adaptations (aerobic, hypertrophy) decay slowest.

Sources:
- [Block periodization of endurance training - systematic review and meta-analysis (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6802561/)
- [Running Periodization Part 3: Block and Undulating Periodization (Track & Field News)](https://trackandfieldnews.com/track-coach/running-periodization-part-3-block-and-undulating-periodization/)
- [A Fresh Look at Block Periodization (80/20 Endurance)](https://www.8020endurance.com/a-fresh-look-at-block-periodization/)
- [Implementing Block Periodization in Endurance Training (TrainingPeaks)](https://www.trainingpeaks.com/blog/implementing-block-periodization/)
- [Residual Training Effect (ExRx.net)](https://exrx.net/Sports/ResidualTraining)
- [Residual Training Effects: How Long Training Programs Last (Adam Loiacono)](https://adamloiacono.com/residual-training-effects-how-long-training-programs-last/)

---

## 2. ACWR (Acute:Chronic Workload Ratio)

### 2.1 Definition

The ACWR measures the ratio of recent training load ("acute" -- typically 1 week) to longer-term training load ("chronic" -- typically 4 weeks). It quantifies whether an athlete is training more or less than what their body has been prepared for.

### 2.2 Risk Thresholds

| ACWR Range | Risk Level | Action |
|-----------|------------|--------|
| **< 0.8** | Under-training / detraining risk | Athlete is doing significantly less than their body is prepared for. Fitness may be declining. Increase load gradually. |
| **0.8 - 1.3** | **Optimal "sweet spot"** / lowest injury risk | Training load is well-matched to the athlete's preparation. This is the target zone. |
| **1.3 - 1.5** | Moderate / caution zone | Load is elevated relative to preparation. Monitor closely, ensure recovery. |
| **1.5 - 2.0** | High risk | Significant spike in load. Injury probability is elevated. Reduce load. |
| **> 2.0** | Very high risk | 5-21x increased injury likelihood. Immediate load reduction required. |

### 2.3 Calculation Methods

#### Rolling Average (RA) Model

```
ACWR = Acute Load (1-week total) / Chronic Load (4-week average)
```

- Simple to compute
- Treats all workload in the window as equal
- Does not account for fitness decay
- "Coupled" version: the acute week is included in the chronic calculation
- "Uncoupled" version: the acute week is excluded from the chronic average (preferred -- avoids mathematical coupling artifact)

#### Exponentially Weighted Moving Average (EWMA) Model (Preferred)

```
EWMA_today = Load_today x lambda + (1 - lambda) x EWMA_yesterday

Where: lambda = 2 / (N + 1)
```

For acute load (7-day window): `lambda_acute = 2 / (7 + 1) = 0.25`
For chronic load (28-day window): `lambda_chronic = 2 / (28 + 1) = 0.069`

```
ACWR_EWMA = EWMA_acute / EWMA_chronic
```

**Why EWMA is superior**:
- Assigns greater weight to recent workload (more physiologically realistic)
- Accounts for the decaying nature of fitness/fatigue over time
- More sensitive for detecting increased injury risk (higher R-squared for injury prediction)
- Both models show significant associations between ACWR > 2.0 and injury, but EWMA explains more variance

### 2.4 What to Measure for Runners

For running-specific ACWR, track these metrics:

| Metric | Description | Notes |
|--------|-------------|-------|
| **Weekly Distance (km/miles)** | Total volume | Primary metric for most runners |
| **Duration (minutes)** | Total training time | Useful when pace varies greatly |
| **Session RPE x Duration** | Subjective load | Captures internal load; accounts for terrain, heat, fatigue |
| **Training Impulse (TRIMP)** | HR-weighted duration | More precise than distance alone; captures intensity |

### 2.5 Important Caveats

A 2024 study comparing methods in runners found significant disagreement between approaches: weekly training load flagged 33.4% of sessions as significant increases, coupled RA flagged 16.2%, uncoupled RA flagged 25.8%, and EWMA flagged 18.9%. The field still lacks definitive validation of which method best predicts running-related injuries specifically.

**Single-session spikes may matter more than weekly totals**: A 2025 study of 5,200+ runners (British Journal of Sports Medicine) found that increasing a single run by >10% compared to the longest run in the past 30 days raised overuse injury risk by 64%. Weekly ACWR was less predictive than single-session spikes.

Sources:
- [Acute:Chronic Workload Ratio (Science for Sport)](https://www.scienceforsport.com/acutechronic-workload-ratio/)
- [ACWR systematic review and meta-analysis (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12487117/)
- [EWMA provides more sensitive indicator of injury likelihood (PubMed)](https://pubmed.ncbi.nlm.nih.gov/28003238/)
- [Comparison of Weekly Training Load and ACWR Methods in Running (PubMed)](https://pubmed.ncbi.nlm.nih.gov/38291782/)
- [How much running is too much? 5200-person cohort study (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12421110/)
- [ACWR R Package (CRAN)](https://cran.r-project.org/web/packages/ACWR/ACWR.pdf)

---

## 3. Progressive Overload Rules for Runners

### 3.1 The 10% Rule: What It Says

The traditional guideline states: never increase weekly running mileage by more than 10% from one week to the next.

### 3.2 The 10% Rule: What the Evidence Actually Shows

**The rule lacks scientific support.** Key findings:

1. **Buist et al. (2008) RCT**: 532 novice runners were split into a 10% progression group and a more aggressive group. Injury rates were nearly identical -- 20.8% vs 20.3%. The 10% rule did not reduce injuries.

2. **Nielsen et al. (2014, JOSPT)**: Novice runners progressing at 24% per week over 8 weeks had no more injuries than those progressing at 10% over 12 weeks.

3. **Aarhus University Study (2012)**: Uninjured runners had an average weekly increase of 22.1% -- more than double the 10% rule.

4. **Systematic Review (2022, 36 articles, 23,047 runners)**: "No universal recommendations on training parameters or progressions can be issued... the popular '10% rule' for increasing weekly distance is not justified."

### 3.3 Why the 10% Rule Fails

- **Does not scale**: A 10% increase at 5 miles/week (0.5 miles) is trivially small; a 10% increase at 60 miles/week (6 miles) may be excessive.
- **Ignores individual variation**: Baseline fitness, running history, biomechanics, age, and load tolerance all matter.
- **Only measures external load**: Distance/duration alone ignores intensity, terrain, temperature, and internal stress.
- **Ignores session-level spikes**: A runner could stay within 10% weekly but have one massively long run that causes injury.

### 3.4 Modern Evidence-Based Load Progression Guidelines

| Principle | Guideline | Source/Rationale |
|-----------|----------|------------------|
| **ACWR Sweet Spot** | Keep ACWR between 0.8-1.3 | More nuanced than a flat percentage; accounts for chronic preparation |
| **Session Spike Control** | No single run should exceed the longest run in the past 30 days by more than 10% | 2025 BJSM cohort study (n=5,200) |
| **Absolute Mileage Matters** | Higher-mileage runners tolerate smaller percentage increases | At 50+ miles/week, even 5-8% increases may be appropriate limits |
| **Never Increase Volume AND Intensity Simultaneously** | In the same week, progress one or the other, not both | Fundamental periodization principle to manage total stress |
| **Step-Back Weeks** | Every 3rd or 4th week, reduce volume by 20-30% | Allows structural adaptation (tendons, bones need ~72 hours longer than muscles to adapt) |
| **Speed Work Cap** | Limit high-intensity work to 15-20% of weekly mileage | Consistent across Daniels, Seiler, and other coaching frameworks |
| **Build Base Before Intensity** | Establish consistent mileage before adding speed work | Strides and hill sprints are safe introductions to neuromuscular speed |

### 3.5 Volume vs. Intensity Periodization

The 80/20 (polarized) training model, first described by [Dr. Stephen Seiler](https://www.fasttalklabs.com/pathways/polarized-training/), provides the foundation:

- **~80% of training at low intensity** (below first lactate threshold / Zone 1): Easy conversational pace
- **~20% of training at high intensity** (above second lactate threshold / Zone 3): Intervals, tempo
- **Avoid the "grey zone"** (Zone 2 / moderate intensity): Too hard to recover from, not hard enough to drive optimal adaptation

Key research supporting this:
- Esteve-Lanao et al. (2007): Runners following 80/12/8 distribution improved 10K times by 4.2%, vs. 2.9% for 67/25/8 distribution
- Stoggl & Sperlich (2014): Polarized training had greater impact on endurance variables than threshold, high-intensity, or high-volume training alone
- A 2019 study: Over a 7-year horizon, volume of easy running had the highest correlation with performance

**Periodized intensity shift**: Move from pyramidal distribution (more threshold work) during base-building toward polarized distribution (more hard intervals, less threshold) during competition phase.

Sources:
- [The 10% Rule: New Study Suggests We've Been Doing It Wrong (Marathon Handbook)](https://marathonhandbook.com/the-10-rule-new-study-suggests-weve-been-doing-it-wrong-this-whole-time/)
- [Why the 10% Rule Fails (OnTracx)](https://www.ontracx.com/news/the-10-rule-why-it-fails-as-a-preventive-measure-for-running-related-injuries)
- [Excessive Progression and Running Injury Risk (JOSPT)](https://www.jospt.org/doi/10.2519/jospt.2014.5164)
- [The Myth of the 10 Percent Rule (Outside Online)](https://run.outsideonline.com/training/getting-started/myth-of-the-10-percent-rule/?scope=anon)
- [Reassessing the 10% Rule (Runners Connect)](https://runnersconnect.net/coach-corner/reassessing-the-10-percent-rule/)
- [The Association Between Running Injuries and Training Parameters (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9528699/)
- [80/20 Running: Foundation of Evidence-Based Endurance Training (Medium Running)](https://www.mediumrunning.com/medium-blog/blog-post-title-one-en72t-8h5r6-8h5r6)
- [Polarized Training for Marathon Runners (Marathon Ireland)](https://marathonireland.com/blog/polarized-training-8020/)
- [What Is Best Practice for Training Intensity Distribution (PubMed)](https://pubmed.ncbi.nlm.nih.gov/20861519/)

---

## 4. Mesocycle/Macrocycle Structure

### 4.1 Terminology

| Term | Duration | Description |
|------|----------|-------------|
| **Macrocycle** | 16-52 weeks | Entire training season toward a goal race |
| **Mesocycle** | 3-6 weeks | A block with a specific training focus |
| **Microcycle** | 7-14 days | Typically one week; the smallest repeating training unit |

### 4.2 Jack Daniels' 4-Phase Model (24 Weeks Total)

Jack Daniels' system divides training into four 6-week phases, each building on the previous:

| Phase | Name | Duration | Focus | Key Workouts |
|-------|------|----------|-------|-------------|
| **I** | Foundation & Injury Prevention (FI) | 6 weeks | Base building, aerobic development | Easy runs, strides, easy hills. Build to goal mileage. |
| **II** | Early Quality (EQ) | 6 weeks | Neuromuscular development, speed | R-pace (repetition) workouts (e.g., 400m repeats), T-pace cruise intervals, long runs |
| **III** | Transition Quality (TQ) | 6 weeks | VO2max, race-specific fitness | I-pace (interval) workouts (e.g., 1K repeats), longer threshold sessions, long runs |
| **IV** | Final Quality (FQ) | 6 weeks | Competition, sharpening, taper | Race-specific work, competitions, taper in final 1-3 weeks |

**Shorter prep cycles**: For 12 weeks, allocate 3 weeks per phase. For 16 weeks, allocate 4 weeks per phase.

### 4.3 Recommended Phase Durations by Race Distance

#### 5K Training (12-20 weeks total)

| Phase | Duration | Focus |
|-------|----------|-------|
| Base Building | 4-6 weeks | Easy running, strides, build mileage to target |
| Speed Development | 3-4 weeks | R-pace work, hill sprints, neuromuscular development |
| VO2max / Race-Specific | 3-6 weeks | I-pace intervals (1K repeats, 800m repeats), threshold runs |
| Sharpening + Taper | 2-3 weeks | Race-pace work, tune-up races, 7-day taper |

#### 10K Training (12-20 weeks total)

| Phase | Duration | Focus |
|-------|----------|-------|
| Base Building | 4-6 weeks | Aerobic foundation, mileage buildup |
| Speed Development | 3-4 weeks | R-pace and short intervals |
| Threshold / VO2max | 4-6 weeks | Tempo runs, cruise intervals, I-pace work |
| Sharpening + Taper | 2-3 weeks | Race-specific sessions, 10-day taper |

#### Half Marathon Training (12-16 weeks total)

| Phase | Duration | Focus |
|-------|----------|-------|
| Base Building | 4-6 weeks | Mileage buildup, long run progression |
| Strength / Speed | 3-4 weeks | Tempo runs, hill work, strides |
| Race-Specific | 4-6 weeks | Goal-pace long runs, extended tempo, progression runs |
| Taper | 10-14 days | Volume reduction 40-50%, maintain intensity |

#### Marathon Training (16-24 weeks total)

| Phase | Duration | Focus |
|-------|----------|-------|
| Base Building | 6-8 weeks | Mileage buildup to peak weekly volume target |
| Fundamental / Strength | 4-6 weeks | Long runs up to 18-20 miles, marathon-pace work, tempo runs |
| Sharpening / Peak | 4-6 weeks | Peak long runs (20-22 miles), specific marathon-pace sessions, highest mileage weeks |
| Taper | 2-3 weeks | Progressive volume reduction 40-60%, maintain some intensity |

### 4.4 Microcycle Structure (Weekly Template)

A typical 7-day microcycle for a runner doing 5-6 sessions per week:

| Day | Session Type | Intensity |
|-----|-------------|-----------|
| Monday | Rest or easy cross-training | Recovery |
| Tuesday | Quality session 1 (intervals/tempo) | High |
| Wednesday | Easy run | Low |
| Thursday | Quality session 2 (tempo/threshold) | Moderate-High |
| Friday | Easy run or rest | Low/Recovery |
| Saturday | Long run | Low-Moderate |
| Sunday | Easy run or rest | Low/Recovery |

**Hard-easy principle**: Always separate high-intensity sessions by at least 1-2 easy/rest days. 2-3 days of recovery between hard workouts is recommended.

### 4.5 Step-Back / Recovery Weeks

Every 3rd or 4th week within a mesocycle should be a "step-back" or recovery week:
- Reduce volume by 20-30% from the previous week
- Maintain some intensity (but reduced volume of speed work)
- Allows musculoskeletal adaptation (tendons and bones adapt slower than cardiovascular system)
- Pattern: Build-Build-Build-Recover or Build-Build-Recover

Sources:
- [Jack Daniels' Formulaic Approach to Periodisation (CoachRay)](https://www.coachray.nz/2021/10/11/jack-daniels-phd-formulaic-approach-to-periodisation/)
- [A Review of the 5k to 10k Training Plan in Jack Daniels Running Formula (RunningWithRock)](https://runningwithrock.com/review-jack-daniels-5k-10k-training-plan/)
- [How Long Should My Training Cycles Be? (TrainingPeaks)](https://www.trainingpeaks.com/blog/how-long-should-my-training-cycles-be/)
- [Macrocycles, Mesocycles, Microcycles Explained (TrainingPeaks)](https://www.trainingpeaks.com/blog/macrocycles-mesocycles-and-microcycles-understanding-the-3-cycles-of-periodization/)
- [Running Training Periodisation (Run161)](https://run161.com/running-training/running-training-periodisation-how-to-structure-your-training/)
- [Marathon Training Periodization: 52-Week Plans (RunnersConnect)](https://runnersconnect.net/marathon-periodization/)
- [Periodization: How COROS Uses Phases (COROS)](https://coros.com/stories/coros-coaches/c/periodization-how-coros-uses-phases-to-build-training-plans)
- [The Four Phases of Marathon Training (The Running Channel)](https://therunningchannel.com/the-four-phases-of-marathon-training/)

---

## 5. Taper Strategies

### 5.1 What Tapering Achieves

During a taper, the body undergoes critical physiological recovery:
- Muscle glycogen stores replenish to supranormal levels
- Enzyme activity, antioxidants, and hormones normalize
- Micro-damage in muscles, tendons, and connective tissue repairs
- Neuromuscular freshness improves
- Psychological readiness peaks

**Performance improvement from proper taper**: 2-3% on average (Bosquet et al. 2007 meta-analysis of 27 studies). For a 3-hour marathoner, that translates to 3-6 minutes. Some research suggests up to 5.6% improvement and 22% improvement in time-to-fatigue.

### 5.2 Taper Duration by Distance

| Race Distance | Taper Duration | Notes |
|--------------|----------------|-------|
| **5K** | 5-7 days | Minimal taper needed; keep sharp with strides |
| **10K** | 7-10 days | Slightly longer; one final interval session 4-6 days before race |
| **Half Marathon** | 10-14 days | Moderate taper; progressive volume reduction |
| **Marathon** | 14-21 days (2-3 weeks) | Longest taper; higher-volume runners (50+ miles/week) benefit from 3 weeks |

**Taper duration by weekly volume**:
- 50+ miles/week: 14-21 day taper
- 30-50 miles/week: 10-14 day taper
- Under 30 miles/week: 7-10 day taper

### 5.3 Volume Reduction Protocol

The three key principles: **reduce volume, maintain intensity, maintain frequency**.

#### The Numbers

| Taper Week | Volume (% of Peak Week) | Notes |
|------------|------------------------|-------|
| **Week 1 (3 weeks out)** | 70-80% of peak | Begin modest reduction |
| **Week 2 (2 weeks out)** | 55-65% of peak | Significant reduction; last quality workout |
| **Race Week** | 40-50% of peak | Easy running only; strides to stay sharp |

**Overall volume reduction**: Research consensus is 40-60% total reduction from peak volume, applied progressively (not as a sudden step-down).

#### Progressive (Exponential Decay) vs. Step Taper

Research favors **progressive/exponential decay tapering** over a sudden step-down:
- Reduce gradually, with larger cuts closer to race day
- One study found optimal approach: 50% reduction by day 3 of taper, 75% by day 6, then gradual reduction over final 8 days
- Exponential decay tapers outperformed step reductions, particularly when ~75% of remaining volume was quality running

### 5.4 Intensity During Taper

**Intensity should be maintained or only slightly reduced.** This is the most counterintuitive but most evidence-supported principle:

- Keep race-pace and faster sessions in the schedule, but with reduced volume (fewer reps, shorter sessions)
- Scientific studies consistently show that maintaining intensity is the most important factor in a successful taper
- Reducing intensity during taper leads to worse outcomes than maintaining it

### 5.5 Frequency During Taper

**Maintain training frequency.** Do not skip running days.

- A 2023 meta-analysis demonstrated that reducing frequency did not improve performance as much as reducing duration of individual runs
- If you normally run 5 days/week, continue running 5 days/week through race week
- Shorten individual runs rather than eliminating sessions

### 5.6 Specific Taper Protocols by Distance

#### 5K Taper (7 days)

| Days Before Race | Session |
|-----------------|---------|
| 7 | Normal easy run |
| 6 | Final interval workout: same intensity, 50-67% of normal reps |
| 5 | Easy run (short) |
| 4 | Easy run + 6-8 strides |
| 3 | Rest or very easy 15-20 minutes |
| 2 | Easy run + 4-6 strides |
| 1 | Rest or very easy 10-15 min shakeout |
| **Race Day** | Race |

#### 10K Taper (10 days)

| Days Before Race | Session |
|-----------------|---------|
| 10 | Normal easy run |
| 9 | Final quality workout: tempo or intervals at 60-67% normal volume |
| 8 | Easy run |
| 7 | Easy run + strides |
| 6 | Rest or easy cross-training |
| 5 | Easy run + 6-8 strides at race pace |
| 4 | Easy run (short) |
| 3 | Rest or very easy jog |
| 2 | Easy run + 4-6 strides |
| 1 | Rest or 10-15 min shakeout |
| **Race Day** | Race |

#### Half Marathon Taper (10-14 days)

| Week | Volume | Key Sessions |
|------|--------|-------------|
| Week before race (days 8-14) | 65-75% of peak | One moderate tempo run; one short interval session; reduced long run (60-70% of peak long run) |
| Race week (days 1-7) | 40-50% of peak | Easy runs only; 4-6 strides 2-3 days before race; rest day before or 10-min shakeout |

#### Marathon Taper (3 weeks)

| Week | Volume (% of Peak) | Key Sessions |
|------|-------------------|-------------|
| **3 weeks out** | 70-80% | Last 20+ mile long run; one final hard workout (tempo or marathon pace); reduce mid-week volume |
| **2 weeks out** | 55-65% | Long run of 10-13 miles with some race-pace; one short quality session; otherwise easy running |
| **Race week** | 40-50% | All easy running; 2-3 mile "dress rehearsal" run at marathon pace 4-5 days out; strides 2 days out; rest or shakeout day before |

### 5.7 Strict vs. Relaxed Tapers

A study of 158,000+ recreational marathon runners (Frontiers in Sports and Active Living, 2021) found:

- **Strict 3-week taper**: Median finish-time saving of 5 minutes 32 seconds (2.6%) compared to minimal taper
- **Relaxed tapers** (non-progressive reductions) were more common (~69%) but less effective than strict tapers (~30%)
- **Female runners benefited more**: 3.12% median benefit for 2-week strict taper vs. 2.14% for males

### 5.8 Pre-Taper Overload

Research suggests that a brief period of intensified training (pre-taper overload) immediately before the taper can amplify the supercompensation effect. This is akin to the "peak week" concept:

- The hardest training week should be 3-4 weeks before the race
- This provides maximal stimulus before the taper allows recovery
- The taper then "releases" the fitness gains accumulated during overload

### 5.9 Common Taper Mistakes

1. **Tapering too long**: Beyond 21 days, fitness begins to decline. Maximum taper duration should not exceed 3 weeks.
2. **Dropping intensity**: The most common mistake. Keep running at race pace and faster; just do less of it.
3. **Reducing frequency**: Maintain your normal number of running days; shorten individual runs instead.
4. **Not tapering enough**: "Relaxed" or insufficient tapers leave significant performance on the table.
5. **Adding new training elements**: The taper is not the time to try new workouts, shoes, nutrition, or pacing strategies.

Sources:
- [Longer Disciplined Tapers Improve Marathon Performance (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8506252/)
- [Effects of Tapering on Performance: Systematic Review and Meta-Analysis (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10171681/)
- [The Art and Science of the 5K/10K Taper (Outside Online)](https://www.outsideonline.com/health/running/racing/race-strategy/the-art-and-science-of-the-5k-10k-taper/)
- [How to Taper for a Marathon (Laura Norris Running)](https://lauranorrisrunning.com/how-to-taper-for-a-marathon/)
- [Designing Taper for Race Performance (Mayo Clinic)](https://www.mayoclinichealthsystem.org/hometown-health/speaking-of-health/designing-your-taper-to-maximize-your-potential-on-race-day)
- [How to Master Your Taper (COROS)](https://coros.com/stories/coros-coaches/c/how-to-master-your-taper)
- [5K and 10K Taper (The Wired Runner)](https://thewiredrunner.com/5k-and-10k-taper/)
- [Mastering the Half Marathon Taper (Mottiv)](https://www.mymottiv.com/how-to-train-for-a-half-marathon/mastering-the-half-marathon-taper)

---

## Quick Reference: Decision Rules for an AI Running Coach

### Load Management Rules

```
IF acwr < 0.8:
    WARN "Under-training risk. Consider gradually increasing load."
IF 0.8 <= acwr <= 1.3:
    STATUS "Sweet spot. Continue current progression."
IF 1.3 < acwr <= 1.5:
    CAUTION "Elevated load. Monitor recovery closely."
IF acwr > 1.5:
    ALERT "High injury risk. Reduce training load immediately."
IF acwr > 2.0:
    CRITICAL "Very high injury risk (5-21x baseline). Mandatory load reduction."
```

### Weekly Progression Rules

```
IF weekly_mileage < 20:
    max_increase = 20-25%  (absolute increase is small, percentage can be higher)
IF 20 <= weekly_mileage < 40:
    max_increase = 10-15%
IF 40 <= weekly_mileage < 60:
    max_increase = 5-10%
IF weekly_mileage >= 60:
    max_increase = 3-5%

ALWAYS: Step-back week every 3rd or 4th week (reduce 20-30%)
NEVER: Increase both volume AND intensity in the same week
```

### Intensity Distribution

```
easy_percentage = 80%     (Zone 1: below LT1, conversational)
hard_percentage = 20%     (Zone 3: above LT2, intervals/tempo)
grey_zone = MINIMIZE      (Zone 2: between LT1 and LT2)
```

### Taper Decision Matrix

```
IF race_distance == "5K":
    taper_days = 5-7
    volume_reduction = 25-40%
IF race_distance == "10K":
    taper_days = 7-10
    volume_reduction = 30-45%
IF race_distance == "Half Marathon":
    taper_days = 10-14
    volume_reduction = 40-50%
IF race_distance == "Marathon":
    taper_days = 14-21
    volume_reduction = 40-60%

ALWAYS: Maintain intensity during taper
ALWAYS: Maintain frequency during taper
ALWAYS: Use progressive (exponential decay) reduction, not step-down
```

---

This document synthesizes research from systematic reviews, meta-analyses, randomized controlled trials, and large cohort studies. The evidence quality varies -- ACWR thresholds and taper protocols have the strongest support, while periodization model comparisons remain limited by small, short-duration studies. When in doubt, the AI coach should err on the side of conservative load progression and individualized adjustment based on athlete response.