# Measurement Spec (MVP) 量表条目、评分规则、分档阈值、映射方式（可直接用于实现）

## 1) Neuroticism (N) Short Form — 6 items
Scale: 1 (strongly disagree) — 5 (strongly agree)

N1. When I face uncertain new technologies, I feel tense.
N2. I often worry I can’t keep up with change.
N3. When technology fails, I stay upset for a long time.
N4. I tend to overthink potential negative outcomes.
N5. With complex systems, I prefer avoiding rather than trying.
N6. I find it hard to ignore thoughts about an unfavorable future.

### Scoring
N_total = sum(N1..N6) range 6–30

### Banding (MVP thresholds)
- low: 6–14
- mid: 15–22
- high: 23–30

> Note: This is **not** a clinical diagnosis. Used only for personalization style.

## 2) Job Replacement Anxiety (J) Short Form — 4 items
Scale: 1 (strongly disagree) — 5 (strongly agree)

J1. I am afraid that AI may replace humans in work.
J2. I am afraid AI will replace someone’s job (including roles like mine).
J3. I worry that using AI makes people dependent and weakens reasoning skills.
J4. I worry that AI will make us lazier / overly reliant.

### Scoring
J_total = sum(J1..J4) range 4–20

### Mapping to 0–10 intensity
J_intensity_0_10 = round((J_total - 4) / 16 * 10)

Examples:
- J_total=4 -> 0
- J_total=12 -> round(8/16*10)=5
- J_total=20 -> 10

## 3) J Driver (user-selected)
Ask user:
“Which part feels strongest right now?”

- job_loss: “I fear my role will disappear.”
- value_threat: “I fear I’ll become irrelevant / not needed.”
- skill_erosion: “I fear I’ll lose my skills / become dependent.”

Store as `J_driver`.
