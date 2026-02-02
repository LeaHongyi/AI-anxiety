# Intervention Library (MVP) 干预库字段说明 + 每个干预的设计原则

## Purpose
Provide **micro-actions** (<= 10 minutes) that restore control and reduce J-anxiety.
Actions are selected by:
- neuroticism_band (low/mid/high)
- J_driver (job_loss/value_threat/skill_erosion)

## Design Rules
1) Time-bounded: <= 10 min (high neuroticism: <= 5 min)
2) Success = completion, not mastery
3) No job-market predictions
4) Avoid “you must” language, prefer “try”
5) End with a concrete artifact (a sentence, a list, a boundary rule, etc.)

## Data Structure
See: `src/interventions/library.json`

Fields:
- id: unique string
- driver: job_loss | value_threat | skill_erosion
- neuroticism_band: low | mid | high
- title: short
- goal: 1 sentence
- time_minutes: number
- steps: array of short step strings
- success_criteria: 1 sentence
- fallback_if_stuck: 1 sentence
- tags: array

## MVP Coverage
Start with 9 interventions (3 drivers x 3 bands).
Later extend to more contexts (role-based).
