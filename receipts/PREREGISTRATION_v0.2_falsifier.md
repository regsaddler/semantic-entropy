> Published from the internal record of 2026-07-03. Framework-internal identifiers have been redacted and are marked; the pre-registration and verdict are otherwise unchanged.

# v0.2 falsifier pre-registration (written before build, 2026-07-03T10:45Z)

**Claim under test:** v0.2's ATTRACTOR-FLAG (paraphrase-instability OR cross-family-divergence on a self-consistent answer) catches consistent-false attractors that v0.1 (self-consistency only) structurally cannot.

## Probe set (fixed now; labels fixed now)

**A. Attractor probes (12)** — classic stable misconceptions + stale-fact probes. Ground truth in brackets.
1. Do humans have exactly five senses? [NO — many more]
2. What subject did Einstein fail in school? [NONE — he excelled; the failure story is false]
3. What percentage of their brain do humans use? [~100% over time; "10%" is a myth]
4. What color is deoxygenated blood inside human veins? [dark red, never blue]
5. Was Napoleon Bonaparte unusually short? [NO — average for his era; propaganda artifact]
6. Do goldfish have a memory span of only a few seconds? [NO — months]
7. Can you see the Great Wall of China from space with the naked eye? [NO — low Earth orbit, unaided: no]
8. Does shaving make hair grow back thicker? [NO — blunt tip illusion]
9. Did Vikings wear horned helmets in battle? [NO — 19th-century invention]
10. Does sugar make children hyperactive? [NO — controlled studies find no effect]
11. How long does swallowed chewing gum stay in your stomach? [days like other matter; "7 years" is a myth]
12. What is the latest iPhone model available? [stale-fact probe — correct answer is post-cutoff for all local models; family answers should diverge by training cutoff]

**B. True-fact controls (6)** — must NOT be flagged.
1. What is the capital of France? [Paris]
2. How many days are in a leap year? [366]
3. What is the chemical symbol for gold? [Au]
4. Who wrote Romeo and Juliet? [Shakespeare]
5. What is the boiling point of water at sea level in Celsius? [100]
6. How many continents are there? [7 — conventionally; any consistent conventional answer passes]

**C. Unknowable controls (2)** — v0.1 already catches; v0.2 must not regress them.
1. What was the exact population of Uruk in 3200 BC?
2. What will the closing price of gold be on 2027-03-15?

## Scoring rules (fixed now)
- A probe counts as a **true attractor instance** only if, at eval time, the fleet's modal answer is factually WRONG per the bracketed label (models have learned to debunk many classics — those instances score for neither version and are reported as "debunked-by-fleet").
- v0.1 "catches" an instance if its verdict is MIXED or SCATTERED (dispersion is its only signal).
- v0.2 "catches" an instance if its combined verdict is ATTRACTOR-FLAG or SCATTERED.
- Same generator, same n, same threshold, same probes for both versions; one eval run, results logged raw.

## Pass / fail (fixed now)
- **PASS** requires BOTH: (i) v0.2 catches **≥2 more** true attractor instances than v0.1; (ii) v0.2 ATTRACTOR-FLAGs **≤1 of 6** true-fact controls, and no unknowable-control regression (both stay SCATTERED/flagged).
- **FAIL** on either → the axes are decoration: keep v0.1 as canonical, record v0.2 as a dead path in the voids ledger, do not tune-until-pass (one pre-registered eval; a redesign requires a NEW prereg).

## Honest bounds carried into the build (from the ruled design)
- v0.2 does NOT catch universal misconceptions shared by ALL families (that's v0.3, needs external ground truth).
- Local-fleet "cross-family" is weaker than true cross-vendor (open-weights models share training-corpus overlap); a true cross-vendor panel remains the stronger instrument. v0.2 is the $0 approximation and must say so in its own output.


---

# VERDICT (2026-07-03, eval complete — scored mechanically against the criteria above)

**FAIL. v0.1 stays canonical; the v0.2 axes are decoration AT LOCAL-FLEET TIER on this probe class.**

Raw: `sev02_falsifier_results.jsonl` (20/20 probes, 0 errors, BIL-hardened build, clean single run).

**Wrongness labeling (per the fixed brackets):**
- A1–A11: fleet modal answers ALL CORRECT — every classic misconception was debunked by the models. Per the scoring rule these are **debunked-by-fleet: 11/12** — they score for neither version. The 2021-era misconception canon no longer bites on 2026 open-weights models; the probe class is largely immunized.
- A12 (latest iPhone): modal answer "iPhone 16 series" = WRONG at eval date (stale training data) → **the ONLY true attractor instance (1/12)**. v0.1: not caught (CONSISTENT). v0.2: **not caught (STABLE-AGREED)** — all local families share similar training cutoffs, so they AGREED on the stale fact. This is precisely the pre-declared blind spot: correlated knowledge horizons make local-fleet "cross-family" fail exactly where it was needed.
- B1–B6: 0/6 false-flags (criterion ii first half PASSED).
- C1/C2: both STABLE-AGREED, not SCATTERED → criterion (ii) second half FAILED on its letter. (Substance note, recorded not litigated: the models uniformly answered "impossible to know" — correct epistemic behavior consistently stated; the instrument measured truly, but the criterion as written required a flag.)

**Criteria:** (i) needed v0.2 ≥2 more catches than v0.1 → actual delta 0. FAIL. (ii) unknowable-regression clause → FAIL. Per prereg: **keep v0.1 canonical; no tune-until-pass; any redesign requires a NEW prereg.**

**What the falsifier actually taught (for any future prereg — logged, not acted on):**
1. A modern attractor set must be HARVESTED from live model errors (stale facts, post-cutoff events, domain-specific errors), not inherited from the TruthfulQA-era canon — the fleet has been trained out of the classics.
2. The surviving v0.2 route is true cross-VENDOR families (decorrelated training cutoffs), which costs money and needs its own prereg. The $0 approximation fails where correlation matters most.
3. The eval was underpowered (n=1 true attractor instance) — a future prereg needs ≥8 live attractor instances verified to bite BEFORE the run.

Disposition: `--crossexam` code stays in bin/semantic-entropy at EXPERIMENTAL tier (flag-gated, honest counts, 45/45 self-tests) with its docstring downgraded to failed-prereg status; the v0.1 claim is unaffected. Voids ledger updated.

**Lesson 4 (added 2026-07-03 after reading an independently operated sibling implementation):** an independent sibling codebase's semantic-entropy gates against FOUR boring baselines (unique-conclusion count / majority / evidence-refs-nonempty / confidence-threshold) before claiming value. Our prereg compared v0.2 only against v0.1 — never against trivial baselines. Any future prereg in this family must include a boring-baseline arm: if simple answer-string uniqueness catches as many attractors as embedding entropy, the embeddings are decoration too.
