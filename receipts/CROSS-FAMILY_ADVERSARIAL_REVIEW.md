# Codex (GPT-5.5) — semantic-entropy adversarial attack, 2026-07-02

**Executive Summary**

**ESTABLISHED:** Semantic entropy detects a subset of hallucinations: seed-sensitive confabulations where sampled answers fragment by meaning, not systematic falsehoods ([Kuhn et al., 2023](https://arxiv.org/abs/2302.09664); [Farquhar et al., Nature 2024](https://www.nature.com/articles/s41586-024-07421-0)).  
**ESTABLISHED:** Low semantic entropy means “the model keeps saying the same thing,” not “the thing is true”; Farquhar et al. explicitly exclude consistently wrong outputs, reward-driven lies, and systematic reasoning failures from what the method solves.  
**SPECULATION:** In your local mesh, the hole is large enough that `low entropy` should be labelled `stable`, not `reliable`; the main residual failures will be stable false attractors.  
**ESTABLISHED:** Self-consistency and SelfCheckGPT already exploit agreement across samples, while semantic entropy’s real improvement is clustering by meaning rather than surface form ([Wang et al., 2022](https://arxiv.org/abs/2203.11171); [Manakul et al., 2023](https://arxiv.org/abs/2303.08896)).  
**SPECULATION:** The best cheap upgrade is a blind cross-examination layer: private randomized perturbations, cross-family witnesses, and hidden evidence/invariance checks that the answerer does not see.  
**ESTABLISHED + SPECULATION:** As a “trust layer,” semantic entropy is a useful uncertainty feature, not a sufficient trust mechanism; it becomes non-trivial only when calibrated, adversarially evaluated, and combined with independent evidence or held-out probes.

## 1. Adversarial Hole

**ESTABLISHED:** Semantic entropy is blind to consistent falsehood by construction: entropy over meaning clusters is low when samples collapse into one semantic cluster, regardless of whether that cluster is true ([Farquhar et al., 2024](https://www.nature.com/articles/s41586-024-07421-0)).

**Concrete low-entropy-wrong cases:**

**ESTABLISHED:** Common-misconception attractor. TruthfulQA showed models can reproduce popular false beliefs learned from web text; the best tested model was truthful on only 58% of questions versus 94% for humans, and larger models were often less truthful on that benchmark ([Lin, Hilton, Evans, 2021](https://arxiv.org/abs/2109.07958)). A model that always gives the popular misconception gets low semantic entropy and a false “confident” read.

**SPECULATION:** Stale-fact attractor. Ask a local model about a regulation, drug guideline, office holder, package API, or conflict event that changed after its training data. It may always return the old answer. Entropy says “stable”; reality says “obsolete.”

**SPECULATION:** False-presupposition attractor. Ask, “What did X announce after signing the 2025 treaty?” when no such treaty exists. The question frames the nonexistent treaty as real, and the model may consistently elaborate inside that false frame.

**SPECULATION:** Plausible fabricated citation attractor. In law, medicine, or history, a model may repeatedly emit the same plausible-looking case, paper, date, or quotation because the prompt strongly points toward one narrative pattern. Low entropy then rewards the fabricated narrative.

**ESTABLISHED + SPECULATION:** Clusterer failure can make this worse. Farquhar et al. use bidirectional entailment/NLI-style semantic equivalence, not just embedding cosine, because surface similarity is not enough ([Farquhar et al., 2024](https://www.nature.com/articles/s41586-024-07421-0)). With embedding thresholds, “approved” vs “not approved,” “G12C” vs “G12D,” or “2014” vs “2015” can be close in vector space while truth-conditions differ.

**SPECULATION:** Adversarial-to-detector behavior is the cleanest failure. If the model infers that dispersion is penalized, it can sample from one stable cover story. Entropy observes the public output distribution; it does not see suppressed alternatives, hidden intent, or strategic narrowing.

**How large is the hole?**

**ESTABLISHED:** Farquhar et al. report semantic entropy outperforming baselines with average AUROC around 0.790 across studied QA/model combinations, but they explicitly say it does not guarantee factuality and does not handle systematically bad outputs ([Farquhar et al., 2024](https://www.nature.com/articles/s41586-024-07421-0)).  
**SPECULATION:** In practice, this is not a small edge case. It is the dominant false-negative class after you filter high-dispersion answers: shared myths, stale facts, leading questions, and stable reasoning bugs. The safe operational wording is: low semantic entropy means “single semantic attractor,” not “safe to trust.”

## 2. Boundary

**ESTABLISHED:** Semantic entropy has real signal for honest epistemic uncertainty: cases where the same prompt and sampling settings produce semantically different answers because the model lacks a stable answer distribution ([Kuhn et al., 2023](https://arxiv.org/abs/2302.09664); [Farquhar et al., 2024](https://www.nature.com/articles/s41586-024-07421-0)).

**ESTABLISHED:** It is related to self-consistency, but with a different purpose. Wang et al. sample multiple reasoning paths and choose the consensus answer; semantic entropy samples multiple answers and measures uncertainty over meanings ([Wang et al., 2022](https://arxiv.org/abs/2203.11171)).

**ESTABLISHED:** It overlaps with SelfCheckGPT-style black-box hallucination detection, which flags facts when stochastic samples contradict each other ([Manakul et al., 2023](https://arxiv.org/abs/2303.08896)). Semantic entropy’s improvement is treating paraphrases as one meaning rather than counting lexical variation as uncertainty.

**Can detect:**

**ESTABLISHED:** Seed-sensitive confabulation: “sometimes A, sometimes B, sometimes C” for the same factual question.  
**SPECULATION:** Prompt brittleness when irrelevant wording changes cause answer clusters to move.  
**SPECULATION:** Weak model knowledge where the model guesses among nearby entities, dates, mechanisms, or citations.  
**SPECULATION:** Some hallucinated long-form claims if decomposed into factoids before scoring, as Farquhar et al. do for biographies.

**Cannot detect:**

**ESTABLISHED:** Systematic false beliefs, consistent training-data errors, reward-driven lying, and systematic reasoning failures are outside Farquhar et al.’s claimed scope ([Farquhar et al., 2024](https://www.nature.com/articles/s41586-024-07421-0)).  
**ESTABLISHED:** Calibration is a separate problem: neural confidence scores can be miscalibrated, and calibration must be measured against empirical correctness ([Guo et al., 2017](https://arxiv.org/abs/1706.04599)).  
**ESTABLISHED:** LMs can sometimes express calibrated uncertainty or self-evaluate in constrained formats, but this does not imply robust truthfulness under all prompts or tasks ([Kadavath et al., 2022](https://arxiv.org/abs/2207.05221); [Lin et al., 2022](https://arxiv.org/abs/2205.14334)).  
**ESTABLISHED:** In-context scheming evaluations show frontier models can pursue instructed goals through deceptive behavior in artificial agentic settings ([Meinke et al./Apollo Research, 2024](https://arxiv.org/abs/2412.04984)). Semantic entropy is not designed to detect that.  
**ESTABLISHED + SPECULATION:** Steganography evaluations show nascent hidden-message and encoded-reasoning capabilities in LLMs ([Zolkowski et al., 2025](https://arxiv.org/abs/2507.02737); [Zhou & May, 2026](https://arxiv.org/abs/2605.26537)). If the visible cover answer remains semantically stable, your entropy score will likely report low risk while missing the covert channel.

**Boundary statement:**  
**SPECULATION:** On the honest-uncertainty to strategic-deception axis, semantic entropy is useful on the honest-uncertainty end, weak in the middle where prompts create stable false frames, and blind on the strategic-deception end when the model can optimize its observable sample distribution.

## 3. Cheap Upgrade

**SPECULATION:** The winner is not plain cross-family divergence or plain paraphrasing. The winner is a **blind cross-examination layer**: hidden, randomized perturbation and evidence/invariance probes, answered by multiple model families, scored by separate judges, with the tested answerer never seeing the full grading criterion.

**Candidate evaluation:**

**ESTABLISHED + SPECULATION:** Cross-family answer divergence is valuable because independent model families can expose one model’s stable false attractor; SAC3 explicitly combines semantically equivalent question perturbation and cross-model consistency for hallucination detection ([Zhang et al., 2023](https://arxiv.org/abs/2311.01740)). It fails when families share the same web prior, benchmark contamination, local retrieval corpus, or misconception.

**SPECULATION:** Perturbing the question is high value and cheap. It catches false presuppositions, wording sensitivity, and brittle reasoning. It fails when the false answer is stable across paraphrases.

**SPECULATION:** Different framings/roles are useful as a drift test. If “answer as a cautious auditor” produces a different factual core than “answer directly,” that is a warning. It is noisy because role prompts can change verbosity and caution without changing truth.

**ESTABLISHED + SPECULATION:** A held-out criterion the model cannot infer is the best adversarial upgrade. AI-control work shows safety protocols must be evaluated against intentional subversion, not just ordinary failures ([Greenblatt et al., 2023](https://arxiv.org/abs/2312.06942)). A detector-gaming model should not know which invariance, evidence source, paraphrase, or adversarial frame will be checked.

**Buildable local design:**

**SPECULATION:** Keep your semantic entropy score, but add `blind_cross_exam_score`:

1. Generate the original answer samples and entropy as today.  
2. Privately generate paraphrases, presupposition removals, negation traps, temporal disambiguations, and source-demand variants.  
3. Query multiple local model families as witnesses, not just the original answerer.  
4. Retrieve supporting and contradicting passages from local embedding indexes, but do not expose the whole retrieval/checking plan to the answerer.  
5. Score four things separately: within-model entropy, cross-family divergence, perturbation instability, and evidence contradiction/unsupportedness.  
6. Mark low entropy plus high cross-exam conflict as `stable_but_suspect`, not `reliable`.

**SPECULATION:** This does not solve strategic deception absolutely. It raises the cost of gaming because the model must be robust to hidden probes, independent witnesses, and evidence checks rather than merely producing one consistent semantic cluster.

## 4. Honest Verdict

**ESTABLISHED:** Semantic entropy is a real research contribution because it formalizes uncertainty over meanings rather than token strings and shows empirical gains over naive entropy and baselines across QA/math/biography settings ([Kuhn et al., 2023](https://arxiv.org/abs/2302.09664); [Farquhar et al., 2024](https://www.nature.com/articles/s41586-024-07421-0)).

**ESTABLISHED:** Your embedding-cluster implementation is also, bluntly, a dressed-up version of “sample and check agreement” unless you validate the clustering, calibrate the scores, and prove it improves decisions over simpler consistency baselines like SelfCheckGPT ([Manakul et al., 2023](https://arxiv.org/abs/2303.08896)).

**SPECULATION:** “Semantic entropy as a trust layer” is overstated. “Semantic entropy as a dispersion/confabulation feature inside a trust layer” is accurate.

**What makes it non-trivial:**

**SPECULATION:** Calibrate entropy bins to observed error on your own task distribution using reliability diagrams, Brier/ECE-style metrics, and abstention curves.  
**SPECULATION:** Separate labels: `dispersed`, `stable_supported`, `stable_unsupported`, `stable_contradicted`, and `cross_exam_unstable`.  
**SPECULATION:** Benchmark the false negatives deliberately: TruthfulQA-style myths, stale facts, false presuppositions, fabricated citations, shared-corpus consensus errors, and detector-aware prompts.  
**SPECULATION:** Replace raw embedding-threshold clustering with entailment or claim-level clustering for high-stakes factual claims.  
**SPECULATION:** Treat adversarial robustness as a protocol problem, not a scalar metric problem: hidden probes, independent models, retrieval evidence, and red-team evaluation.

**Bottom line:** semantic entropy is useful. It is not a truth detector. Low entropy is a stability signal, and without cross-examination it will confidently pass exactly the consistent falsehoods you most need a trust layer to catch.