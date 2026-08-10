# Provenance

## Baseline source

This repository's public v0.1 baseline was frozen at commit
`36456156ebf3878bfa30c793c38d6e4a1557d70a`, committed on
2026-07-15. The metadata and continuous-integration additions that follow do
not reconstruct an earlier development history.

## Baseline hashes

```text
7e5132131e216bf75980a72355e13174a54ed4e6246deead1a90eb97056718e4  LICENSE
59f4bbd31c07cf128704471043baf38e5fe477f5c4fc760c3737079349d27743  README.md
40215e4b4e765cf9f944df777ccb1f9ec5a5dcb76656b4c5d13aa4f6c95463fd  demo.sh
e7d95eab8c09581b9327285cf79760cf32d17f0a0a84e1e28d72b9555da05921  receipts/CROSS-FAMILY_ADVERSARIAL_REVIEW.md
8363cb32ef766c58dad98f998bd2334ba87d796057bb204407ade2ec105f1755  receipts/PREREGISTRATION_v0.2_falsifier.md
e5f1ebb5fbe06d6b40b21a221d8d5f8a6de963fdbfb9fbdbb9dda1f2b7b939a3  semantic_entropy.py
```

## Reproduction record

The command below was run against the frozen baseline on 2026-08-10:

```bash
python3 -B semantic_entropy.py --self-test
```

Observed result: `ALL PASS (45/45)`.

This establishes that the frozen implementation passed its own deterministic
checks in the inspected environment. It does not establish truth detection,
peer review, independent validation, scientific novelty, or deployment
safety. The repository's v0.2 receipt is a preserved negative result, not
evidence that the remaining method is correct.

## Post-baseline hardening

Later revisions may add bounded transport reads, endpoint validation, tests,
documentation, and CI policy. Those changes are ordinary reviewed hardening;
they do not alter the baseline hashes above or retroactively improve the
pre-registered experimental result.
