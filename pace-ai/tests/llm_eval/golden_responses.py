"""Golden coaching responses — curated correct advice for each profile.

Each response follows the output format from the coaching prompt templates
and embodies the methodology, tool outputs, and evidence-based guidelines
for that profile's specific situation.

These serve as:
1. Mocked outputs for deterministic rubric testing
2. Reference standards for live LLM comparison
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════
# WEEKLY PLAN GOLDEN RESPONSES
# ═══════════════════════════════════════════════════════════════════════

WEEKLY_PLAN_GOLDEN: dict[str, str] = {}

# ── 01: Beginner Male, 30, Healthy ──────────────────────────────────

WEEKLY_PLAN_GOLDEN["01_beginner_m30_healthy"] = """\
## Weekly Training Plan — Alex (Beginner, 5K goal: 27:00)

Your ACWR is 1.14 and training load is in the optimal range. You've been \
consistent at 17-20 km/week, which is a solid foundation. Let's build \
gradually toward your 5K goal.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Easy run — 5.0 km at 7:00-8:00/km pace. Purpose: aerobic \
base building at conversational effort.
- **Wednesday**: Rest or light cross-training (walking, cycling, yoga — 30 min)
- **Thursday**: Easy run — 5.5 km at 7:00-8:00/km pace. Purpose: aerobic \
development, building running habit.
- **Saturday**: Long run — 6.5 km at 7:30-8:00/km pace. Purpose: build \
endurance and time on feet. Keep it conversational.
- **Sunday**: Easy recovery run — 4.0 km at 7:30-8:00/km pace, or rest \
if feeling fatigued.

### Weekly Summary

- **Weekly total**: 21.0 km (5% increase from last week's 20 km)
- **Intensity distribution**: 100% easy
- **Key session**: Saturday's long run — at this stage, building time on \
feet is the single most important thing you can do. Keep it genuinely easy \
and enjoy it.

### Notes
At your current level, all running should be at easy, conversational pace. \
Speed work is not appropriate yet — your aerobic base is still developing. \
The fitness gains from consistent easy running are substantial and will \
naturally bring your 5K time down. Focus on showing up consistently \
3-4 times per week.
"""

# ── 02: Beginner Female, 28, Healthy ───────────────────────────────

WEEKLY_PLAN_GOLDEN["02_beginner_f28_healthy"] = """\
## Weekly Training Plan — Sarah (Beginner, 5K goal: 29:00)

Your ACWR is 1.13 — you're in the optimal training range. You've been \
building consistently from 12 to 17 km/week. Let's continue that gradual \
progression.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Easy run — 4.5 km at 7:30-8:30/km pace. Purpose: aerobic \
base building at conversational effort.
- **Wednesday**: Rest or gentle cross-training (swimming, yoga — 20-30 min)
- **Thursday**: Easy run — 5.0 km at 7:30-8:30/km pace. Purpose: building \
consistency and aerobic capacity.
- **Saturday**: Long run — 5.5 km at 8:00-8:30/km pace. Purpose: building \
endurance. This should feel comfortable — if you're breathing hard, slow down.
- **Sunday**: Rest day

### Weekly Summary

- **Weekly total**: 15.0 km (staying within your recent range rather than \
pushing further, since last week was already a jump to 17 km)
- **Intensity distribution**: 100% easy
- **Key session**: Saturday's long run — building your longest continuous \
run is the priority. Keep it genuinely easy. If you need to walk for a \
minute, that's perfectly fine.

### Notes
You're making excellent progress. At this stage, consistency matters more \
than speed. All your runs should be at a pace where you can hold a full \
conversation. Your 5K goal of 29:00 is very achievable with steady base \
building — no speed work needed yet. Your body is adapting to the demands \
of running, and patience now pays dividends later.
"""

# ── 03: Beginner Male, 45, Returning from Injury ───────────────────

WEEKLY_PLAN_GOLDEN["03_beginner_m45_returning_injury"] = """\
## Weekly Training Plan — David (Returning from Injury, 10K goal)

**Important**: Your ACWR is 0.43, which means your recent volume is well \
below your chronic average. You've been tapering down — from 15 km to 5 km \
over the last few weeks. This is consistent with managing a calf strain, \
but we need to be very careful about how we rebuild.

The biggest risk right now is ramping up too fast. Your chronic load has \
dropped, so even a modest increase could spike your ACWR into dangerous \
territory. Patience is essential.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Easy walk/jog — 2.0 km. Alternate 3 min jogging / 2 min \
walking. Purpose: tissue reloading at minimal stress. Stay at 8:30-9:00/km \
or slower.
- **Wednesday**: Rest day
- **Thursday**: Easy walk/jog — 2.0 km. Same walk/jog protocol. Purpose: \
assess how the calf responds with a day of rest between sessions.
- **Friday**: Rest day
- **Saturday**: Easy walk/jog — 2.5 km. Purpose: slightly longer time on \
feet if Tuesday and Thursday went well.
- **Sunday**: Rest day

### Weekly Summary

- **Weekly total**: 6.5 km (gradual increase from 5 km)
- **Intensity distribution**: 100% easy (walk/jog only)
- **Key session**: Thursday — this is your test session. If the calf feels \
good after Tuesday AND after Thursday, Saturday can proceed. If you feel \
any pain, tightness, or discomfort in the calf, skip Saturday and consult \
your physiotherapist.

### Notes
Your 10K goal on August 1st gives you plenty of time. There is no rush. \
The walk/jog approach protects the healing tissue while maintaining fitness. \
Monitor for: pain during or after running, swelling at the injury site, \
or any change in your running gait. Rest days between every running day \
are non-negotiable at this stage. We can begin transitioning to continuous \
easy running once you're comfortably doing 10+ km/week without symptoms \
for 2-3 consecutive weeks.
"""

# ── 04: Beginner Female, 35, Returning from Injury ─────────────────

WEEKLY_PLAN_GOLDEN["04_beginner_f35_returning_injury"] = """\
## Weekly Training Plan — Maria (Returning from Injury, 5K goal)

**Important**: Your ACWR is 0.65, and your recent trend shows declining \
volume (from 15 km down to 8 km). This suggests the knee issue may still \
be affecting your training. The priority is to stabilise your volume \
before trying to build.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Easy run — 3.0 km at 8:00-8:45/km pace. Purpose: gentle \
return to consistent running. Keep effort truly easy.
- **Wednesday**: Rest day — light stretching or yoga if desired
- **Thursday**: Easy run — 3.0 km at 8:00-8:45/km pace. Purpose: build \
running consistency with adequate recovery between sessions.
- **Friday**: Rest day
- **Saturday**: Easy run — 3.0 km at 8:00-8:45/km pace. Purpose: maintain \
frequency without adding volume stress.
- **Sunday**: Rest day

### Weekly Summary

- **Weekly total**: 9.0 km (a small, gradual increase from 8 km)
- **Intensity distribution**: 100% easy
- **Key session**: There is no "key session" this week — the key is \
consistency and being symptom-free across all three runs.

### Notes
I know it's tempting to push back toward 12-15 km/week where you were a \
few weeks ago, but rebuilding gradually is essential. Your knee needs \
consistent, predictable loading — not big spikes. If all three runs this \
week feel good with no knee pain during or after, we can add 1 km to \
one session next week. Your July 5K gives us plenty of time to rebuild \
safely. Every run should feel comfortable and pain-free. If any run \
produces knee discomfort, take an extra rest day and consider checking \
in with your physiotherapist.
"""

# ── 05: Intermediate Male, 32, Healthy ─────────────────────────────

WEEKLY_PLAN_GOLDEN["05_intermediate_m32_healthy"] = """\
## Weekly Training Plan — James (Intermediate, Half Marathon goal: 1:35:00)

Your ACWR is 1.06 and load variability is very low (CV 0.03) — excellent \
consistency. Your VDOT of 47.7 predicts a half marathon time of 1:35:19, \
which aligns perfectly with your sub-1:35 goal. This is realistic with \
good preparation.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Tempo run — 10 km total. Warm up 2 km easy, then 6 km at \
threshold pace (4:25-4:37/km), cool down 2 km easy. Purpose: raise lactate \
threshold, which is the key limiter at half marathon distance.
- **Wednesday**: Easy run — 7 km at 5:30-6:00/km. Purpose: recovery and \
aerobic maintenance.
- **Thursday**: Interval session — 10 km total. Warm up 2 km easy, \
5 x 1000m at 3:59-4:09/km (interval pace) with 3 min jog recovery, \
cool down 2 km easy. Purpose: VO2max development to lift your overall \
aerobic ceiling.
- **Friday**: Easy run — 6 km at 5:30-6:00/km. Purpose: active recovery.
- **Saturday**: Long run — 14 km. First 10 km at easy pace (5:30-6:00/km), \
last 4 km at marathon pace (4:32-4:54/km). Purpose: build endurance and \
practise half marathon-pace running on tired legs.
- **Sunday**: Easy run — 5 km at 5:30-6:00/km, or rest if fatigued.

### Weekly Summary

- **Weekly total**: ~48 km (4% increase from last week's 46 km)
- **Intensity distribution**: 79% easy / 13% threshold / 8% interval
- **Key session**: Tuesday's tempo run — sustained threshold running is \
the most race-specific session for a half marathon. If you can comfortably \
hold 4:30/km for 6 km in training, you're on track for sub-1:35.
"""

# ── 06: Intermediate Female, 29, Healthy ───────────────────────────

WEEKLY_PLAN_GOLDEN["06_intermediate_f29_healthy"] = """\
## Weekly Training Plan — Emma (Intermediate, Half Marathon goal: 1:42:00)

Your ACWR is 1.07 with very low variability — textbook consistency. Your \
VDOT of 44.1 predicts a half marathon time of exactly 1:42:00, confirming \
your goal is well-calibrated.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Tempo run — 9 km total. Warm up 2 km easy, then 5 km at \
threshold pace (4:42-4:56/km), cool down 2 km easy. Purpose: lactate \
threshold development — the key physiological determinant for half marathon.
- **Wednesday**: Easy run — 6 km at 5:45-6:15/km. Purpose: recovery and \
aerobic maintenance.
- **Thursday**: Interval session — 9 km total. Warm up 2 km easy, \
4 x 1000m at 4:14-4:25/km with 3 min jog recovery, cool down 2 km easy. \
Purpose: VO2max stimulus to lift aerobic capacity.
- **Friday**: Rest day or easy cross-training (30 min swim/bike)
- **Saturday**: Long run — 12 km at easy pace (5:45-6:15/km). Purpose: \
build endurance and time on feet for half marathon preparation.
- **Sunday**: Easy run — 5 km at 5:45-6:15/km. Purpose: light recovery \
volume.

### Weekly Summary

- **Weekly total**: ~41 km (2.5% increase from last week's 40 km)
- **Intensity distribution**: 78% easy / 14% threshold / 8% interval
- **Key session**: Tuesday's tempo run — for half marathon preparation, \
the ability to sustain threshold pace for extended periods is crucial. \
Building from 5 km tempo segments toward 8-10 km will be a key marker \
of readiness.
"""

# ── 07: Intermediate Male, 40, Overreaching ────────────────────────

WEEKLY_PLAN_GOLDEN["07_intermediate_m40_overreaching"] = """\
## Weekly Training Plan — Mark (CAUTION: Overreaching Detected)

**ACWR Alert**: Your ACWR is 1.6, which is in the HIGH risk zone. You \
jumped from 30 km last week to 48 km this week — a 60% increase. Your \
chronic average is 30 km. This is a significant training load spike and \
the priority this week is protecting your health.

### Recommendation: Immediate Deload Week

I know you're excited about your first marathon (September 20), and a \
sub-3:30 is achievable based on your VDOT of 45.9. But right now, the \
single most important thing is to reduce volume and recover. You have \
plenty of time — the marathon is months away.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Easy run — 5 km at 5:30-6:15/km. Purpose: maintain \
movement without adding load. Truly easy effort only.
- **Wednesday**: Rest day or light cross-training (30 min walk, swim, yoga)
- **Thursday**: Easy run — 5 km at 5:30-6:15/km. Purpose: gentle volume \
at recovery effort.
- **Friday**: Rest day
- **Saturday**: Easy run — 6 km at 5:30-6:15/km. Purpose: longest run \
of the week, still at easy effort.
- **Sunday**: Rest day

### Weekly Summary

- **Weekly total**: ~16 km (a deliberate reduce from this week's 48 km)
- **Intensity distribution**: 100% easy — no tempo, no intervals, no speed work
- **Key session**: There is no key session this week. The key is recovery.

### Recovery Plan
This deload brings your volume back below your chronic average. After this \
week, we can begin gradually rebuilding. Here's the path forward:
1. **Next week**: ~20 km (all easy)
2. **Week after**: ~25 km (easy + strides)
3. **Following weeks**: Gradual 10% increases back toward 30-35 km
4. **Resume quality sessions**: Only after 2 weeks of consistent volume \
at or near your chronic average

The best marathon training is consistent training. One big spike week \
followed by forced time off is worse than steady, moderate progression. \
Let's protect your health and build toward September properly.
"""

# ── 08: Intermediate Female, 38, Overreaching ──────────────────────

WEEKLY_PLAN_GOLDEN["08_intermediate_f38_overreaching"] = """\
## Weekly Training Plan — Lisa (CAUTION: Overreaching Detected)

**ACWR Alert**: Your ACWR is 1.51, placing you in the HIGH risk zone. \
You went from 26 km to 40 km this week — a 54% increase, well above the \
safe threshold. Your chronic average is 26.5 km. This needs to be \
addressed immediately.

### Recommendation: Deload Week

Your half marathon goal of sub-1:48 in July is realistic — your VDOT of \
42.0 predicts 1:46:22. But training through a load spike like this is \
how injuries happen. We need to reduce volume now to protect your ability \
to train consistently through the spring and summer.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Easy run — 4 km at 5:45-6:30/km. Purpose: maintain running \
habit without loading stress.
- **Wednesday**: Rest day
- **Thursday**: Easy run — 4 km at 5:45-6:30/km. Purpose: gentle movement \
at purely conversational effort.
- **Friday**: Rest day
- **Saturday**: Easy run — 5 km at 5:45-6:30/km. Purpose: slightly longer \
easy effort if Tuesday and Thursday felt good.
- **Sunday**: Rest day or gentle cross-training

### Weekly Summary

- **Weekly total**: ~13 km (deliberate reduce to well below chronic average)
- **Intensity distribution**: 100% easy — no quality sessions this week
- **Key session**: None — recovery is the priority.

### Path Forward
After this deload week, we'll rebuild gradually:
1. **Week 2**: ~18 km (all easy)
2. **Week 3**: ~22 km (easy + strides)
3. **Week 4**: ~25 km (easy + one light tempo session)
4. **Resume normal training**: Once volume has been consistent at 25-28 km \
for 2 weeks

Taking 7-10 days at reduced volume now prevents losing months to injury. \
This is how smart training works.
"""

# ── 09: Advanced Male, 25, Healthy ─────────────────────────────────

WEEKLY_PLAN_GOLDEN["09_advanced_m25_healthy"] = """\
## Weekly Training Plan — Ryan (Advanced, Marathon goal: sub-2:40)

Your ACWR is 1.06 with exceptional load consistency (CV 0.03). At VDOT \
61.8, the VDOT model predicts a marathon time of 2:39:19, which confirms \
sub-2:40 is achievable. You're in a strong position.

### Day-by-Day Plan

- **Monday**: Easy run — 10 km at 4:30-4:55/km. Purpose: recovery after \
the weekend long run. Truly easy effort.
- **Tuesday**: Threshold session — 16 km total. Warm up 3 km easy, \
then 2 x 5 km at threshold pace (3:34-3:45/km) with 2 min jog recovery, \
cool down 3 km easy. Purpose: sustained lactate threshold work — critical \
for marathon performance.
- **Wednesday**: Easy run — 12 km at 4:30-4:55/km. Include 6 x 100m \
strides at the end. Purpose: aerobic volume + neuromuscular activation.
- **Thursday**: Marathon-pace long intervals — 16 km total. Warm up 3 km \
easy, then 3 x 3 km at marathon pace (3:41-3:59/km) with 1 km easy \
between, cool down 2 km easy. Purpose: race-specific preparation — \
practise holding marathon pace when fatigued.
- **Friday**: Easy run — 8 km at 4:30-4:55/km. Purpose: active recovery.
- **Saturday**: Long run — 28 km. First 20 km at easy pace (4:30-4:55/km), \
last 8 km progressing to marathon pace (3:41-3:59/km). Purpose: this is \
the most important session of the week — builds marathon-specific endurance \
and practises negative splitting on tired legs.
- **Sunday**: Easy run — 6 km at 4:30-4:55/km, or complete rest.

### Weekly Summary

- **Weekly total**: ~96 km (4% increase from 92 km — within 10% guideline)
- **Intensity distribution**: 76% easy / 16% threshold-marathon / 8% interval
- **Key session**: Saturday's long run with marathon-pace finish. At this \
stage of preparation, the ability to run the final 8-10 km of a 28+ km \
long run at goal marathon pace is the strongest predictor of race-day \
readiness. This session builds both physiological and psychological \
confidence.
"""

# ── 10: Advanced Female, 27, Healthy ──────────────────────────────

WEEKLY_PLAN_GOLDEN["10_advanced_f27_healthy"] = """\
## Weekly Training Plan — Olivia (Advanced, Half Marathon goal: sub-1:18)

Your ACWR is 1.06 with excellent consistency (CV 0.03). At VDOT 57.8, \
the model predicts 1:20:43 for the half marathon. Sub-1:18 is aggressive \
but achievable with focused preparation.

### Day-by-Day Plan

- **Monday**: Easy run — 10 km at 4:45-5:10/km. Purpose: recovery from \
the weekend. Keep effort conversational.
- **Tuesday**: Threshold session — 14 km total. Warm up 3 km easy, \
then 4 x 2 km at threshold pace (3:46-3:57/km) with 90 sec jog recovery, \
cool down 3 km easy. Purpose: lactate threshold development — the primary \
physiological limiter for half marathon performance.
- **Wednesday**: Easy run — 10 km at 4:45-5:10/km with 6 x 100m strides. \
Purpose: aerobic volume + leg speed maintenance.
- **Thursday**: VO2max intervals — 14 km total. Warm up 3 km easy, \
5 x 1000m at 3:24-3:33/km (interval pace) with 3 min jog recovery, \
cool down 3 km easy. Purpose: elevate VO2max ceiling to support a faster \
sustained pace.
- **Friday**: Easy run — 8 km at 4:45-5:10/km. Purpose: active recovery.
- **Saturday**: Long run — 22 km. Easy pace throughout (4:45-5:10/km) \
with the final 5 km at half marathon pace (~3:42-3:50/km). Purpose: \
build endurance and practise goal pace on tired legs.
- **Sunday**: Easy run — 6 km at 4:45-5:10/km, or rest.

### Weekly Summary

- **Weekly total**: ~84 km (2.4% increase from 82 km)
- **Intensity distribution**: 77% easy / 14% threshold / 9% interval
- **Key session**: Tuesday's threshold session — for sub-1:18, you need \
to sustain ~3:42/km for 21.1 km. Building the ability to hold threshold \
pace (3:46-3:57/km) for longer and longer segments is the most direct \
path to race readiness.
"""

# ── 11: Advanced Male, 22, Injury Risk ─────────────────────────────

WEEKLY_PLAN_GOLDEN["11_advanced_m22_injury_risk"] = """\
## Weekly Training Plan — Tyler (URGENT: High Injury Risk)

**ACWR Alert**: Your ACWR is 1.6 with a load variability CV of 0.16. \
This week you ran 100 km — an 82% increase from last week's 55 km, and \
60% above your chronic average of 62.5 km. This is a dangerous loading \
pattern that requires immediate correction.

Beyond the acute spike, your loading pattern over the past 8 weeks has \
been erratic: 60, 65, 55, 70, 50, 75, 55, 100 km. The inconsistency \
itself is a risk factor — your body cannot adapt properly when volume \
swings this wildly.

### Recommendation: Immediate Deload

I understand you have a sub-15 5K goal in 4 weeks. At your fitness level \
(VDOT 66.2), you have the aerobic capacity. But running that race requires \
arriving healthy. Right now, the priority is reducing volume to allow your \
body to absorb the recent overload.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Easy run — 8 km at 4:15-4:40/km. Purpose: maintain movement \
without adding training stress.
- **Wednesday**: Rest day or pool running/aqua jogging (30 min)
- **Thursday**: Easy run — 8 km at 4:15-4:40/km. Purpose: gentle volume \
at recovery effort.
- **Friday**: Rest day
- **Saturday**: Easy run — 10 km at 4:15-4:40/km. Purpose: longest run \
of the week, still purely easy.
- **Sunday**: Rest day or light cross-training

### Weekly Summary

- **Weekly total**: ~26 km (sharp and deliberate reduce to well below \
chronic average)
- **Intensity distribution**: 100% easy — absolutely no speed work, no \
intervals, no tempo
- **Key session**: None — recovery and consistency are the only goals.

### Path Forward
1. **This week**: 26 km easy
2. **Week 2**: ~45 km easy + strides
3. **Week 3**: ~55-60 km with one moderate tempo session
4. **Week 4 (race week)**: ~40 km with a sharpening session early in the \
week, then taper

Going forward, commit to CONSISTENT weekly volume. Running 60-70 km every \
week is far better than alternating between 50 and 100 km. The erratic \
loading pattern is as dangerous as any single spike. Build a steady rhythm \
and your 15:00 5K will come.
"""

# ── 12: Advanced Female, 24, Injury Risk ───────────────────────────

WEEKLY_PLAN_GOLDEN["12_advanced_f24_injury_risk"] = """\
## Weekly Training Plan — Jade (URGENT: High Injury Risk)

**ACWR Alert**: Your ACWR is 1.59 with a load variability CV of 0.12. \
This week you ran 90 km — a 73% increase from last week's 52 km, and \
well above your chronic average of 56.8 km. This loading spike places \
you in the high injury risk category.

Your loading pattern has been inconsistent: 55, 58, 50, 62, 48, 65, \
52, 90 km. This week-to-week volatility makes it harder for your body \
to adapt and increases injury vulnerability.

### Recommendation: Immediate Deload

Your 10K goal of sub-35 on April 1st is realistic — your VDOT of 61.2 \
predicts 34:46. But arriving at the start line injured helps no one. \
The priority is to reduce volume immediately and stabilise.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Easy run — 7 km at 4:30-5:00/km. Purpose: gentle movement \
at recovery effort.
- **Wednesday**: Rest day or light cross-training (pool, bike)
- **Thursday**: Easy run — 7 km at 4:30-5:00/km. Purpose: maintain routine \
without additional stress.
- **Friday**: Rest day
- **Saturday**: Easy run — 8 km at 4:30-5:00/km. Purpose: longest run of \
the week, easy effort.
- **Sunday**: Rest day

### Weekly Summary

- **Weekly total**: ~22 km (significant and deliberate reduce)
- **Intensity distribution**: 100% easy
- **Key session**: None — recovery is the priority.

### Path Forward
1. **This week**: 22 km easy
2. **Week 2**: ~40 km easy + strides
3. **Week 3**: ~50 km with one tempo session
4. **Race week**: ~35 km taper with a sharpening workout early in the week

For the future: aim for consistent 55-60 km weeks rather than swinging \
between 48 and 90 km. Consistency is the foundation of performance. Your \
aerobic fitness is already there — what you need is the discipline to \
keep loading steady.

Also: please ensure you're eating enough to support this training load. \
At your volume and intensity, energy availability is critical. If you \
notice unusual fatigue, missed periods, or declining performance despite \
adequate training, these are signals worth discussing with a sports \
medicine professional.
"""

# ── 13: Senior Male, 62, Beginner ──────────────────────────────────

WEEKLY_PLAN_GOLDEN["13_senior_m62_beginner"] = """\
## Weekly Training Plan — Robert (Senior Beginner, 5K goal: finish running)

Your ACWR is 1.02 — very stable. You've been consistent at 12-14 km/week \
for the past month, which is a great foundation. Your commitment to \
regular running is paying off.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Easy run/walk — 4.0 km. Run 4 min, walk 1 min, repeat. \
Pace should be 9:00-10:00/km during running segments. Purpose: build \
running endurance gradually while protecting joints and connective tissue.
- **Wednesday**: Strength training — 25-30 min. Focus on: squats (bodyweight \
or light), single-leg balance exercises, calf raises, planks, hip bridges. \
Purpose: bone density, joint stability, injury prevention. This is as \
important as the running itself.
- **Thursday**: Rest day
- **Friday**: Easy run/walk — 4.5 km. Same walk/run approach. Purpose: \
maintain running frequency with a rest day between each session.
- **Saturday**: Rest day
- **Sunday**: Easy run/walk — 5.0 km (your longest run of the week). \
Purpose: build time on feet.

### Weekly Summary

- **Weekly total**: 13.5 km (similar to recent weeks — maintaining rather \
than pushing)
- **Intensity distribution**: 100% easy
- **Key session**: Wednesday's strength work — at 62, strength training \
is essential for safe running. It builds bone density, stabilises joints, \
and prevents the muscle loss that accelerates after age 60. Even 20-30 \
minutes twice a week makes a significant difference.

### Notes
Never run on consecutive days at this stage — recovery between sessions is \
essential. Your muscles recover faster than your tendons and bones, which \
need 48+ hours between running sessions. \
The run/walk approach is not a compromise — many experienced runners use \
it, and it dramatically reduces injury risk while building the same aerobic \
fitness.

Your 5K race in June is very achievable. If you'd like to run the entire \
distance, we can gradually reduce the walk intervals over the coming weeks. \
But finishing strong with walk breaks is far better than pushing for \
continuous running and getting injured.

If you haven't already, consider a check-in with your GP or a sports \
physician — not because anything is wrong, but because it's good practice \
when starting a new exercise programme in your 60s. A brief cardiovascular \
screening provides peace of mind and helps us train with confidence.
"""

# ── 14: Senior Female, 58, Beginner ───────────────────────────────

WEEKLY_PLAN_GOLDEN["14_senior_f58_beginner"] = """\
## Weekly Training Plan — Patricia (Senior Beginner, 5K goal: complete it)

Your ACWR is 1.02 — nicely stable. You've been very consistent at 10-12 \
km/week, and that consistency is exactly what builds long-term fitness. \
You mentioned concern about joint health — the evidence is reassuring: \
recreational running does not increase osteoarthritis risk and may actually \
protect joints through improved cartilage nutrition.

### Day-by-Day Plan

- **Monday**: Rest day
- **Tuesday**: Easy run/walk — 3.5 km. Run 3 min, walk 2 min, repeat. \
Stay at 9:30-10:30/km during running segments. Purpose: aerobic base \
building with managed impact loading.
- **Wednesday**: Strength training — 25-30 min. Bodyweight squats, wall \
push-ups, calf raises, hip bridges, balance work (single-leg stands). \
Purpose: bone density maintenance, joint stability, fall prevention.
- **Thursday**: Rest day
- **Friday**: Easy run/walk — 3.5 km. Same run/walk intervals. Purpose: \
second running session of the week with full recovery day between.
- **Saturday**: Rest day
- **Sunday**: Easy run/walk — 4.0 km. Purpose: longest session of the \
week, building time on feet.

### Weekly Summary

- **Weekly total**: 11.0 km (maintaining your current range)
- **Intensity distribution**: 100% easy
- **Key session**: Wednesday's strength training — for runners over 55, \
strength work is not optional. It maintains bone mineral density, prevents \
age-related muscle loss (sarcopenia), and stabilises the joints that running \
loads. Even light resistance work twice a week provides substantial benefits.

### Notes
Three running days per week with rest days between each is the right \
structure for you right now. Your tendons and connective tissue need \
48-72 hours to recover between running sessions — this is not a sign of \
weakness, it's normal physiology.

Your July 5K goal is well within reach. Walking breaks during the race \
are absolutely fine — you mentioned that yourself, and it's the smart \
approach. As your fitness builds, the running intervals will naturally get \
longer and the walk breaks shorter.

Keep running on flat, predictable surfaces for now. As balance and \
proprioception improve (the strength training helps with this), trails \
can be introduced gradually.

If you haven't had a recent cardiovascular screening, consider scheduling \
one with your doctor. This is standard guidance for anyone beginning an \
exercise programme later in life.
"""

# ── 15: Teen Male, 17, Talent ─────────────────────────────────────

WEEKLY_PLAN_GOLDEN["15_teen_m17_talent"] = """\
## Weekly Training Plan — Ethan (17yo, Development Phase, 5K goal: 17:00)

Your ACWR is 1.2 — still in the optimal range but at the upper end. \
Note that this week was 48 km, up 20% from last week's 40 km. That's a \
larger jump than ideal. Let's be careful not to keep pushing volume up \
aggressively.

At VDOT 56.3 with a recent 18:00 5K, you're a talented runner with a \
bright future. The most important thing at your age is long-term \
development, not peaking for one race.

### Day-by-Day Plan

- **Monday**: Easy run — 6 km at 4:45-5:15/km. Purpose: start the week \
with recovery volume.
- **Tuesday**: Workout — 9 km total. Warm up 2 km easy, 4 x 1000m at \
3:28-3:37/km (interval pace) with 3 min jog recovery, cool down 2 km \
easy. Purpose: VO2max development for 5K preparation.
- **Wednesday**: Easy run — 6 km at 4:45-5:15/km + strength and \
conditioning (20 min core, hip stability, plyometrics). Purpose: aerobic \
maintenance + injury prevention.
- **Thursday**: Easy run — 6 km at 4:45-5:15/km. Purpose: recovery between \
quality sessions.
- **Friday**: Tempo run — 8 km total. Warm up 2 km easy, 4 km at threshold \
pace (3:51-4:03/km), cool down 2 km easy. Purpose: lactate threshold \
development — builds the sustained speed needed for a strong 5K.
- **Saturday**: Long run — 10 km at easy pace (4:45-5:15/km). Purpose: \
aerobic endurance and time on feet.
- **Sunday**: Rest day

### Weekly Summary

- **Weekly total**: ~45 km (a slight pullback from 48 km for sustainability)
- **Intensity distribution**: 80% easy / 11% threshold / 9% interval
- **Key session**: Tuesday's intervals — 4 x 1000m is the classic 5K \
preparation workout. Focus on even pacing across all 4 repeats rather \
than going out too hard.

### Development Notes
You're at an age where your body is still developing. The focus should be \
on building a broad aerobic base and developing good habits — these will \
serve you for the next decade of running. A few things to keep in mind:

1. **Consistency over heroics**: Steady 42-48 km weeks are better than \
alternating between 35 and 55 km.
2. **No more than 2 quality sessions per week** at this stage.
3. **Sleep**: Aim for 8-10 hours. This is when adaptation happens.
4. **Nutrition**: Eat enough to fuel your training. Growing and training \
at this volume requires substantial energy intake.
5. **Enjoy it**: Running should be fun. If it stops being fun, something \
needs to change.

Your state championship qualifier goal of 17:00 is within reach — you \
ran 18:00 recently and have room to improve with good preparation. Trust \
the process and stay patient.
"""

# ── 16: Teen Female, 16, Talent ───────────────────────────────────

WEEKLY_PLAN_GOLDEN["16_teen_f16_talent"] = """\
## Weekly Training Plan — Sophia (16yo, Development Phase, 5K goal: 18:00)

Your ACWR is 1.2 — optimal range, but this week's 42 km was 20% higher \
than last week's 35 km. That's the upper limit of what's safe. Let's \
stabilise here rather than continuing to push upward.

At VDOT 51.3 with a 19:30 5K, you have excellent talent and room to grow. \
The priority at 16 is long-term development — building the foundation for \
your best running years ahead, not peaking now.

### Day-by-Day Plan

- **Monday**: Easy run — 5 km at 5:00-5:40/km. Purpose: start the week \
with easy volume.
- **Tuesday**: Workout — 8 km total. Warm up 2 km easy, 5 x 800m at \
3:45-3:54/km (interval pace) with 2.5 min jog recovery, cool down 2 km \
easy. Purpose: VO2max development — the key physiological quality for 5K.
- **Wednesday**: Easy run — 5 km at 5:00-5:40/km + strength and \
conditioning (20 min — single-leg squats, hip stability, core, light \
plyometrics). Purpose: injury prevention and neuromuscular development.
- **Thursday**: Easy run — 5 km at 5:00-5:40/km. Purpose: recovery.
- **Friday**: Tempo run — 7 km total. Warm up 1.5 km easy, 4 km at \
threshold pace (4:09-4:22/km), cool down 1.5 km easy. Purpose: lactate \
threshold development.
- **Saturday**: Long run — 9 km at easy pace (5:00-5:40/km). Purpose: \
build aerobic endurance.
- **Sunday**: Rest day

### Weekly Summary

- **Weekly total**: ~39 km (a slight pullback from 42 km)
- **Intensity distribution**: 80% easy / 12% threshold / 8% interval
- **Key session**: Tuesday's 5 x 800m — shorter intervals with adequate \
recovery develop VO2max without excessive fatigue. Focus on smooth, \
controlled running rather than racing the reps.

### Development Notes
At 16, you're in a critical development phase. Here's what matters most:

1. **Long-term thinking**: The best female distance runners in the world \
typically peak in their mid-to-late 20s. Everything you do now is building \
toward that potential. There's no need to rush.
2. **Consistency over volume**: Steady 35-42 km weeks are more valuable \
than occasional big weeks.
3. **No more than 2 quality sessions per week.**
4. **Sleep**: 8-10 hours per night. This is when your body grows and adapts.
5. **Nutrition and energy availability**: Eat enough to fuel both your \
training AND your growth. Restricting food intake at your age is harmful \
and counterproductive. Female runners are at higher risk for iron \
deficiency — consider periodic iron checks with your doctor. If \
you're frequently tired, getting sick, noticing missed periods, or feel \
like training is getting harder despite being consistent, talk to your \
coach or a sports medicine professional. These can be signs of low \
energy availability (RED-S), which is both a health and performance concern.
6. **Listen to your body**: If something hurts, speak up. Growth plates \
are still developing at your age, and pain deserves attention, not \
toughness.
7. **Have fun**: Running should bring you joy. Cross-training, running with \
friends, and keeping variety in your training all help sustain your love \
of the sport.

Your 18:00 5K goal for the state qualifier is achievable. Trust the \
process.
"""


# ═══════════════════════════════════════════════════════════════════════
# INJURY RISK GOLDEN RESPONSES
# ═══════════════════════════════════════════════════════════════════════

INJURY_RISK_GOLDEN: dict[str, str] = {}

# ── 03: Beginner Male, 45, Returning from Injury ───────────────────

INJURY_RISK_GOLDEN["03_beginner_m45_returning_injury"] = """\
## Injury Risk Assessment — David (Returning from Calf Strain)

### Risk Level: Moderate — Requires Careful Management

While your ACWR of 0.43 technically falls in the "undertraining" category, \
the real risk here is not undertraining — it's what happens next. Your \
chronic load has dropped due to the injury recovery, and any rapid attempt \
to rebuild volume will cause a dangerous ACWR spike.

### Specific Concerns

1. **Declining volume trend**: Your weekly mileage has dropped from a peak \
of 15 km down to 5 km over the last 3 weeks. This is consistent with \
managing the calf strain, but it means your chronic baseline is eroding.
2. **Load variability (CV = 0.21)**: The erratic pattern (0, 5, 8, 12, \
15, 12, 8, 5 km) reflects the injury-recovery cycle, but it means your \
body hasn't had a stable training stimulus to adapt to.
3. **Re-injury risk**: The calf is the most vulnerable tissue right now. \
Returning to 12-15 km/week immediately would spike your ACWR well above \
1.5 and dramatically increase re-injury risk.
4. **The 10% rule applies from current volume, not pre-injury volume**: \
This means increasing from 5 km by no more than ~0.5-1 km per week.

### Recommendations

- **Next week**: 6-7 km total, spread across 3 sessions with rest days \
between each. All running at easy pace or walk/jog intervals.
- **Gradual rebuild**: Increase by no more than 10% per week. Target: \
reach 10 km/week within 4-5 weeks, 15 km/week within 8-10 weeks.
- **Monitor the calf**: Any pain during or after running (beyond normal \
post-run tiredness) warrants a rest day and possible physio review.
- **Do not skip rest days** between running sessions.
- **Add calf-specific strengthening** (eccentric heel drops) on non-running \
days if approved by your physiotherapist.
"""

# ── 04: Beginner Female, 35, Returning from Injury ─────────────────

INJURY_RISK_GOLDEN["04_beginner_f35_returning_injury"] = """\
## Injury Risk Assessment — Maria (Returning from Knee Issue)

### Risk Level: Moderate — Caution Required

Your ACWR of 0.65 is below optimal (the safe range is 0.8-1.3), and the \
downward trend (12 km to 8 km) suggests the knee issue may still be \
limiting your training. A gradual and patient rebuild is essential.

### Specific Concerns

1. **Declining volume**: You reached 15 km/week before dropping back to \
8 km. The downward trajectory needs to stabilise before rebuilding.
2. **Week-to-week inconsistency (CV = 0.15)**: The pattern 0, 3, 6, 10, \
12, 15, 12, 8 km shows initial progress followed by a setback — classic \
injury-return volatility.
3. **ACWR rebound risk**: If you jump back to 15 km next week, your ACWR \
would spike to approximately 1.2-1.3 — borderline. Any further increase \
from there would push into dangerous territory.
4. **Knee loading**: The knee is a weight-bearing joint that accumulates \
stress with running volume and intensity. The initial ramp from 0 to 15 km \
was likely too aggressive (even though it felt manageable), which may have \
caused the subsequent setback.

### Recommendations

- **Stabilise first**: Hold at 8-9 km/week for 2 weeks before increasing. \
The goal is consecutive symptom-free weeks, not rapid volume recovery.
- **Three running days maximum** with rest days between each.
- **All running at easy pace** — no speed work, tempo, or intensity of any kind.
- **Consider a physio assessment** to identify any biomechanical factors \
contributing to the knee issue (hip weakness, IT band tightness, etc.).
- **Strength training**: Include 2 sessions per week focused on glutes, \
quads, and hip stability. Strong hips reduce knee loading significantly.
- **When to add volume**: Only after 2-3 consecutive weeks at the same \
volume with zero knee symptoms. Then increase by 10% per week maximum.
"""

# ── 07: Intermediate Male, 40, Overreaching ────────────────────────

INJURY_RISK_GOLDEN["07_intermediate_m40_overreaching"] = """\
## Injury Risk Assessment — Mark (Overreaching)

### Risk Level: High

Your ACWR of 1.6 places you firmly in the high-risk zone. The data is \
clear and requires immediate action.

### Specific Concerns

1. **60% volume spike**: You went from 30 km to 48 km in a single week. \
The 10% rule (maximum safe weekly increase) would have allowed 33 km. \
You exceeded this by 15 km.
2. **ACWR 1.6**: The research is consistent — ACWR above 1.5 is associated \
with significantly elevated injury risk. At 1.6, you're well into the \
danger zone.
3. **Chronic load context**: Your chronic average is 30 km/week. The 48 km \
week represents 160% of your chronic baseline — your tissues, tendons, \
and bones have not adapted to this level of loading.
4. **Age factor**: At 40, connective tissue recovery is slower than at 25. \
Load spikes are less well-tolerated, and injury recovery takes longer.
5. **Marathon training context**: You have the race in September. A \
training-ending injury now would cost you the entire preparation block.

### Recommendations

- **Immediate deload**: Reduce next week to 16-20 km, all at easy pace. \
This is not optional.
- **No quality sessions** (tempo, intervals, speed work) for the next \
7-10 days.
- **Gradual rebuild**: After the deload, increase by 10% per week. Target \
30-32 km/week within 3 weeks, then resume structured marathon training.
- **Monitor for warning signs**: Persistent soreness, elevated resting \
heart rate (>5 bpm above normal for 3+ days), declining performance, \
sleep disruption, or mood changes.
- **Reframe the narrative**: This deload is not lost training — it's \
protective. The fitness from the 48 km week is already banked. Now let \
your body absorb it.
"""

# ── 08: Intermediate Female, 38, Overreaching ──────────────────────

INJURY_RISK_GOLDEN["08_intermediate_f38_overreaching"] = """\
## Injury Risk Assessment — Lisa (Overreaching)

### Risk Level: High

Your ACWR of 1.51 crosses the high-risk threshold. This demands immediate \
attention.

### Specific Concerns

1. **54% volume spike**: You went from 26 km to 40 km this week. Safe \
weekly increase would have been ~29 km (10% rule). The 40 km week is \
significantly beyond what your body has adapted to.
2. **ACWR 1.51**: Just above the 1.5 danger threshold. Injury risk is \
significantly elevated.
3. **Chronic load of 26.5 km**: Your body is adapted to ~26-28 km/week. \
The 40 km week asked your tissues to handle 151% of their adapted load.
4. **Half marathon training timeline**: Your race is in July — plenty of \
time. An injury now would be far more costly than a planned deload week.

### Recommendations

- **Immediate deload**: Reduce next week to 13-15 km, all at easy pace.
- **Drop all intensity work** for the deload period. Easy running only.
- **3-4 rest days** in the deload week.
- **Gradual rebuild**: After the deload, increase by 10% per week. Aim \
to stabilise at 26-28 km/week for 2 weeks before resuming quality sessions.
- **Self-monitoring checklist**: Each morning, check resting heart rate, \
sleep quality, and energy levels. Any persistent negative trend warrants \
an additional rest day.
- **Prioritise consistency**: After recovery, aim for steady 26-30 km \
weeks rather than fluctuating between 25 and 40.
"""

# ── 11: Advanced Male, 22, Injury Risk ─────────────────────────────

INJURY_RISK_GOLDEN["11_advanced_m22_injury_risk"] = """\
## Injury Risk Assessment — Tyler (Dangerous Loading Pattern)

### Risk Level: High

This is a serious concern. Your ACWR of 1.6, combined with a load \
variability CV of 0.16, creates a compounding risk that requires \
immediate intervention.

### Specific Concerns

1. **82% volume spike**: From 55 km to 100 km in one week. The 10% rule \
would have allowed a maximum of ~60.5 km. You nearly doubled your volume.
2. **ACWR 1.6**: Well above the 1.5 danger threshold.
3. **Erratic loading pattern (CV = 0.16)**: Your 8-week loading has been: \
60, 65, 55, 70, 50, 75, 55, 100 km. The standard deviation across weeks \
is high. This inconsistency is an independent risk factor — your body \
can't establish a stable adaptation when volume oscillates by 20-45 km \
week to week.
4. **Multiple 10% rule violations**: Week 4 (55→70 = +27%), Week 6 \
(50→75 = +50%), Week 8 (55→100 = +82%). This pattern suggests systemic \
issues with load management, not a one-off spike.
5. **Race proximity**: Sub-15 5K in 4 weeks. Arriving injured would waste \
months of training.

### Recommendations

- **Immediate deload to 25-30 km** this week, all easy. This is non-negotiable.
- **Absolute zero intensity work** for the next 7-10 days.
- **After the deload**: Rebuild to ~55-60 km over 2 weeks, then hold steady.
- **Address the root cause**: The erratic loading suggests either a lack of \
planning, inconsistent scheduling, or a tendency to "make up" missed volume \
with big catch-up weeks. All of these are fixable with a structured weekly plan.
- **Consistency commitment**: Aim for a CV below 0.10 going forward. That \
means weekly variation of no more than 5-10 km. If you miss a run, \
accept the lower week rather than overcompensating.
- **Monitor aggressively**: Resting HR, sleep quality, any new or unusual \
pain. At your training volume, your body's margin for error is smaller \
than a recreational runner's.

The fitness is there. Your VDOT of 66.2 supports a sub-15 5K. What's \
needed now is discipline with load management, not more volume.
"""

# ── 12: Advanced Female, 24, Injury Risk ───────────────────────────

INJURY_RISK_GOLDEN["12_advanced_f24_injury_risk"] = """\
## Injury Risk Assessment — Jade (Dangerous Loading Pattern)

### Risk Level: High

Your loading pattern requires immediate correction. The combination of \
a high ACWR and inconsistent week-to-week volume creates compounding risk.

### Specific Concerns

1. **73% volume spike**: From 52 km to 90 km. The 10% rule maximum was \
~57 km. You exceeded it by 33 km.
2. **ACWR 1.59**: Above the 1.5 danger threshold.
3. **Erratic loading (CV = 0.12)**: Your 8-week pattern — 55, 58, 50, 62, \
48, 65, 52, 90 km — shows repeated oscillation. Weeks alternate between \
building and dropping, with this week's massive spike.
4. **Bone stress injury risk**: Female athletes with erratic loading \
patterns and high ACWR spikes are at elevated risk for bone stress injuries. \
This is especially relevant at the volume you're training. Ensure you're \
monitoring for any localised bone pain, particularly in the shins, feet, \
or hips.
5. **Energy availability**: At 90 km/week, caloric needs are substantial. \
Inadequate energy intake at this volume can lead to hormonal disruption, \
reduced bone density, and increased injury risk (RED-S). If you've noticed \
any changes in menstrual regularity, unusual fatigue, or recurring illness, \
please discuss this with a sports medicine professional.

### Recommendations

- **Immediate deload to 22-25 km** this week, all easy pace.
- **No intensity work** for 7-10 days.
- **After the deload**: Rebuild to ~50-55 km over 2 weeks, then hold steady.
- **Commit to consistency**: Target a weekly CV below 0.10. If your \
target volume is 55 km, stay between 50-60 km every week. No exceptions.
- **Energy availability check**: Are you eating enough? This is not about \
weight — it's about fuelling performance and protecting bone health.
- **Race preparation**: Your 10K on April 1 is realistic at your fitness \
level. After the deload and rebuild, a short sharpening phase with one \
tempo session and one interval session per week will be sufficient.
"""


# ═══════════════════════════════════════════════════════════════════════
# RACE READINESS GOLDEN RESPONSES
# ═══════════════════════════════════════════════════════════════════════

RACE_READINESS_GOLDEN: dict[str, str] = {}

# ── 01: Beginner Male, 30, Healthy ──────────────────────────────────

RACE_READINESS_GOLDEN["01_beginner_m30_healthy"] = """\
## Race Readiness Assessment — Alex (5K, goal: 27:00)

### Readiness Score: 7/10 — On Track

You're in a good position for your first sub-27 5K attempt on April 15.

### Strengths
- **Consistent training**: Your ACWR of 1.14 is in the optimal range, and \
you've built steadily from 15 km to 20 km/week over 8 weeks. This shows \
discipline and good load management.
- **Adequate volume for 5K**: At 20 km/week, you're running 4x the race \
distance weekly, which is more than sufficient for 5K preparation.
- **Realistic goal**: Your VDOT of 33.5 predicts a 5K time of approximately \
28:00. A 27:00 target is ambitious but achievable with continued consistent \
training over the next 8 weeks.

### Risks
- **Limited race-specific fitness**: Your training has been predominantly \
easy running. To hit 27:00, you'll need to develop some speed endurance at \
your threshold pace (5:52-6:08/km) and interval pace (5:17-5:31/km).
- **No racing experience**: First race nerves can affect pacing. Practice \
running at goal pace (5:24/km) in training to build confidence.

### Recommendations
- **Weeks 1-5**: Introduce one short tempo effort per week (e.g., 2 x 8 min \
at threshold pace with 2 min recovery). Keep all other running easy.
- **Weeks 6-7**: Include one session of 5K-specific work (e.g., 4 x 3 min \
at 5:20-5:30/km with 2 min jog recovery).
- **Week 8 (race week)**: Taper — reduce volume by 40%, no intensity in the \
last 3 days. Easy 2-3 km shakeout the day before.
- **Race strategy**: Start at 5:30/km for the first km, settle into 5:24/km, \
then give what you have in the final km.
"""

# ── 02: Beginner Female, 28, Healthy ────────────────────────────────

RACE_READINESS_GOLDEN["02_beginner_f28_healthy"] = """\
## Race Readiness Assessment — Sarah (5K, goal: 29:00)

### Readiness Score: 7/10 — On Track

With 10 weeks until your first 5K on May 1, you have plenty of time to \
prepare well.

### Strengths
- **Building consistently**: ACWR 1.13 is optimal. Your volume has increased \
steadily from 12 km to 17 km/week — textbook progression.
- **Volume is sufficient**: 17 km/week is more than adequate for 5K readiness.
- **Achievable goal**: Your VDOT of 30.2 predicts a 5K around 30:30. A 29:00 \
target is a stretch but realistic with focused preparation.

### Risks
- **Goal is slightly above current fitness**: You'll need modest improvement \
over the next 10 weeks to bridge the ~90-second gap.
- **No race experience**: First race logistics and pacing will be new.

### Recommendations
- **Weeks 1-6**: Continue building base. Introduce one tempo effort per week \
(10-15 min at threshold pace, 6:22-6:40/km).
- **Weeks 7-9**: Add one short speed session (e.g., 5 x 2 min at 5:50/km \
with 2 min jog recovery).
- **Week 10 (race week)**: Taper — reduce volume by 40%. Easy shakeout day before.
- **Race strategy**: Start conservatively at 5:55/km, settle into 5:48/km. \
The goal is to finish feeling strong in your first race.
"""

# ── 03: Beginner Male, 45, Returning from Injury ───────────────────

RACE_READINESS_GOLDEN["03_beginner_m45_returning_injury"] = """\
## Race Readiness Assessment — David (10K, goal: 1:10:00)

### Readiness Score: 3/10 — Not Ready

You are not ready to race, and that's OK. Your race isn't until August 1, \
which gives you over 5 months to rebuild properly.

### Strengths
- **Smart goal timeline**: Choosing an August race gives you ample time to \
rebuild from the calf strain without rushing.
- **Realistic target**: A 1:10:00 10K (7:00/km pace) is achievable at your \
fitness level once you rebuild your base.

### Risks
- **Declining volume**: Your weekly mileage has dropped from 15 km to 5 km \
over the last 3 weeks. Your ACWR of 0.43 confirms you're significantly \
below your chronic training level.
- **Calf strain recovery**: The injury is the primary limiter. Rushing back \
risks re-injury and a longer total time away from running.
- **Insufficient base for 10K**: At 5 km/week, you're running less than \
the race distance in an entire week.

### Recommendations
- **Priority 1**: Rebuild to 15 km/week over the next 8-10 weeks (gradual \
10% increases from current 5 km).
- **Priority 2**: Once stable at 15 km/week for 3-4 consecutive weeks, begin \
adding a long run that reaches 8-10 km by June.
- **Priority 3**: Race-specific preparation (6 weeks before race) — practice \
running at 7:00/km pace for progressively longer intervals.
- **Do not race before**: You can comfortably run 10 km continuously at easy \
pace with no calf symptoms. This is the minimum bar for readiness.
"""

# ── 04: Beginner Female, 35, Returning from Injury ─────────────────

RACE_READINESS_GOLDEN["04_beginner_f35_returning_injury"] = """\
## Race Readiness Assessment — Maria (5K, goal: 32:00)

### Readiness Score: 3/10 — Not Ready

Your current training state does not support racing, but with 4.5 months \
until your July 1 race, there's plenty of time.

### Strengths
- **Achievable goal**: Your VDOT of 29.6 supports a 5K around 31:00. A \
32:00 target is realistic once you rebuild your base.
- **Time on your side**: July 1 is far enough away for a full recovery and \
preparation cycle.

### Risks
- **Volume declining**: From 15 km to 8 km/week. Your ACWR of 0.65 is in \
the undertraining zone. Your body is losing fitness, not building it.
- **Knee issue**: The injury caused the initial setback and the recent \
decline suggests it may not be fully resolved.
- **Insufficient base**: At 8 km/week, you need to more than double your \
volume and sustain it before racing.

### Recommendations
- **Phase 1 (weeks 1-4)**: Stabilise at 8-10 km/week. Run 3 days with rest \
days between. All easy pace. Zero symptoms required.
- **Phase 2 (weeks 5-10)**: Build to 15-18 km/week with 10% weekly increases. \
Include one run of 5+ km to prove race-distance readiness.
- **Phase 3 (weeks 11-16)**: Hold at 18-20 km/week. Add one tempo effort per \
week. Run a practice 5K at easy pace.
- **Race readiness checkpoint**: By mid-June, you should be able to run 5 km \
continuously at easy pace with zero knee symptoms. If not, defer the race.
"""

# ── 05: Intermediate Male, 32, Healthy ─────────────────────────────

RACE_READINESS_GOLDEN["05_intermediate_m32_healthy"] = """\
## Race Readiness Assessment — James (Half Marathon, goal: 1:35:00)

### Readiness Score: 8/10 — Strong

You're in excellent shape for your half marathon PB on May 15.

### Strengths
- **Consistent volume**: 40-46 km/week with an optimal ACWR of 1.06. \
This is a solid base for half marathon preparation.
- **Goal is realistic**: Your VDOT of 47.7 predicts a half marathon time of \
1:35:19 — your 1:35:00 target is right at your current fitness level.
- **Training maturity**: 2 years of consistent running with steady \
progression. Your body is well-adapted to the training load.

### Risks
- **Minimal margin**: The predicted time (1:35:19) and goal (1:35:00) are \
nearly identical. A bad day or tactical error could mean missing the target.
- **Volume ceiling**: You may benefit from one block at 48-52 km to add a \
small fitness buffer, if your body tolerates it.

### Recommendations
- **Weeks 1-6**: Peak training block. Maintain 44-48 km/week. Key sessions: \
1 tempo run at threshold pace (4:25-4:37/km), 1 long run building to 18-20 km \
with the last 4-5 km at marathon pace (4:32-4:54/km).
- **Weeks 7-8**: Begin taper. Reduce to 35 km (week 7) then 25 km (race week).
- **Race execution**: Start at 4:32/km (slightly conservative). Settle into \
4:30/km by km 5. Assess at halfway — if feeling strong, hold pace. If not, \
maintain 4:32/km for a safe PB.
- **Fuelling**: Practice race-day nutrition in long runs. Gel or sports drink \
every 30-40 minutes during the race.
"""

# ── 06: Intermediate Female, 29, Healthy ───────────────────────────

RACE_READINESS_GOLDEN["06_intermediate_f29_healthy"] = """\
## Race Readiness Assessment — Emma (Half Marathon, goal: 1:42:00)

### Readiness Score: 8/10 — Strong

Your preparation for the June 1 half marathon is going well.

### Strengths
- **Consistent and progressing**: ACWR 1.07 is optimal. Volume has built \
from 35 to 40 km/week. This is textbook preparation.
- **Goal matches fitness**: Your VDOT of 44.1 predicts exactly 1:42:00 for \
a half marathon. The goal is realistic.
- **Ample time**: With 15 weeks until race day, you have time for a full \
training block plus proper taper.

### Risks
- **Goal exactly at predicted fitness**: No margin for error. Consider \
whether a slight volume increase (to 42-44 km) could provide a buffer.
- **Second race experience**: Less racing experience means pacing and \
race-day execution are still developing skills.

### Recommendations
- **Weeks 1-9**: Peak training. Build to 42-44 km/week. Include 1 tempo \
session at threshold pace (4:42-4:56/km) and 1 long run building to 18 km \
with race-pace segments.
- **Weeks 10-12**: Maintain peak volume. Add race-specific sessions \
(e.g., 3 x 3 km at 4:51/km with 3 min recovery).
- **Weeks 13-15**: Taper — 38 km, 30 km, then 20 km (race week).
- **Race strategy**: Start at 4:52/km, settle into 4:51/km. Even pacing \
is the priority for a PB.
"""

# ── 07: Intermediate Male, 40, Overreaching ────────────────────────

RACE_READINESS_GOLDEN["07_intermediate_m40_overreaching"] = """\
## Race Readiness Assessment — Mark (Marathon, goal: 3:30:00)

### Readiness Score: 4/10 — Not Ready (Load Issue)

Your marathon isn't until September, which is fortunate — because your \
current training state needs correction before race preparation can begin.

### Current Concern
Your ACWR of 1.6 is in the high-risk zone. You spiked from 30 km to \
48 km this week — a 60% increase. This is a load management issue, not \
a fitness issue. Racing in this state would be inadvisable.

### Strengths
- **Fitness base exists**: Your VDOT of 45.9 predicts a marathon time of \
3:24:51. A 3:30 goal is within reach once you're properly prepared.
- **September timeline**: 7+ months is more than enough time for a full \
marathon build, including a proper base, build, peak, and taper.

### Risks
- **Injury risk is the immediate concern**: ACWR 1.6 means your body is \
under significantly more stress than it's adapted to. Racing or hard \
training now risks a training-ending injury.
- **Volume inconsistency**: The spike from 30 to 48 km suggests the \
training is not following a structured plan.

### Recommendations
- **Immediate**: Deload to 16-20 km this week. Easy running only. This is \
non-negotiable before any race-focused training begins.
- **Weeks 2-4**: Rebuild to 30-32 km/week (your chronic average).
- **Weeks 5-20**: Structured marathon build following a periodised plan. \
Target peak volume of 55-65 km/week.
- **Taper**: 3-week taper before September 20.
- **Bottom line**: Fix the load management now. The marathon fitness will come.
"""

# ── 08: Intermediate Female, 38, Overreaching ──────────────────────

RACE_READINESS_GOLDEN["08_intermediate_f38_overreaching"] = """\
## Race Readiness Assessment — Lisa (Half Marathon, goal: 1:48:00)

### Readiness Score: 4/10 — Not Ready (Load Issue)

Your half marathon on July 15 gives you 5 months, but your current \
training state requires immediate attention.

### Current Concern
Your ACWR of 1.51 has crossed the high-risk threshold. You went from \
26 km to 40 km this week — a 54% spike. This puts you at elevated risk \
for injury and must be addressed before race preparation can continue.

### Strengths
- **Goal is achievable**: Your VDOT of 42.0 predicts a half marathon \
time of 1:46:22. A 1:48:00 target is comfortably within reach.
- **Adequate timeline**: 5 months allows for recovery, rebuild, and a \
full race preparation cycle.

### Risks
- **ACWR 1.51**: Injury risk is significantly elevated. Training through \
this spike increases the chance of a setback that could cost you the race.
- **Volume inconsistency**: The jump from 26 to 40 km needs to be addressed \
with structured, gradual progression going forward.

### Recommendations
- **Week 1**: Deload to 13-15 km. Easy running only. 3-4 rest days.
- **Weeks 2-4**: Rebuild to 26-28 km/week (chronic average).
- **Weeks 5-16**: Structured half marathon build. Target peak of 38-42 km/week.
- **Weeks 17-19**: Taper — 2 weeks of progressive volume reduction.
- **Key lesson**: Consistency at 28-32 km/week beats alternating between \
25 and 40. Build gradually.
"""

# ── 09: Advanced Male, 25, Healthy ─────────────────────────────────

RACE_READINESS_GOLDEN["09_advanced_m25_healthy"] = """\
## Race Readiness Assessment — Ryan (Marathon, goal: 2:40:00)

### Readiness Score: 8/10 — Strong

You're well-positioned for your marathon PB on April 20.

### Strengths
- **Elite-level volume**: 80-92 km/week with an optimal ACWR of 1.06. \
This is a robust, well-managed training load.
- **Goal matches fitness**: VDOT 61.8 predicts a marathon time of 2:39:19. \
Your 2:40 target is at your current fitness level.
- **Training maturity**: The consistency of your weekly loading (CV very low) \
indicates excellent training discipline.

### Risks
- **Tight margin**: Predicted time (2:39:19) is only 41 seconds under your \
goal. Any pacing error, fuelling issue, or bad weather could push you over.
- **Race execution at this level**: A 2:40 marathon requires disciplined \
pacing at 3:47/km for 42.2 km. There's very little room for error.

### Recommendations
- **Weeks 1-4**: Peak training block. Maintain 88-92 km/week. Key sessions: \
marathon pace long run (28-32 km with 16-20 km at 3:47/km), threshold \
session (6-8 km at 3:34-3:45/km).
- **Weeks 5-6**: Sharpen. Reduce to 75-80 km. Add one session of race-pace \
intervals (e.g., 6 x 2 km at 3:47/km with 90 sec jog).
- **Weeks 7-8**: Taper. 60 km, then 35 km (race week). Last hard session \
10 days out. Final shakeout 2 days before.
- **Race strategy**: First 10 km at 3:49/km (conservative). Settle into \
3:47/km from 10-30 km. Assess at 30 km — if you have it, hold. If not, \
2:42-2:43 is still an excellent result.
- **Fuelling**: Caffeine + carb gel every 30 min from km 10. Practice this \
in every long run.
"""

# ── 10: Advanced Female, 27, Healthy ───────────────────────────────

RACE_READINESS_GOLDEN["10_advanced_f27_healthy"] = """\
## Race Readiness Assessment — Olivia (Half Marathon, goal: 1:18:00)

### Readiness Score: 8/10 — Strong

You're tracking well for your half marathon PB on May 10.

### Strengths
- **High-volume consistency**: 70-82 km/week with ACWR 1.06. Excellent \
training discipline.
- **Goal is realistic**: VDOT 57.8 predicts a half marathon time of 1:20:43. \
Your 1:18 target is ambitious but achievable with a strong sharpening phase.
- **Training maturity**: The low variability in your weekly loading indicates \
you can handle high volume safely.

### Risks
- **2:43 gap to close**: The predicted time (1:20:43) is 2:43 slower than \
goal (1:18:00). You'll need meaningful fitness improvement over the next 12 \
weeks to bridge this.
- **Race execution**: At sub-1:18 pace (3:42/km), pacing discipline is critical.

### Recommendations
- **Weeks 1-6**: Peak training. Maintain 78-82 km/week. Key sessions: \
threshold work (5-6 km at 3:46-3:57/km), long run with race-pace finish \
(18-20 km with final 6-8 km at 3:42/km).
- **Weeks 7-9**: Sharpen. Maintain volume but increase session quality. \
Add interval work (6 x 1600 m at 3:24-3:33/km with 90 sec recovery).
- **Weeks 10-12**: Taper. 65 km, 50 km, 30 km. Last hard session 10 days out.
- **Race execution**: First 5 km at 3:44/km (2 sec/km conservative). Settle \
into 3:42/km from 5-15 km. Final 6 km — race instinct.
"""

# ── 11: Advanced Male, 22, Injury Risk ─────────────────────────────

RACE_READINESS_GOLDEN["11_advanced_m22_injury_risk"] = """\
## Race Readiness Assessment — Tyler (5K, goal: sub-15:00)

### Readiness Score: 3/10 — Not Ready (Dangerous Loading)

You have the fitness for sub-15. Your VDOT of 66.2 supports it. But \
fitness is not the same as readiness, and right now, you are not ready \
to race.

### The Problem
Your ACWR of 1.6 and erratic loading pattern (CV 0.16) create a \
compounding risk that makes racing inadvisable:
- You spiked from 55 km to 100 km this week — an 82% increase.
- Your 8-week loading (60, 65, 55, 70, 50, 75, 55, 100 km) shows \
wild inconsistency.
- Racing on this accumulated fatigue increases both injury risk and \
the likelihood of underperformance.

### Strengths
- **The fitness is there**: VDOT 66.2 predicts a 5K time of approximately \
15:05-15:10. Sub-15 is within reach with proper preparation.
- **Race is 4 weeks away**: Enough time for a deload, stabilisation, and \
short sharpening phase — IF you act now.

### Recommendations
- **This week**: Deload to 25-30 km. Easy running only. Zero intensity.
- **Week 2**: Rebuild to 50-55 km. Introduce one moderate tempo (20 min \
at threshold).
- **Week 3**: 55-60 km. Add one 5K-specific session (5 x 1000 m at \
2:56-3:00/km with 2 min recovery).
- **Week 4 (race week)**: 30-35 km. One short sharpener 4 days out \
(3 x 800 m at race pace). Easy the rest of the week.
- **If you skip the deload**: DNS is better than a soft-tissue injury \
that costs you the entire spring season.
"""

# ── 12: Advanced Female, 24, Injury Risk ───────────────────────────

RACE_READINESS_GOLDEN["12_advanced_f24_injury_risk"] = """\
## Race Readiness Assessment — Jade (10K, goal: sub-35:00)

### Readiness Score: 3/10 — Not Ready (Dangerous Loading)

Your fitness supports the goal, but your current training state makes \
racing inadvisable.

### The Problem
Your ACWR of 1.59 and erratic loading (CV 0.12) are the immediate \
concerns. The risk of racing in this state is twofold:
1. **Injury risk**: 73% volume spike (52 to 90 km) means your tissues \
are under far more stress than they've adapted to.
2. **Performance risk**: Accumulated fatigue from the spike will likely \
compromise your race result anyway.

### Strengths
- **Fitness is strong**: VDOT 61.2 predicts a 10K time of 34:46. Sub-35 \
is achievable at your fitness level.
- **Race is 6 weeks away**: Enough time for recovery + sharpening.

### Risks
- **Bone stress injury**: Female athletes with erratic loading and high \
ACWR spikes are at elevated risk. Monitor for any localised bone pain.
- **Energy availability**: At 90 km/week, caloric needs are substantial. \
Ensure energy intake matches expenditure.

### Recommendations
- **Week 1**: Deload to 22-25 km. Easy only. No intensity.
- **Weeks 2-3**: Rebuild to 50-55 km. Add one tempo (20 min at 3:36-3:47/km).
- **Week 4-5**: Hold at 55 km. Add one 10K-specific session (5 x 2000 m \
at 3:28-3:33/km with 90 sec recovery).
- **Week 6 (race week)**: Taper to 30 km. One sharpener 4 days out.
- **Commitment**: After the race, establish consistent 50-55 km weeks \
(CV below 0.10) before any future volume increases.
"""

# ── 13: Senior Male, 62, Beginner ──────────────────────────────────

RACE_READINESS_GOLDEN["13_senior_m62_beginner"] = """\
## Race Readiness Assessment — Robert (5K, goal: finish running)

### Readiness Score: 7/10 — On Track

Your first 5K on June 15 is a realistic and achievable goal. You're \
doing the right things.

### Strengths
- **Consistent training**: ACWR 1.02 is optimal. Your volume has been \
steady at 10-14 km/week for 4 months. This consistency is the single \
most important predictor of readiness.
- **Volume is adequate for 5K**: At 13 km/week, you're running over 2x \
the race distance weekly. For a 5K, this is sufficient.
- **Manageable goal**: Your goal is to finish running the whole thing — \
this is a healthy, realistic target that sets you up for long-term success.

### Risks
- **Longest single run**: Make sure you've run 5 km continuously at least \
once before race day. If your longest run is currently shorter, build up \
to it over the next few weeks.
- **Race-day logistics**: First race can be overwhelming — start position, \
pacing, other runners. A plan for race day will help.

### Recommendations
- **Weeks 1-8**: Continue current approach. Ensure one run per week reaches \
5 km by week 6 (build gradually from your current longest run).
- **Week 9 (race week)**: Reduce to 8-9 km total. Easy 2 km shakeout \
2 days before. Rest the day before.
- **Race strategy**: Start at the back of the pack. Run at your easy pace \
(8:42-10:17/km). Walking breaks are completely fine if needed. The goal \
is to finish, enjoy it, and come back wanting more.
- **Recovery**: Take 2-3 easy days after the race before resuming normal training.
- **Strength training**: If not already included, add 1-2 sessions per week \
focusing on leg strength and balance. This supports running and overall health.
"""

# ── 14: Senior Female, 58, Beginner ────────────────────────────────

RACE_READINESS_GOLDEN["14_senior_f58_beginner"] = """\
## Race Readiness Assessment — Patricia (5K, goal: finish, walking breaks OK)

### Readiness Score: 7/10 — On Track

Your July 1 race is very achievable with your current training approach.

### Strengths
- **Excellent consistency**: ACWR 1.02, steady volume at 8-12 km/week for \
3 months. You're doing the most important thing — showing up regularly.
- **Realistic goal**: Finishing a 5K with walking breaks is entirely within \
your current ability. This is a smart first-race goal.
- **Strong foundation**: 3 months of regular running means your body has \
adapted to the training stimulus.

### Risks
- **Joint health**: At your volume and pace, joint stress is low, but \
continue to monitor for any knee or hip discomfort, especially in the \
weeks with longer runs.
- **Confidence**: Running your first race at 58 can feel daunting. Know \
that your consistent training has prepared you well.

### Recommendations
- **Weeks 1-10**: Continue current approach. Build one run per week to \
5 km (with walking breaks as needed). The other runs stay short and easy.
- **Weeks 11-13**: Practice the race distance. Run/walk 5 km at least twice. \
Use a pattern like run 4 min, walk 1 min — or whatever feels comfortable.
- **Week 14 (race week)**: Easy week. Short 2 km shakeout. Rest day before race.
- **Race-day plan**: Run/walk from the start. Don't get caught up in other \
runners' pace. Start conservatively and finish strong.
- **Recovery**: Walk gently for 10 min after finishing. Easy week following the race.
"""

# ── 15: Teen Male, 17, Talent ──────────────────────────────────────

RACE_READINESS_GOLDEN["15_teen_m17_talent"] = """\
## Race Readiness Assessment — Ethan (5K, goal: 17:00, state qualifier)

### Readiness Score: 7/10 — Approaching Readiness

Your state championship qualifier on April 10 is within reach, but the \
recent volume jump needs attention.

### Strengths
- **Strong fitness**: VDOT 56.3 suggests you can run approximately 17:30 \
for 5K at current fitness. With good preparation and race execution, 17:00 \
is achievable.
- **Improving trajectory**: Volume has been building steadily, and your \
ACWR of 1.2 is still within the optimal range (though at the upper end).

### Concerns
- **20% volume jump**: From 40 to 48 km this week is a 20% increase. For \
a developing athlete, this is aggressive. Stabilise at this level or pull \
back slightly before increasing again.
- **Race in 8 weeks**: You have time, but the priority is consistent \
training, not peak volume.

### Recommendations — Development Focus
This race matters, but it's one race in a long career. The goal is to \
perform well while continuing to develop as a runner.

- **Weeks 1-3**: Stabilise at 45-48 km/week. No further volume increases. \
1 tempo session (20 min at 3:51-4:03/km), 1 interval session (6 x 800 m \
at 3:28-3:37/km with equal jog recovery).
- **Weeks 4-5**: Hold volume. Sharpen with race-specific work (3 x 1600 m \
at 3:24/km with 2 min recovery).
- **Week 6**: Reduce to 38 km. One moderate session only.
- **Week 7**: Reduce to 30 km. Short sharpener 4 days out (4 x 400 m at \
race pace).
- **Week 8 (race week)**: 15-20 km total. Easy shakeout 2 days before. Rest day before.
- **Race strategy**: Start at 3:25/km for the first 800 m. Settle into \
3:24/km. Final km — race hard.
- **Important**: Sleep 8-9 hours. Eat well. This matters as much as the \
training at your age.
"""

# ── 16: Teen Female, 16, Talent ────────────────────────────────────

RACE_READINESS_GOLDEN["16_teen_f16_talent"] = """\
## Race Readiness Assessment — Sophia (5K, goal: 18:00, state qualifier)

### Readiness Score: 7/10 — Approaching Readiness

Your state championship qualifier on April 10 is achievable with smart \
preparation over the next 8 weeks.

### Strengths
- **Strong fitness**: VDOT 51.3 suggests a 5K time around 19:00-19:15. \
With continued development, 18:00 is a stretch goal that could come together.
- **Building well**: ACWR 1.2 is at the upper end of optimal, showing \
good training progression.

### Concerns
- **20% volume increase**: From 35 to 42 km this week. This is aggressive \
for a developing athlete. Stabilise before increasing further.
- **Goal is ambitious**: 18:00 vs ~19:15 predicted is a meaningful gap. \
This doesn't mean it's impossible, but approach it as a development target \
rather than a must-hit number.

### Recommendations — Development Focus
- **Weeks 1-3**: Stabilise at 40-42 km/week. 1 tempo (15-20 min at \
4:09-4:22/km), 1 interval session (5 x 800 m at 3:45-3:54/km with equal \
jog recovery). Everything else easy.
- **Weeks 4-5**: Hold volume. Race-specific sharpening (3 x 1200 m at \
3:36/km with 2 min recovery).
- **Weeks 6-7**: Taper. 35 km, then 28 km.
- **Week 8 (race week)**: 15-18 km. Short sharpener 4 days out. Rest before.
- **Race plan**: Start at 3:38/km. Settle into 3:36/km. Final km — race \
with whatever you have.
- **Bigger picture**: Whether you run 18:00 or 18:30, this is one data \
point in a long development arc. The process matters more than this single \
result.
- **Take care of yourself**: Sleep 8-9 hours. Eat enough to fuel your \
training and development. If you notice unusual fatigue, missed periods, \
or recurring illness, talk to a trusted adult or sports medicine professional.
"""
