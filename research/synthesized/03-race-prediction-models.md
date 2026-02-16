
# Race Prediction Models: Reference Document for an AI Running Coach

## Table of Contents

1. Riegel Formula
2. Cameron Model
3. Tanda Marathon Prediction
4. VDOT (Jack Daniels)
5. ML/Modern Approaches
6. Adjustment Factors
7. Practical Application for a Coaching AI

---

## 1. Riegel Formula

### The Formula

```
T2 = T1 * (D2 / D1) ^ 1.06
```

Where:
- `T1` = known race time
- `D1` = known race distance
- `D2` = target race distance
- `T2` = predicted race time
- `1.06` = the fatigue factor (endurance exponent)

**Interpretation:** Doubling the distance increases time by a factor of approximately `2^1.06 = 2.084` (not just 2x), capturing the nonlinear slowdown as distance increases.

### Origin

Published by Peter Riegel in *Runner's World* magazine in 1977 and formalized in a 1981 paper. Riegel was an American research engineer and marathoner. The formula models the power-law relationship between race distance and time.

### The Fatigue Factor Exponent

The 1.06 exponent is the population average. Research and coaching experience show it varies by runner profile:

| Runner Type | Exponent Range | Notes |
|---|---|---|
| Speed-oriented / sprinters | 1.03 - 1.05 | Less pace degradation with distance |
| Average recreational runner | 1.06 | Riegel's default |
| Endurance-oriented runner | 1.07 - 1.08 | Standard for strong endurance runners |
| Ultramarathon runners | 1.08 - 1.15 | Greater fatigue effect over extreme distances |
| Nordic skiing | ~1.01 | Lowest across sports |
| Roller skating | ~1.14 | Highest across sports |

**Personalization method:** If a runner has race results at two different distances, solve for the exponent: `exponent = ln(T2/T1) / ln(D2/D1)`. This personal fatigue factor is more accurate than the default 1.06.

### Valid Range

- **Duration:** 3.5 minutes to ~230 minutes (1500m to marathon)
- **Best accuracy:** When input and target distances are within 2-4x of each other
- **Degrades:** For very short races (<3.5 min) and very long races (>4 hours)

### Assumptions and Limitations

1. **Assumes equivalent training** for both distances. A 5K-fit runner on 40 miles/week cannot achieve the predicted marathon time.
2. **Assumes all-out effort** for the input race. Training runs will produce overly slow predictions.
3. **Single exponent for all runners** introduces bias. Natural sprinters will underperform at long distances relative to prediction; natural endurance athletes will outperform.
4. **Based on elite performance data.** May be less accurate for slower recreational runners.
5. **Does not account for** fueling, glycogen depletion, or environmental conditions.
6. **Marathon predictions from 5K** are notoriously optimistic for undertrained runners.

### Scientific Context

A 2023 paper in the *European Journal of Applied Physiology* ("Modelling human endurance: power laws vs critical power") confirmed that the power-law model (Riegel's approach) is more adequate than the hyperbolic/critical-power model for representing the power-duration relationship across a wide range of durations. The power-law model naturally models fatigue without additional corrections and is considered a safer tool for pace selection.

### Sources
- [About Riegel's Formula - PredictMyRun](https://www.predictmyrun.com/about)
- [Riegel's Formula - TrainAsONE](https://trainasone.com/ufaq/riegels-formula/)
- [Peter Riegel - Wikipedia](https://en.wikipedia.org/wiki/Peter_Riegel)
- [Modelling human endurance: power laws vs critical power (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10858092/)
- [Running Writings - Power Laws](https://runningwritings.com/2024/01/problems-with-critical-speed-and-power-laws.html)
- [Race Calculator Accuracy - Runners Connect](https://runnersconnect.net/race-calculators/)
- [Riegel Calculator - had2know.org](https://www.had2know.org/sports/running-time-prediction-calculator-riegel.html)

---

## 2. Cameron Model

### The Formula

```
T2 = T1 * (D2 / D1) * (f(D1) / f(D2))
```

Where `f(x)` is a speed-adjustment function defined as:

**With distances in meters:**
```
f(x) = 13.49681 - 0.000030363 * x + 835.7114 / (x ^ 0.7905)
```

**With distances in miles:**
```
f(x) = 13.49681 - 0.048865 * x + 2.438936 / (x ^ 0.7905)
```

### Coefficients

| Coefficient | Value | Role |
|---|---|---|
| Constant | 13.49681 | Asymptotic speed factor |
| Linear term | -0.000030363 (meters) / -0.048865 (miles) | Distance-dependent speed decay |
| Power term numerator | 835.7114 (meters) / 2.438936 (miles) | Short-distance speed boost |
| Power term exponent | 0.7905 | Rate of short-distance advantage |

### Derivation

Developed by Dave Cameron (1998) for Statistical Services of A.C. Nielsen Co. using **non-linear regression** on the top 10 world-level performances from 400m to 50 miles. Cameron's key insight was modeling **speed** as a function of distance rather than time as a function of distance, which produced a much better fit.

### How It Differs from Riegel

| Aspect | Riegel | Cameron |
|---|---|---|
| Approach | Single power-law exponent | Non-linear regression on speed vs. distance |
| Basis | Population average fatigue factor | World-record performances at each distance |
| Function form | Simple power law | Rational function with 4 coefficients |
| Distance range | 1500m - marathon | 800m - 50 miles |
| Long-distance predictions | Slightly more conservative | Slightly faster (more optimistic) |
| Customization | Can adjust exponent per runner | Fixed coefficients |

### Accuracy Profile

- Works well for post-1945 records at 800m through 10K
- Works well for marathon records from 1964 onward
- Tends to produce slightly faster marathon predictions than Riegel
- Often more accurate for elite runners (since derived from world-class data)
- Does not account for age, sex, or training volume

### Sources
- [Cameron Formula Calculator - had2know.org](https://www.had2know.org/sports/race-performance-prediction-calculator-cameron.html)
- [General Race Predictors - RunBundle](https://runbundle.com/tools/race-predictors/general-race-predictors)
- [FAQ: Race time predictor - chatnrun.nl](https://www.chatnrun.nl/calculator/faq/rp.php)
- [Run-Down Statistics - Performance Predictors](https://run-down.com/statistics/calcs_explained.php)

---

## 3. Tanda Marathon Prediction

### The Formula

```
Pm = 17.1 + 140.0 * exp(-0.0053 * K) + 0.55 * P
```

Where:
- `Pm` = predicted marathon pace (seconds per km)
- `K` = mean weekly training distance (km/week) over the 8-week window
- `P` = mean training pace (seconds per km) over the 8-week window

**To get marathon finish time:** `Finish_time = Pm * 42.195`

### Coefficients Explained

| Constant | Value | Role |
|---|---|---|
| C1 | 17.1 | Base offset (sec/km) -- irreducible minimum pace |
| C2 | 140.0 | Amplitude of mileage effect |
| C3 | 0.0053 | Decay rate of mileage benefit (diminishing returns) |
| C4 | 0.55 | Training pace multiplier (how much faster training -> faster race) |

**How each component works:**
- **C1 (17.1):** Fixed baseline. Even with infinite mileage and zero training pace, you cannot go faster than 17.1 sec/km (~4:33/mile pace).
- **C2 * exp(-C3 * K):** The exponential term captures diminishing returns of weekly mileage. At K=0 km/week, this adds 140 sec/km. At K=100 km/week, it adds ~82 sec/km. At K=200 km/week, ~48 sec/km.
- **C4 * P:** Linear relationship between training pace and race pace. Every 1 sec/km faster in training yields 0.55 sec/km faster in the marathon.

### Data Requirements

- **Training window:** 8 weeks of training data, ending 1 week before the marathon (i.e., weeks 9 through 2 before race day, excluding taper week)
- **Required inputs:** Daily distance and pace for each training run
- **Compute:** Mean weekly distance K (km/week) and mean training pace P (sec/km) across the 8-week window

### Accuracy

- **Standard error of estimate (SEE):** ~4 minutes for runners in the original validation range
- **R-squared:** 0.72 (Tanda's original); 0.81 (Tanda & Knechtle extended model)
- **Validated range:** Marathon finish times of 2:47 to 3:36
- **Gender-independent:** The four coefficients are the same for men and women within the validated range

### Limitations and Adjustments

1. **Range limitations:** Fitted on 22 runners (46 marathons, 2:47-3:36 finish). Less accurate outside this range.
2. **For faster runners (sub-2:47):** The formula tends to overestimate pace (predict slower times). Faster athletes often use polarized training, making C4 effectively lower than 0.55. Personal calibration of C4 may be needed.
3. **For slower runners (>3:36):** Less validated, but the exponential structure should still capture the mileage-performance relationship.
4. **BMI assumption:** Original subjects had BMI < 25. Runners with higher BMI may see reduced accuracy.
5. **Does not account for:** terrain, weather, race strategy, fueling, mental state, or injuries/training interruptions.
6. **Assumes consistent training:** Irregular training patterns reduce accuracy.

### 2022 Validation Study

Tanda's 2022 follow-up paper ("A simple relationship for predicting marathon performance from training: Is it generally applicable?" *Journal of Human Sport and Exercise*, 17(2), 293-301) confirmed:
- C2 and C3 (mileage coefficients) are independent of individual characteristics
- C4 (pace coefficient) may need personalization for elite athletes
- The formula is robust and consistent with Strava data for runners in the 2:47-3:36 range
- For 90 athletes with MPT 2:14-2:47, the formula showed some concerns (tended to overpredict pace)

### Sources
- [Tanda Original Paper (ResearchGate)](https://www.researchgate.net/publication/262686102_Prediction_of_marathon_performance_time_on_the_basis_of_training_indices)
- [Tanda 2022 Validation (ResearchGate)](https://www.researchgate.net/publication/346908023_A_simple_relationship_for_predicting_marathon_performance_from_training_Is_it_generally_applicable)
- [Tanda Race Predictor Tool](https://tandaracepredictor.com/)
- [Tanda Marathon Predictor - Running Universe](https://running-universe.com/predicting-marathon-finish-times-the-tanda-equation/)
- [Fetcheveryone Tanda Calculator](https://www.fetcheveryone.com/training-calculators-tanda.php)

---

## 4. VDOT (Jack Daniels)

### What VDOT Is

VDOT is a "pseudo-VO2max" score developed by Dr. Jack Daniels and Jimmy Gilbert that combines aerobic capacity (VO2max) and running economy into a single performance index. Unlike lab-based VO2max testing, VDOT is calculated from actual race performance.

### The Daniels-Gilbert Formula

**VDOT = VO2_cost / fraction_VO2max**

#### Numerator: Oxygen Cost of Running

```
VO2 = -4.60 + 0.182258 * v + 0.000104 * v^2
```

Where `v` = velocity in **meters per minute**.

| Coefficient | Value | Unit |
|---|---|---|
| Constant | -4.60 | ml O2/kg/min |
| Linear | 0.182258 | ml O2/kg/min per m/min |
| Quadratic | 0.000104 | ml O2/kg/min per (m/min)^2 |

#### Denominator: Fraction of VO2max Sustainable Over Time

```
%VO2max = 0.8 + 0.1894393 * e^(-0.012778 * t) + 0.2989558 * e^(-0.1932605 * t)
```

Where `t` = race duration in **minutes**.

| Coefficient | Value | Role |
|---|---|---|
| Asymptote | 0.8 | Long-duration limit (~80% VO2max) |
| Amplitude 1 | 0.1894393 | Slow decay component |
| Decay rate 1 | 0.012778 | Slow exponential rate (min^-1) |
| Amplitude 2 | 0.2989558 | Fast decay component |
| Decay rate 2 | 0.1932605 | Fast exponential rate (min^-1) |

**Behavior:**
- At t=0 (instantaneous): %VO2max = 0.8 + 0.189 + 0.299 = ~1.288 (>100%, accounting for anaerobic contribution)
- At t=4 min: ~1.0 (100% VO2max sustainable for ~4 min)
- At t=10 min: ~0.96
- At t=30 min: ~0.90
- At t=60 min: ~0.86
- At t=120 min: ~0.83
- At t=240 min: ~0.81
- As t->infinity: approaches 0.80

### Computing VDOT from a Race Result

```python
# Given: race_distance (meters), race_time (minutes)
velocity = race_distance / race_time  # meters per minute
vo2_cost = -4.60 + 0.182258 * velocity + 0.000104 * velocity**2
pct_max = 0.8 + 0.1894393 * math.exp(-0.012778 * race_time) + 0.2989558 * math.exp(-0.1932605 * race_time)
vdot = vo2_cost / pct_max
```

### Predicting Race Times from VDOT

To predict a time at a new distance, you need to find the time `t` such that:
```
VDOT = (-4.60 + 0.182258 * (D/t) + 0.000104 * (D/t)^2) / (0.8 + 0.1894393 * e^(-0.012778*t) + 0.2989558 * e^(-0.1932605*t))
```

This requires numerical solving (Newton's method or binary search) since time appears in both numerator and denominator.

### Training Pace Zones

Each zone is defined as a percentage of VO2max, which maps to a velocity via the oxygen cost equation:

| Zone | % of VO2max | % of HRmax | Purpose | Typical Duration |
|---|---|---|---|---|
| **Easy (E)** | 59-74% | 65-79% | Aerobic base, recovery | Continuous |
| **Marathon (M)** | 75-84% | 80-90% | Marathon-specific endurance | 40-110 min |
| **Threshold (T)** | 83-88% | 88-92% | Lactate threshold improvement | 20-40 min total |
| **Interval (I)** | 95-100% | 98-100% | VO2max development | 3-5 min bouts |
| **Repetition (R)** | >100% | N/A | Speed & running economy | 30s-2 min bouts |

**To compute a training pace from VDOT:**
1. Multiply VDOT by the target %VO2max (e.g., 0.86 for Threshold)
2. Solve the oxygen cost equation for velocity: `target_VO2 = -4.60 + 0.182258*v + 0.000104*v^2`
3. Use the quadratic formula to find `v` (meters/min), then convert to pace

### Sample VDOT Reference Points

| VDOT | 5K Time | 10K Time | Half Marathon | Marathon | Easy Pace (min/mi) |
|---|---|---|---|---|---|
| 30 | 30:40 | 63:46 | 2:21:04 | 4:49:17 | 13:00-14:00 |
| 35 | 27:00 | 56:05 | 2:04:13 | 4:16:13 | 11:30-12:24 |
| 40 | 24:08 | 50:03 | 1:50:59 | 3:49:45 | 10:18-11:06 |
| 45 | 21:50 | 45:16 | 1:40:20 | 3:28:26 | 9:18-10:00 |
| 50 | 19:57 | 41:21 | 1:31:35 | 3:10:49 | 8:30-9:08 |
| 55 | 18:22 | 38:03 | 1:24:16 | 2:56:01 | 7:48-8:24 |
| 60 | 17:03 | 35:22 | 1:18:09 | 2:43:25 | 7:18-7:48 |
| 65 | 15:54 | 33:01 | 1:12:53 | 2:32:35 | 6:48-7:18 |
| 70 | 14:55 | 30:58 | 1:08:19 | 2:23:10 | 6:24-6:54 |
| 75 | 14:03 | 29:09 | 1:04:16 | 2:14:55 | 6:00-6:30 |
| 80 | 13:16 | 27:31 | 1:00:39 | 2:07:38 | 5:42-6:06 |
| 85 | 12:35 | 26:03 | 57:25 | 2:01:06 | 5:24-5:48 |

*Note: Times are approximate. Use the Daniels-Gilbert formula programmatically for precise values.*

### Coaching Adjustments

- **Marathon derating:** Many coaches derate VDOT predictions by 1-1.5 points for half marathon and 2-3 points for full marathon to account for training specificity and fueling challenges.
- **Best input distances:** 5K and 10K races provide the most reliable VDOT estimates (long enough for aerobic measurement, short enough for maximal effort).
- **Recalculation frequency:** Every 4-8 weeks, or after each race.
- **Train at current VDOT, not goal VDOT.**

### Sources
- [VDOT O2 Official Calculator](https://vdoto2.com/calculator)
- [VDOT Training Definitions](https://vdoto2.com/learn-more/training-definitions)
- [Daniels-Gilbert Formula - RunBundle](https://runbundle.com/tools/vo2-max-calculators/vo2-max-calculator)
- [VDOT Training Tables - RunDNA](https://rundna.com/resources/run-training/vdot-training-tables-how-to-use-them/)
- [Demystifying VDOT - T2M Coaching](https://www.tri2max.com/demystifying-vdot)
- [Sport Calculator - VDOT](https://sport-calculator.com/calculators/running/jack-daniels-running-calculator)
- [Daniels-Gilbert Formula GitHub](https://github.com/mekeetsa/vdot)

---

## 5. ML/Modern Approaches

### Overview of Research

Machine learning approaches to race prediction have grown significantly, particularly using large-scale data from platforms like Strava and major marathon race databases.

### Key Models and Papers

#### A. Strava's Performance Predictions (Production System)
- Uses an ML model leveraging **100+ athlete data attributes** including all-time run history and top performances
- Only uses real activity data (not theoretical VO2max estimates)
- Leverages performances from athletes with similar training histories
- Requires at least 20 run activities within a rolling 24-week window
- Generates new predictions after each run upload
- Calculates times for each race distance independently

#### B. LSTM Neural Networks for Generalized Prediction (PMC, 2024)
- "Win Your Race Goal" study analyzed 15,686 runs from 15 runners
- LSTM regression approach achieved **89.13% accuracy**
- Time series regression (TSR) approach achieved 85.21%
- Compared against Riegel formula and UltraSignup formula across 60 races
- Works across marathon to ultramarathon distances with varying elevation

#### C. XGBoost for Ultramarathons (Scientific Reports, 2025)
- Predicts running speed from age, gender, country, event location
- For 100-mile races: R-squared = 0.23 (moderate for population-level prediction)
- Event location was the most important predictor
- For 50-mile races: similar XGBoost approach with improved results

#### D. Case-Based Reasoning / CBR (Springer, 2024)
- Uses "nearest neighbor" runners from large databases
- Predictions based on maximally similar runners in feature space
- More interpretable than black-box ML approaches
- Can add new cases without retraining
- Well-suited to the noisy nature of GPS/running data

#### E. Marathon Prediction from Half-Marathon (Frontiers in Physiology, 2025/2026)
- Predicts marathon time using age group, half-marathon time, sex, and half-marathon pacing strategy
- Intraclass correlation (ICC) = 0.92 between predicted and actual times
- Used Valencia Marathon data; compared against VDOT model

#### F. In-Race Finish Time Prediction (ACM, 2019)
- "Pace My Race" system using 7,931 high-resolution marathon performances
- Real-time pacing recommendations during the race
- Outperforms existing techniques for in-race prediction

### Key Features That Matter

| Feature Category | Specific Features | Importance |
|---|---|---|
| **Training volume** | Weekly mileage, long run distance, total runs | High |
| **Training intensity** | Average pace, pace distribution, HR zones | High |
| **Prior race performance** | Recent 5K/10K/HM times | Very High |
| **Demographics** | Age, sex | Moderate |
| **Training consistency** | Runs per week, training streak, missed days | Moderate |
| **Course characteristics** | Elevation gain, terrain, location | Moderate |
| **Pacing behavior** | Even/negative split tendency, variability | Moderate |
| **Training progression** | Fitness trend (improving/declining) | Moderate |
| **Heart rate data** | Resting HR, training HR, HR drift | Moderate (when available) |

### Algorithms Ranked by Performance

Based on the literature:
1. **XGBoost / Gradient Boosting** -- consistently strong across studies
2. **Decision Trees** -- surprisingly competitive; simple and interpretable
3. **LSTM / Recurrent Neural Networks** -- best for time-series training data
4. **Case-Based Reasoning (k-NN)** -- excellent interpretability, handles noisy data
5. **Random Forest** -- solid but typically slightly behind gradient boosting
6. **Linear Regression** -- good baseline; the problem is near-linear for many feature sets
7. **Bayesian Ridge Regression** -- useful for uncertainty quantification

### ML vs. Classical Formulas

| Aspect | Classical (Riegel/VDOT/Cameron) | ML Approaches |
|---|---|---|
| **Input** | Single recent race result | Entire training history |
| **Data needed** | 1 race time + distance | 20+ activities over 24 weeks |
| **Personalization** | Limited (population average) | High (individual patterns) |
| **Interpretability** | High (clear formula) | Variable (high for CBR, low for NN) |
| **Accuracy for trained runners** | Good (within 3-5%) | Better (within 1-3%) |
| **Cold start** | Works with 1 data point | Needs substantial history |
| **Environmental factors** | Not included | Can be incorporated |

### Notable Tools
- **Strava Performance Predictions** -- ML-powered, subscriber feature
- **Garmin Race Predictor** -- Uses VO2max estimates from wearable data
- **Metathon** -- ML-based marathon prediction platform
- **42cal** -- Multi-model race predictor

### Sources
- [Win Your Race Goal - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11495242/)
- [XGBoost for Ultra-Marathon - Scientific Reports](https://www.nature.com/articles/s41598-025-92581-w)
- [Learning to Run Marathons - Springer](https://link.springer.com/chapter/10.1007/978-3-031-67256-9_13)
- [Strava Performance Predictions](https://support.strava.com/hc/en-us/articles/35272903405965-Performance-Predictions)
- [Strava ML blog announcement](https://communityhub.strava.com/what-s-new-10/we-know-how-fast-you-ll-run-your-next-race-9441)
- [ML Marathon Prediction Medium article](https://medium.com/runners-life/i-was-tired-of-flawed-race-predictions-so-i-built-a-model-that-actually-understands-runners-179a2a1e57a4)
- [Quantifying Uncertainty in Marathon Predictions (CMU)](https://www.stat.cmu.edu/cmsac/conference/2024/assets/pdf/Onyejekwe24.pdf)
- [Modelling Training Practices (ACM)](https://dl.acm.org/doi/fullHtml/10.1145/3565472.3592952)
- [Frontiers in Physiology - Marathon from Half (2026)](https://public-pages-files-2025.frontiersin.org/journals/physiology/articles/10.3389/fphys.2025.1718298/pdf)

---

## 6. Adjustment Factors

### 6.1 Temperature / Heat

#### Simple Coaching Rule of Thumb
```
pace_adjustment_sec_per_mile = (temp_F - 65) * 2    (for temp > 65F)
```
Example: At 88F, add 46 seconds per mile.

#### Percentage-Based Model
```
pace_increase_pct = 0.4% * max(0, temp_F - 60) + 0.2% * max(0, humidity_pct - 60)
```

#### Temperature + Dew Point Method

Sum temperature (F) and dew point (F), then look up:

| Temp + Dew Point Sum | Pace Adjustment |
|---|---|
| <= 100 | No adjustment |
| 101-110 | 0% to 0.5% |
| 111-120 | 0.5% to 1.0% |
| 121-130 | 1.0% to 2.0% |
| 131-140 | 2.0% to 3.0% |
| 141-150 | 3.0% to 4.5% |
| 151-160 | 4.5% to 6.0% |
| 161-170 | 6.0% to 8.0% |
| 171-180 | 8.0% to 10.0% |
| >180 | Hard running not recommended |

#### Research-Based Marathon Heat Table (from Fellrnr / 42,000 finish times)

Approximate performance degradation by heat index temperature for marathon:

| Heat Index | Performance Loss (approx.) |
|---|---|
| 40-50F (4-10C) | Optimal; 0% |
| 55F (13C) | 0-1% |
| 60F (16C) | 1-3% |
| 65F (18C) | 2-5% |
| 70F (21C) | 4-8% |
| 75F (24C) | 6-12% |
| 80F (27C) | 8-16% |
| 85F (29C) | 12-20% |

*Ranges depend on runner's pace -- slower runners are affected more.*

#### Key Research Finding
Heat and humidity have a **multiplicative** effect: hot and humid is much worse than either in isolation. Humidity effects become negligible below ~65F (18C). Ideal marathon conditions: 35-55F (2-13C).

### 6.2 Altitude

#### General Rules of Thumb

```
performance_loss_pct = 2% per 1000 feet above sea level
```

More refined (below sea-level threshold):
```
performance_loss_pct = 2% per 1000 feet above 3000 feet
```

Effects are not typically noticeable below 3,000 feet (914m).

#### Jack Daniels' Altitude Guidelines

| Altitude (ft) | Pace Slowdown (sec/mile) |
|---|---|
| 3,000 | Threshold of effect |
| 4,000 | 4-5 sec/mile |
| 5,000 | 8-10 sec/mile |
| 6,000 | 12-15 sec/mile |
| 7,000 | 16-20 sec/mile |
| 8,000 | 20-25 sec/mile |

#### VO2max-Based Model

```
vo2max_reduction_pct = 6.3% per 1000m above 300m    (elite athletes)
                     = 7.0% per 1000m               (general population)
                     = 8-11% per 1000m               (some studies)
```

**Important:** Race performance loss is **less** than raw VO2max reduction because athletes do not race at 100% VO2max. Olympic data shows 2-4% slower endurance times above 1000m.

#### Acclimatization
- 2-3 weeks of acclimatization reduces the impact by approximately half
- Allow 2-3 days for moderate altitudes (1,500-2,500m)
- Allow 1-2 weeks for high altitudes (2,500m+)

### 6.3 Course Elevation / Grade Adjusted Pace (GAP)

#### D.B. Dill's Oxygen Cost Model
Vertical oxygen cost: **1.31 ml O2 / kg / meter climbed**

#### Jack Daniels' Simple Rule
- **Uphill:** Add 12-15 seconds per 100m (328 ft) of elevation gain per mile
- **Downhill:** Subtract 7-8 seconds per 100m of elevation loss per mile
- Downhill benefit is ~55% of uphill cost

#### Energy Cost per Grade
- Each 1% grade increase costs approximately **3-4% more energy**
- A 5% grade requires ~15-20% more energy than flat running

#### Minetti et al. (2002) Polynomial Model

Energy cost of running (Cr, in J/kg/m) as a function of gradient *i* (expressed as a decimal, e.g., 0.10 for 10%):

**5th-order polynomial (walking, widely cited form):**
```
Cr(i) = 280.5*i^5 - 58.7*i^4 - 76.8*i^3 + 51.9*i^2 + 19.6*i + 2.5
```

Key data points for running from Minetti's measurements:
- Level (0%): 3.40 J/kg/m
- Optimal downhill (-10%): ~1.73 J/kg/m (minimum metabolic cost)
- +10% grade: ~7.0 J/kg/m
- +45% grade: ~18.93 J/kg/m

#### Flat-Equivalent Distance Formula
```
flat_equivalent_distance = distance + k1 * elevation_gain - k2 * elevation_loss
```

Where k1 > k2 (uphill costs more than downhill saves). Typical values: k1 ~ 7-10, k2 ~ 3-5 (multiplied by vertical meters to produce equivalent horizontal meters).

#### Key Asymmetry
Running up a 10% grade slows pace by ~45%. Running down a 10% grade speeds pace by only ~13%. Uphills hurt much more than downhills help.

### 6.4 Wind

- **Headwind:** Increases metabolic cost proportional to wind speed squared (drag force)
- **Tailwind benefit is approximately 50% of headwind cost** (asymmetric effect)
- No widely-used correction formula for running (unlike cycling)
- Rule of thumb: A 10 mph headwind costs roughly 5-8% more energy; a 10 mph tailwind saves roughly 2-4%

### 6.5 Age Grading (WMA)

#### Formula
```
age_graded_time = actual_time / age_factor
age_grade_pct = (open_world_record / age_graded_time) * 100
```

#### Current Tables
- **WMA 2023 tables** (effective January 1, 2023) are the current standard
- **2025 road running tables** approved January 10, 2025 by USATF Masters (improved interpolation for distances other than 5K, 10K, HM, Marathon)
- Age factors available for ages 8-100, both genders
- Factors derived from millions of performances and validated against individual athlete careers spanning decades

#### Performance Level Classification

| Age-Grade % | Classification |
|---|---|
| >90% | World class |
| 80-89% | National class |
| 70-79% | Regional class |
| 60-69% | Local competitive |
| 50-59% | Recreational |
| <50% | Beginner |

#### Sources for Tables
- [WMA Age-Grading Calculator](https://www.howardgrubb.co.uk/athletics/wmalookup15.html)
- [Age-Grade Tables GitHub](https://github.com/AlanLyttonJones/Age-Grade-Tables)
- [RunBundle Age Grading Calculator](https://runbundle.com/tools/age-grading-calculator)

### 6.6 Fitness Trend (Improving vs. Maintaining)

No standardized formula exists, but practical approaches:

1. **VDOT trajectory:** Track VDOT from races every 4-8 weeks. Fit a trendline. Extrapolate cautiously (1-2 VDOT points per training cycle max).
2. **Training load trend:** If weekly mileage and intensity are increasing, predictions should be adjusted optimistically; if plateaued, use current fitness level.
3. **Rule of thumb:** A runner who has been improving steadily for 3+ months can reasonably target 1-2% faster than current race-equivalent predictions.
4. **Caution:** Never extrapolate improvement indefinitely. Fitness gains follow a logarithmic curve -- large gains early, diminishing returns over years.

### Sources (Section 6)
- [Fellrnr Impact of Heat on Marathon Performance](https://fellrnr.com/wiki/Impact_of_Heat_on_Marathon_Performance)
- [Running Writings Heat Calculator](https://apps.runningwritings.com/heat-adjusted-pace/)
- [Running Writings Heat & Humidity Analysis](https://runningwritings.com/2025/04/heat-humidity-marathon-times.html)
- [Final Surge Altitude Calculator](https://www.finalsurge.com/altitude-conversion-calculator)
- [VDOT Altitude Adjustments](https://news.vdoto2.com/2011/03/ask-a-coach-how-do-you-adjust-threshold-pace-at-altitude/)
- [RunBundle GAP Calculator](https://runbundle.com/tools/grade-adjusted-pace-calculator)
- [Running Writings GAP Calculator](https://apps.runningwritings.com/gap-calculator/)
- [Minetti et al. 2002 - Energy Cost at Extreme Slopes (PubMed)](https://pubmed.ncbi.nlm.nih.gov/12183501/)
- [Runners Connect Altitude Guide](https://runnersconnect.net/high-altitude-training-running-performance/)
- [TrainingPeaks Heat/Humidity/Wind/Altitude](https://www.trainingpeaks.com/coach-blog/preparing-for-heat-humidity-wind-and-altitude/)
- [WMA Age-Grade Tables - EMA](https://european-masters-athletics.org/wma-proposed-age-grading-tables/)
- [USATF Masters Age Grading](https://usatfmasters.org/age-grading/)

---

## 7. Practical Application for a Coaching AI

### 7.1 When to Use Which Model

| Scenario | Recommended Model | Rationale |
|---|---|---|
| Runner has 1 recent race, wants prediction at similar distance | **Riegel** | Simple, reliable for nearby distances |
| Runner has 1 recent race, wants training paces | **VDOT** | Directly produces 5 training zones |
| Runner has extensive training log, targeting marathon | **Tanda** | Uses actual training data, not just race results |
| Runner has multiple race results at different distances | **Riegel with personal exponent** | Calibrated fatigue factor beats population average |
| Runner has rich Strava/GPS history | **ML model** | Leverages full training context |
| Comparing fitness across ages | **WMA Age Grading** | Standardized, well-validated |
| No race data available, only training data | **Tanda** or **ML** | Only models that work without race input |
| Elite runner, 800m-marathon range | **Cameron** | Derived from world-class performances |
| Cold start (new user, minimal data) | **Riegel** or **VDOT** | Work with a single data point |

### 7.2 Decision Tree for Model Selection

```
Does the runner have a recent race result (within 6 weeks)?
  YES:
    Is the target distance within 2-4x of the race distance?
      YES -> Use Riegel AND VDOT. Compare predictions.
      NO -> Use VDOT (better for larger distance jumps)
    Does the runner have training log data for the past 8 weeks?
      YES -> Also run Tanda (for marathon predictions)
    Does the runner have multiple race results at different distances?
      YES -> Compute personal Riegel exponent. Weight this heavily.
  NO:
    Does the runner have 8+ weeks of training data?
      YES -> Use Tanda (marathon) or ML model (other distances)
      NO -> Cannot make reliable prediction. Ask runner to do a time trial.
```

### 7.3 Combining Multiple Predictions

**Ensemble approach (recommended):**

1. Run all applicable models given available data
2. Compute weighted average:
   ```
   final_prediction = w1*riegel + w2*vdot + w3*tanda + w4*cameron
   ```
3. Suggested weights:
   - If race data is recent and reliable: Riegel (0.30), VDOT (0.35), Cameron (0.15), Tanda (0.20)
   - If only training data: Tanda (0.70), ML if available (0.30)
   - If multiple races at different distances: Personal Riegel exponent model (0.50), VDOT (0.30), Cameron (0.20)

4. **Concordance check:** If all models agree within 2-3%, confidence is high. If they diverge by >5%, investigate why:
   - Large divergence often indicates the runner is a "speedster" or "endurance specialist"
   - Divergence between Riegel and VDOT for marathon suggests undertrained for the distance

### 7.4 Confidence Intervals

**Practical uncertainty bands:**

| Prediction Type | 50% Confidence | 80% Confidence | 95% Confidence |
|---|---|---|---|
| 5K from 10K | +/- 1% | +/- 2% | +/- 3% |
| Half from 10K | +/- 2% | +/- 4% | +/- 6% |
| Marathon from half | +/- 3% | +/- 5% | +/- 8% |
| Marathon from 5K | +/- 5% | +/- 8% | +/- 12% |
| Marathon from training (Tanda) | +/- 2% (~4 min) | +/- 4% (~8 min) | +/- 6% (~12 min) |

**Factors that widen confidence intervals:**
- Input race was not a maximal effort
- Input race was >6 weeks ago
- Large distance ratio (e.g., 5K to marathon)
- Runner is new to the target distance
- Runner's training volume is mismatched for target distance
- Environmental conditions differ between input race and target race

**Factors that narrow confidence intervals:**
- Multiple concordant model predictions
- Personal Riegel exponent from multiple races
- Tanda model with consistent 8-week training block
- Runner has previously raced the target distance

### 7.5 Pre-Prediction Adjustments

Before generating a final prediction, apply corrections in this order:

1. **Normalize input race:** Adjust the input race time for any environmental factors (heat, altitude, wind) that were present. Get the "ideal conditions" equivalent time.
2. **Generate raw prediction** using selected model(s).
3. **Apply target-race adjustments:** Correct for the expected environmental conditions of the target race (temperature, altitude, elevation profile).
4. **Apply training-volume sanity check:** If the runner's weekly mileage is below what's typically needed for the distance, derate the prediction.
5. **Apply fitness-trend adjustment:** If the runner is on an improving trajectory, allow a small optimistic adjustment (1-2%).
6. **Present with confidence interval.**

### 7.6 Marathon-Specific Weekly Mileage Sanity Check

| Weekly Mileage (mi) | Realistic Marathon Target |
|---|---|
| 20-30 | Finish only; predictions unreliable |
| 30-40 | 4:00-5:00+ depending on speed |
| 40-50 | 3:30-4:30 |
| 50-60 | 3:00-3:45 |
| 60-70 | 2:45-3:15 |
| 70-80 | 2:30-3:00 |
| 80-100 | Sub-2:45 |
| 100+ | Elite territory |

If a 5K-based prediction suggests a marathon time that is unrealistic for the runner's training volume, the coaching AI should flag this and present a range based on the mileage-adjusted expectation.

### 7.7 Communication to Runners

The coaching AI should:
1. **Always present a range**, not a single number. "Based on your recent 10K, your marathon potential is 3:25-3:35."
2. **Explain the assumptions.** "This assumes you'll average 50+ miles/week in your training block and race in moderate conditions."
3. **Flag mismatches.** "Your 5K speed suggests 3:15, but your current mileage of 35 miles/week makes 3:35-3:45 more realistic."
4. **Use multiple models when possible** and explain concordance: "Three different models agree on 3:28-3:32, which gives us high confidence in this range."
5. **Recommend calibration races.** "Run a half marathon 4-6 weeks before your target marathon to refine the prediction."

### Sources (Section 7)
- [Sport Calculator - Race Prediction Guide](https://sport-calculator.com/blog/how-to-predict-race-times-vdot-critical-speed)
- [Runners Connect - Race Calculator Accuracy](https://runnersconnect.net/race-calculators/)
- [Quantifying Uncertainty in Marathon Predictions (CMU)](https://www.stat.cmu.edu/cmsac/conference/2024/assets/pdf/Onyejekwe24.pdf)
- [Multi-Model Prediction Approach (Medium)](https://medium.com/runners-life/i-was-tired-of-flawed-race-predictions-so-i-built-a-model-that-actually-understands-runners-179a2a1e57a4)
- [Modelling Training Practices for Personalised Recommendations (ACM)](https://dl.acm.org/doi/fullHtml/10.1145/3565472.3592952)
- [RunBundle General Race Predictors](https://runbundle.com/tools/race-predictors/general-race-predictors)

---

## Summary of All Formulas (Quick Reference)

### Riegel
```
T2 = T1 * (D2/D1)^1.06
```

### Cameron
```
T2 = T1 * (D2/D1) * f(D1)/f(D2)
f(x) = 13.49681 - 0.000030363*x + 835.7114/x^0.7905    [x in meters]
```

### Tanda
```
Pm(sec/km) = 17.1 + 140.0 * exp(-0.0053 * K) + 0.55 * P
K = mean weekly km, P = mean training pace (sec/km), 8-week window
```

### VDOT (Daniels-Gilbert)
```
VDOT = (-4.60 + 0.182258*v + 0.000104*v^2) / (0.8 + 0.1894393*e^(-0.012778*t) + 0.2989558*e^(-0.1932605*t))
v = velocity (m/min), t = time (min)
```

### Personal Riegel Exponent (from 2 races)
```
exponent = ln(T2/T1) / ln(D2/D1)
```

### Heat Adjustment (percentage-based)
```
pace_increase_pct = 0.4% * max(0, temp_F - 60) + 0.2% * max(0, humidity_pct - 60)
```

### Altitude Adjustment
```
pace_loss_pct ≈ 2% per 1000 ft above 3000 ft (unacclimatized)
```

### Age Grading
```
age_graded_time = actual_time / WMA_age_factor
age_grade_pct = open_world_record / age_graded_time * 100
```

### Grade Adjusted Pace (simplified Daniels)
```
time_adjustment = +12 to 15 sec per 100m elevation gain per mile
                  -7 to 8 sec per 100m elevation loss per mile
```