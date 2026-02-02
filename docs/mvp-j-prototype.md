# MVP Prototype (J Dimension): Job Replacement Anxiety 产品原型（页面、流程、成功标准、路由逻辑）做 UI 时补截图与文案

## 1. Scope
This MVP targets **Job Replacement Anxiety (J)** as defined in the AIA conceptual model:
- Fear that AI may replace jobs/humans
- Fear of dependency and loss of reasoning skills
- Fear that AI will make people lazier / overly reliant

**Non-goals** (explicit):
- Not career counseling
- Not mental health diagnosis/therapy
- Not prediction about “which jobs will be replaced”

## 2. Target User
People who experience persistent worry like:
- “AI will replace me / my role”
- “My work will become worthless”
- “If I use AI, I’ll lose my skills”

## 3. MVP Success Criteria (per session)
A single session is successful if:
1) User completes **one micro-action (<= 10 min)**
2) Self-rated J-anxiety (0–10) decreases by **>= 1**
3) User can state a stable framing: “AI in my work is mainly a ____ (tool / collaborator / accelerator)”

## 4. Core Personalization Variables
### 4.1 Neuroticism (N) band
- low / mid / high (short-form 6 items, Likert 1–5)

### 4.2 J anxiety intensity + driver
- J intensity: short-form 4 items, Likert 1–5 -> mapped to 0–10
- J driver (user picks one):
  - job_loss: fear the role disappears
  - value_threat: fear “I become irrelevant”
  - skill_erosion: fear “I become dependent / lose reasoning skills”

## 5. MVP User Flow (3 screens)

### Screen A — Assessment
Goal: capture minimal data for personalization.
Inputs:
- N short-form (6 items)
- J short-form (4 items)
- Optional: role (free text)

Outputs (internal):
- neuroticism_band
- J_score, J_intensity_0_10

### Screen B — Reflection Chat (2–4 turns)
Goal: build psychological safety + identify main driver.
Rules:
- no job-market predictions
- mirror user language
- name the fear (J) in plain language
- ask user to pick the strongest driver

Output (internal):
- J_driver
- baseline J_intensity_0_10 (confirm)

### Screen C — Action Plan (personalized micro-action)
Goal: restore control + progress.
Show:
- 2 micro-action choices (<= 10 min)
- steps
- “done” button
- post-check: J_intensity_0_10_after

## 6. Personalization Logic (Routing)
Inputs:
- neuroticism_band (low/mid/high)
- J_driver (job_loss/value_threat/skill_erosion)

Output:
- intervention_id (from `src/interventions/library.json`)
- conversation style prompt (from `src/prompts/{band}.md`)

## 7. Safety & Boundaries
See: `docs/safety-and-scope.md`
