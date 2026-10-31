"""Golden coaching responses — curated correct advice for each profile.

Each response embodies the methodology, tool outputs, and evidence-based guidelines
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
