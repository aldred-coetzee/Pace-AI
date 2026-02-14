"""Coaching methodology — static knowledge base for Claude to reference."""

from __future__ import annotations

METHODOLOGY = """# Running Coaching Methodology

## Core Principles

### 1. Progressive Overload
Gradually increase training stress to drive adaptation. The body needs progressively greater stimulus
to continue improving. Increase weekly volume by no more than 10% per week, with a recovery week
(reduced volume by 20-30%) every 3-4 weeks.

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
Simple and effective. Slightly optimistic for longer distances (marathon from 5K). Best used
for distances within 2-3x of each other.

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

### Volume Distribution
- Long run: 25-30% of weekly volume
- Quality sessions: 15-20% of weekly volume at moderate/hard effort
- Easy running: 50-60% of weekly volume

## Injury Prevention Red Flags

- Weekly mileage increase > 10% from 4-week rolling average
- ACWR > 1.5 (acute:chronic workload ratio)
- Training monotony > 2.0 (too-uniform daily loading)
- Persistent elevated resting heart rate (>5 bpm above baseline for 3+ days)
- Declining performance despite maintained or increased volume
- Any sharp pain (vs. normal training soreness)

## Periodisation

### Phase Structure
1. **Base phase** (4-8 weeks): Build aerobic volume. Mostly easy running with strides. Establish consistency.
2. **Build phase** (4-8 weeks): Introduce quality sessions. Tempo runs, threshold work. Volume continues to build.
3. **Peak phase** (2-4 weeks): Race-specific intensity. Highest quality, volume stabilises or slightly decreases.
4. **Taper phase** (1-3 weeks): Reduce volume by 40-60%. Maintain intensity. Sharpen for race day.
5. **Race**: Execute the plan.
6. **Recovery phase** (1-2 weeks): Reduced easy running. No quality sessions. Physical and mental recovery.

### Taper Guidelines
- Reduce volume, not intensity
- For 5K-10K: 7-10 day taper, 30-40% volume reduction
- For half marathon: 10-14 day taper, 40-50% volume reduction
- For marathon: 2-3 week taper, 50-60% volume reduction
- Last hard workout: 10 days before race (5K-10K) or 14 days before (half/marathon)
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
- Should make up ~80% of weekly running volume

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
