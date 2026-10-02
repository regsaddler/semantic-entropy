# semantic-entropy

An answer-stability screen for language models, written in pure Python with
no third-party dependencies. Ask a model the same question several times,
embed the answers, cluster them by similarity, and measure how widely they scatter.

**Consistency is not truth. A model can repeat the same wrong answer.**

[Quickstart](#quickstart) · [The failed extension](#the-failure-up-front) · [Honest limits](#honest-limits)

```text
Question → sampled answers → embeddings → clusters → entropy + verdict
```

## The failure, up front

We built a v0.2 extension with paraphrase and cross-family axes, pre-registered
its pass/fail criteria, and ran it once. It failed: measured improvement over
v0.1 was zero. In that probe set, the local model families agreed on the one
genuinely stale fact. Agreement did not supply independent evidence.

We kept v0.1 and recorded the failure instead of tuning until it passed.

- [Pre-registration and recorded verdict](receipts/PREREGISTRATION_v0.2_falsifier.md)
- [Cross-family adversarial review](receipts/CROSS-FAMILY_ADVERSARIAL_REVIEW.md)

The records in `receipts/` preserve the negative result, with marked redactions of internal
identifiers. They describe this experiment, not a general verdict on the method.

## Quickstart

### 1. Run the offline self-check

Use Python 3 and Git. No model server, API key, or package installation is needed
for this step.

```bash
git clone https://github.com/regsaddler/semantic-entropy.git
cd semantic-entropy
python3 -B semantic_entropy.py --self-test
```

Expected final line: `ALL PASS (45/45)`. These checks exercise the implementation;
they do not establish detection accuracy on real questions.

### 2. Run against a model endpoint

Start a local OpenAI-compatible server that provides `/v1/models`,
`/v1/chat/completions`, and `/v1/embeddings`. It needs both a chat model and an
embedding model. The script selects the embedder from model IDs containing
`nomic` or `embedding`; check that your server exposes an appropriate ID.
Use `--model` to choose the chat model explicitly if needed.
Set `SE_ENDPOINT` to the server's `/v1` base URL.

```bash
export SE_ENDPOINT="http://127.0.0.1:1234/v1"
python3 semantic_entropy.py --question "What is the capital of Australia?"
python3 semantic_entropy.py --question "What did the 1962 Brookfield Accord establish?" --json
```

The second question is an invented premise. It is a probe, not a promised
detection: a model might reject the premise, vary its answers, or invent the
same story repeatedly. Results depend on the model and sampling.

The current script sends no authentication header. Use a compatible trusted
local endpoint; do not assume an authenticated hosted API will work unchanged.
Model runs send the question and generated answers to the configured endpoint.

### Read the result

| v0.1 verdict | Interpretation |
| --- | --- |
| `CONSISTENT` | The answers fall into one cluster. They can still be wrong. |
| `MIXED` | The answers show some variation in meaning. |
| `SCATTERED` | The answers are spread across clusters; investigate before relying on them. |

## Honest limits

- Entropy measures answer stability, not truth. Treat verdicts as a screening
  signal for follow-up, never as verification.
- This is an embedding-cluster approximation of the published semantic-entropy
  method (Kuhn et al. 2023; Farquhar et al., Nature 2024). The literature's
  comparative results are not measurements of this repository.
- The default cosine threshold, `0.80`, is unvalidated. It was chosen for
  nomic-embed and needs evaluation for your embedding model and task.
- The `--crossexam` flags remain for reproducing the failed extension. They are
  not recommended for use; model-family diversity does not ensure independent
  errors or independent training data.

## What this is not

This is a small, self-contained instrument extracted from a larger private
research stack on evidence-gated AI outputs. The larger stack is not published
here. This tool stands alone and carries its own tests and failure record.

MIT license. Issues and adversarial probes welcome; a reproduced failure is
worth more to us than a compliment.
