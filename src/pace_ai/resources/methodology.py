"""Coaching methodology — static knowledge base for Claude to reference.

Exports:
    METHODOLOGY: Core coaching principles, zones, periodisation, population guidelines.
    ZONES_EXPLAINED: Detailed zone-by-zone breakdown with session formats.
    FIELD_TEST_PROTOCOLS: LTHR, MaxHR, and Resting HR test protocols.
"""

from __future__ import annotations

METHODOLOGY = """# Running Coaching Methodology

## Core Principles

### 1. Progressive Overload
Gradually increase training stress to drive adaptation. The body needs progressively greater stimulus
to continue improving. As a guideline, limit weekly volume increases to ~10% per week, with a
recovery week (reduced volume by 20-30%) every 3-4 weeks. Note: the 10% rule is a guideline, not
an absolute threshold — increases >30% clearly increase injury risk, while 10-30% varies by
individual context (Nielsen et al. 2014; Gabbett 2018). See docs/references.md for citations.

### 2. Specificity
Training must be specific to the goal race. A 5K runner needs more VO2max work; a marathon runner
needs more sustained threshold and long run work. The long run and key workouts should progressively
approach race-specific demands.

### 3. Recovery
Adaptation happens during rest, not during training. Hard days must be followed by easy days.
Sleep, nutrition, and stress management are as important as the training itself.
Signs of inadequate recovery: persistent fatigue, elevated resting HR, declining performance,
mood changes, increased illness frequency.

### 4. Individualisation
Every athlete responds differently. Age, training history, injury history, life stress, and
genetics all affect optimal training load. Monitor individual response rather than following
rigid formulas.

## Training Zones (Daniels' VDOT Model)
Note: The VDOT system is from Daniels' Running Formula (Human Kinetics, ISBN 9781718203662).
It is an industry-standard coaching tool but was not published in a peer-reviewed journal.

| Zone | Name | Effort | % of Threshold Pace | Purpose |
|------|------|--------|---------------------|---------|
| 1 | Easy (E) | Conversational | 59-74% VO2max | Aerobic base, recovery, fat oxidation |
| 2 | Marathon (M) | Comfortably hard | 75-84% VO2max | Marathon-specific endurance |
| 3 | Threshold (T) | Hard but sustainable | 83-88% VO2max | Lactate clearance, sustained speed |
| 4 | Interval (I) | Hard | 95-100% VO2max | VO2max development |
| 5 | Repetition (R) | Very hard / sprint | 105-120% VO2max | Speed, economy, neuromuscular |

### Zone Guidelines
- **Easy runs (Zone 1)**: Should feel genuinely easy. You should be able to hold a conversation.
  If you can't talk in full sentences, you're going too fast. This is where most training happens.
- **Threshold (Zone 3)**: "Comfortably hard." You could sustain this for about 60 minutes in a race.
  In training, tempo runs are typically 20-40 minutes at this effort.
- **Intervals (Zone 4)**: Hard. Typical format: 3-5 minute repeats with equal rest (jog recovery).
  Total hard running: 8-10% of weekly volume.
- **Repetitions (Zone 5)**: Short and fast. 200m-400m repeats at mile pace or faster, with full
  recovery. Develops speed and running economy.

## Race Prediction

### VDOT Model (Daniels)
Uses oxygen cost curves to predict equivalent race performances across distances. More accurate
than Riegel for well-trained runners, especially for shorter-to-longer predictions.

### Riegel Formula
T2 = T1 x (D2/D1)^1.06
Originally published in Runner's World (Riegel, 1977). Simple and effective. Slightly
optimistic for longer distances (marathon from 5K). Best used for distances within 2-3x
of each other. Not formally peer-reviewed but widely adopted.

### Key Workout Indicators
- **5K predictor**: 3 x 1600m at goal 5K pace with 3-4 min rest. If you can do this, the 5K is realistic.
- **10K predictor**: 5 x 1000m at goal 10K pace with 2 min rest.
- **Half marathon predictor**: 2 x 5K at goal half pace with 3 min rest.
- **Marathon predictor**: Long run of 32-35K with final 10-15K at marathon pace.

## Weekly Structure

### Typical Week
- **Monday**: Rest or easy cross-train
- **Tuesday**: Quality session (intervals or tempo)
- **Wednesday**: Easy run
- **Thursday**: Quality session (tempo or threshold)
- **Friday**: Easy run or rest
- **Saturday**: Long run
- **Sunday**: Easy recovery run

### Intensity Distribution (Seiler 2010; Stöggl & Sperlich 2014)
The 80/20 principle refers to cumulative training TIME: ~80% at easy effort (Zone 1),
~20% at moderate-to-hard effort (Zones 2-5). This is distinct from volume (distance)
distribution, where dedicated easy runs typically comprise 50-60% of weekly km, with
the remainder split between quality sessions and warm-up/cool-down segments.

- Long run: 25-30% of weekly volume
- Quality sessions: 15-20% of weekly volume at moderate/hard effort
- Dedicated easy runs: 50-60% of weekly volume
- Overall time in Zone 1: ~80% (including easy portions of quality sessions)

## Injury Prevention Red Flags

- Weekly mileage increase > 30% clearly elevates injury risk; >10% warrants caution
  (Nielsen et al. 2014; Gabbett 2018)
- ACWR > 1.5 (Gabbett 2016; Hulin et al. 2014, 2016). Note: most ACWR validation is from
  team sports; use as one indicator among many, not a standalone predictor (Impellizzeri 2020)
- Inconsistent week-to-week loading (high load variability). Note: the CV > 0.3 threshold is
  a general statistics convention, not a validated sports science threshold
- Persistent elevated resting heart rate (>5 bpm above baseline for 3+ days)
- Declining performance despite maintained or increased volume
- Any sharp pain (vs. normal training soreness)
- For all athletes: signs of low energy availability (RED-S) — fatigue, illness, mood changes,
  declining performance despite training (IOC Consensus: Mountjoy et al. 2014, 2018, 2023)

Full citations: see docs/references.md

## ACWR Action Thresholds

Based on ACWR (acute:chronic workload ratio), adapt the training plan accordingly:

| ACWR Range | Status | Action |
|-----------|--------|--------|
| 0.8-1.3 | Optimal | Maintain or progress as planned |
| 1.3-1.5 | Elevated | Reduce volume, limit or drop intensity sessions |
| >1.5 | High risk | Immediate deload — easy running only, no quality sessions |
| <0.8 | Detraining | Gradual ramp-up; do not spike volume to compensate |

When ACWR is elevated or high, the priority shifts from fitness to protection. Frame deloads
as a positive investment, not a setback.

## Population-Specific Guidelines

### Beginners (new to running or low volume)
- Easy running only — no tempo, threshold, or interval sessions until a consistent
  base of 3-4 weeks is established.
- Maximum 3-4 running days per week with rest days between runs.
- Walk/run approach is appropriate and effective (e.g., run 3 min / walk 1 min).
- Volume progression: conservative (≤10% per week), prioritise consistency over distance.
- Paces should feel genuinely easy — conversational throughout.
- Encouragement and simplicity over complexity.

### Returning from Injury
- No intensity work in the initial return period.
- Gradual volume increase (≤10% per week from current, not pre-injury, baseline).
- Rest day between each running day to allow tissue adaptation.
- Walk/run approach is appropriate during rebuild.
- Monitor for pain, swelling, or recurrence — "listen to your body" with specific guidance
  on what to watch for.
- Do NOT attempt to return to pre-injury volume quickly. Patience is essential.

### Senior Runners (60+)
- Maximum 3 running days per week with rest day between each run.
- Include strength and balance training 1-2 times per week (Rogers 1990; Zampieri 2022).
- Walk/run approach recommended for beginners and those returning to running.
- All running at easy/conversational effort unless the runner has an established base.
- Joint health, bone density, and fall prevention are relevant considerations.
- Recovery takes longer — respect it. Age is not a barrier; inadequate recovery is.

### Youth Athletes (under 18)
- Prioritise long-term athletic development over immediate performance results.
- Limit structured speed work (max 2 quality sessions per week).
- Encourage variety, cross-training, and enjoyment of running.
- Adequate sleep (8-10 hours) and nutrition are critical during growth.
- For adolescent females specifically:
  - Monitor iron status (periodic blood tests recommended).
  - Screen for signs of low energy availability (RED-S): fatigue, recurring illness,
    missed or irregular periods, declining performance despite training.
  - Acknowledge menstrual health openly and without stigma.
  - Create space for the athlete to share how they are feeling — subjective feedback
    is as important as objective data.
  - Never comment on body weight, shape, or composition.
- For all youth: racing is a learning experience, not a judgement of worth.

## Periodisation

### Phase Structure
1. **Base phase** (4-8 weeks): Build aerobic volume. Mostly easy running with strides. Establish consistency.
2. **Build phase** (4-8 weeks): Introduce quality sessions. Tempo runs, threshold work. Volume continues to build.
3. **Peak phase** (2-4 weeks): Race-specific intensity. Highest quality, volume stabilises or slightly decreases.
4. **Taper phase** (1-3 weeks): Reduce volume by 40-60%. Maintain intensity. Sharpen for race day.
5. **Race**: Execute the plan.
6. **Recovery phase** (1-2 weeks): Reduced easy running. No quality sessions. Physical and mental recovery.

### Taper Guidelines (Bosquet et al. 2007; Smyth & Lawlor 2021)
Optimal taper: 2 weeks, 41-60% progressive volume reduction, maintain intensity and
frequency. Yields ~3% performance improvement (Bosquet meta-analysis, 27 studies).
For recreational marathon runners, a disciplined 3-week taper saves ~5:30 median
finish time (Smyth & Lawlor, 158,000+ runners).

- Reduce volume, not intensity
- For 5K-10K: 7-10 day taper, 25-40% volume reduction
- For half marathon: 2-3 week taper, 40-60% progressive volume reduction
- For marathon: 2-3 week taper, 41-60% progressive volume reduction
- Last hard workout: 10 days before race (5K-10K) or 14 days before (half/marathon)
- Maintain session frequency (4-5 runs/week during taper)
"""

ZONES_EXPLAINED = """# Training Zones Explained

## Zone 1: Easy (E)

**Effort**: Conversational. You could talk in full sentences without gasping.
**Heart rate**: 65-79% of threshold HR
**Purpose**: This is where the magic happens for distance runners.
- Builds aerobic base (mitochondrial density, capillary development)
- Promotes fat oxidation efficiency
- Allows recovery between hard sessions
- Strengthens tendons, ligaments, and bones without excess stress

**Common mistake**: Running easy days too fast. If you're breathing hard, slow down.
"If you think you're going too slowly, slow down more."

**Typical sessions**:
- Recovery runs (20-40 min)
- Easy runs (30-60 min)
- Should make up ~80% of weekly running time (Seiler 2010)

---

## Zone 2: Marathon (M)

**Effort**: Comfortably hard. You can speak in short phrases but not paragraphs.
**Heart rate**: 80-87% of threshold HR
**Purpose**: Marathon-specific endurance development.
- Teaches the body to sustain moderate effort for long periods
- Improves glycogen efficiency
- Develops mental toughness for sustained pace

**Typical sessions**:
- Marathon-pace segments within long runs (e.g., last 10-15K of a long run at M pace)
- Standalone marathon-pace runs (40-60 min)
- Not used heavily outside of marathon training blocks

---

## Zone 3: Threshold (T)

**Effort**: Hard but sustainable. You could race at this pace for about 60 minutes.
**Heart rate**: 88-92% of threshold HR
**Purpose**: The most time-efficient zone for improving distance running performance.
- Raises lactate threshold (the pace you can sustain before lactate accumulates)
- Develops your ability to "hold on" when it gets hard
- Critical for 10K through marathon performance

**Typical sessions**:
- Tempo runs: 20-40 min continuous at T pace
- Cruise intervals: 4-6 x 5 min at T pace with 60-90 sec jog rest
- Threshold is the benchmark pace — all other zones reference it

---

## Zone 4: Interval (I)

**Effort**: Hard. Breathing heavily. Can only speak a few words at a time.
**Heart rate**: 93-97% of threshold HR (approaches max by end of intervals)
**Purpose**: Develops maximal aerobic capacity (VO2max).
- The primary limiter for 5K and 10K performance
- Improves oxygen delivery and utilisation
- Develops the ability to process and clear lactate under high load

**Typical sessions**:
- 5 x 1000m with 3-4 min jog recovery
- 4 x 1200m with 3 min recovery
- 6-8 x 800m with 2-3 min recovery
- Hard running should total 8-10% of weekly volume

---

## Zone 5: Repetition (R)

**Effort**: Very hard to all-out. Sprint-like mechanics.
**Heart rate**: Not a useful guide (too short for HR to respond fully)
**Purpose**: Develops speed, running economy, and neuromuscular coordination.
- Improves stride efficiency and ground contact time
- Develops fast-twitch muscle fibre recruitment
- Sharpens leg turnover for race finishing speed

**Typical sessions**:
- 8-12 x 200m at mile pace with full recovery (200m walk)
- 6-8 x 400m at ~mile pace with full recovery
- Strides: 6-8 x 100m accelerations (not a workout, done after easy runs)
- Full recovery between reps is essential — this is about quality, not fatigue
"""

FIELD_TEST_PROTOCOLS = """# Field Test Protocols

## Lactate Threshold Heart Rate (LTHR) — Friel 30-Minute Time Trial

The gold standard self-test for establishing HR training zones. Your LTHR is the
average heart rate from the last 20 minutes of a 30-minute all-out time trial.

### Protocol
1. **Warm up** 15 min easy running with 3-4 strides
2. **Start recording** on your GPS watch
3. **Run 30 minutes** as hard as you can sustain — aim for even effort, not even pace
4. **Lap at 10 minutes** (press lap button to mark the split)
5. **Cool down** 10 min easy
6. **Your LTHR** = average HR from minutes 10-30 (the last 20 minutes)

### Why Last 20 Minutes?
The first 10 minutes include HR ramp-up time and pacing errors. The last 20 minutes
reflect your true steady-state threshold effort.

### Tips
- Pick a flat, measured course (track is ideal)
- Do not sprint the finish — stay steady
- Do this test when rested (after an easy day)
- Repeat every 6-8 weeks to track fitness changes
- Use the result to set HR zones in calculate_training_zones (threshold_hr parameter)

### Expected Results by Level
| Level | Typical LTHR | Notes |
|-------|-------------|-------|
| Beginner | 155-170 bpm | Varies widely with age and genetics |
| Intermediate | 160-175 bpm | Improves with threshold training |
| Advanced | 165-185 bpm | Highly individual at this level |

---

## Maximum Heart Rate — Pfitzinger Uphill Repeats

Determines your true max HR. The 220-age formula is inaccurate for ~30% of people.
A field test gives a personal, accurate number.

### Protocol
1. **Warm up** 15-20 min easy with 4-6 strides
2. **Find a steep hill** (6-10% grade, 400-600m long)
3. **Run 3 x 600m uphill repeats** at maximal effort:
   - Rep 1: Hard but controlled (building to max)
   - Rep 2: Harder
   - Rep 3: All-out from start, sprint the final 100m
4. **Jog down** between reps (full recovery not needed — 2-3 min)
5. **Your Max HR** = highest HR recorded during rep 3
6. **Cool down** 10-15 min easy

### Why Uphill?
- Eliminates the eccentric muscle damage of flat sprinting
- Forces maximum cardiovascular output
- Safer for joints and connective tissue
- More reliable than flat sprinting (less risk of premature stop from leg fatigue)

### Safety
- Only attempt if currently running at least 3x per week
- Do not attempt if you have any cardiovascular concerns — consult a doctor first
- Stop immediately if you feel dizzy, have chest pain, or anything abnormal
- Have someone present if possible

### Tips
- Do not attempt on a treadmill (most cap at low grades)
- Use a chest strap HR monitor (optical watches lag at high HR)
- Your max HR is the single highest reading, not the average
- Max HR does not change with fitness (it's genetic and age-dependent)
- Use the result with calculate_hr_zones_karvonen (max_hr parameter)

---

## Resting Heart Rate — Morning Protocol

Accurate resting HR is essential for Karvonen (HRR) zone calculation.

### Protocol
1. **Measure for 5 consecutive mornings** — consistency matters
2. **Immediately upon waking**, before sitting up, getting out of bed, or checking phone
3. **Lie still for 1-2 minutes** with your HR monitor on
4. **Record the lowest stable reading** (ignore the first few seconds)
5. **Your Resting HR** = average of the 5 lowest morning readings

### Tips
- Alcohol, caffeine (evening before), and poor sleep will elevate readings
- Avoid mornings after hard training sessions
- A sudden increase of 5+ bpm above your baseline for 3+ days signals overtraining or illness
- Resting HR decreases with improved aerobic fitness (a good progress indicator)
"""
