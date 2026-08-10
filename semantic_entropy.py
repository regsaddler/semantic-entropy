#!/usr/bin/env python3
"""Semantic Entropy Checker -- confabulation detector via meaning-spread.

v0.2 crossexam (2026-07-03) -- **EXPERIMENTAL: FAILED its pre-registered falsifier same day**
(verdict in receipts/PREREGISTRATION_v0.2_falsifier.md: delta over v0.1 = 0;
the one live attractor -- a stale fact -- passed as STABLE-AGREED because local families share
training cutoffs; 11/12 classic misconceptions were already debunked-by-fleet). The axes are
mechanically sound (45/45 self-tests) but DECORATIVE at local-fleet tier: do not treat a
--crossexam STABLE-AGREED as attractor-clearance. The surviving route is a true cross-VENDOR
panel under a NEW prereg. v0.1 verdicts are canonical and unaffected. Axis design:
  PARAPHRASE axis -- K hidden rephrasings of the question, one answer each; a real fact
    is stable across rephrasings, a confabulation often flips.
  CROSS-FAMILY axis -- one answer per distinct local model family; internally-consistent
    families that DISAGREE with each other expose a per-model attractor.
Combined verdict: STABLE-AGREED / STABLE-PARTIAL / MIXED / ATTRACTOR-FLAG / SCATTERED.
Default (no --crossexam) behavior is UNCHANGED v0.1.

v0.1 (2026-07-02, adversarial review-hardened -- 3 FAIL/HIGH defects fixed: order-dependent clustering,
silent partial-embed corruption, dead entropy_verdict param). Generate N answers to ONE
question at temp>0; embed; cluster by meaning; Shannon entropy over cluster sizes. Low
entropy = the model consistently means one thing. High entropy = answers fragment across
meanings = likely confabulation / genuine uncertainty. Method: Kuhn 2023 / Farquhar et al.
2024 (Nature) semantic entropy, embedding-cluster variant, on local hardware ~$0.

The literature reports semantic entropy flags confabulation better than a model's own
verbalized confidence [Farquhar 2024] -- this tool is the embedding-cluster approximation
of that idea, NOT a re-measurement of it; the comparative claim is theirs, cited.

HONEST SCOPE: v0.1 detects answer DISPERSION (honest uncertainty). v0.2 additionally
catches per-model attractors + paraphrase-fragile confabulation. NEITHER catches a
universal misconception shared by ALL families (that needs external ground truth = v0.3),
and local-fleet "cross-family" is WEAKER than true cross-vendor (open-weights models share
training-corpus overlap; a true cross-vendor panel is the stronger instrument -- this
is the $0 approximation). Low entropy is the WEAKER claim (single-link clustering can
over-merge); SCATTERED is the stronger signal. Never asserts truth -- only spread/stability.

CALIBRATION: --threshold 0.80 is an UNVALIDATED default for nomic-embed; tune per embedding
model. On partial fleet failure the run is reported as degraded, never silently. An axis
that cannot run (too few families, bad paraphrases) reports UNAVAILABLE and the combined
verdict degrades honestly (STABLE-PARTIAL, never fake agreement).

Usage: semantic-entropy --question "..." [--n 8] [--threshold 0.80] [--temp 0.5] [--json]
       semantic-entropy --question "..." --crossexam [--paraphrases 4] [--families 3]
       semantic-entropy --self-test
"""
import argparse
import os
import json
import math
import re
import sys
import urllib.parse
import urllib.request

FLEET = os.environ.get("SE_ENDPOINT", "http://127.0.0.1:1234/v1")
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _normalize_endpoint(endpoint):
    parts = urllib.parse.urlsplit(endpoint)
    if parts.scheme not in {"http", "https"}:
        raise ValueError("SE_ENDPOINT must use http or https")
    if not parts.hostname:
        raise ValueError("SE_ENDPOINT must include a hostname")
    if parts.username is not None or parts.password is not None:
        raise ValueError("SE_ENDPOINT must not embed credentials")
    if parts.query or parts.fragment:
        raise ValueError("SE_ENDPOINT must not include a query or fragment")
    path = parts.path.rstrip("/")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def _endpoint_url(suffix):
    return _normalize_endpoint(FLEET) + "/" + suffix.lstrip("/")


def _json_request(target, timeout, max_response_bytes=MAX_RESPONSE_BYTES):
    """Read one JSON response with a byte ceiling and no redirect following."""
    if max_response_bytes <= 0:
        raise ValueError("max_response_bytes must be greater than zero")
    target_url = target.full_url if isinstance(target, urllib.request.Request) else target
    _normalize_endpoint(target_url)
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(target, timeout=timeout) as response:
        content_length = response.headers.get("Content-Length")
        if content_length is not None:
            try:
                declared_bytes = int(content_length)
            except ValueError as error:
                raise ValueError("invalid Content-Length") from error
            if declared_bytes < 0 or declared_bytes > max_response_bytes:
                raise ValueError("JSON response exceeds byte ceiling")
        payload = response.read(max_response_bytes + 1)
    if len(payload) > max_response_bytes:
        raise ValueError("JSON response exceeds byte ceiling")
    return json.loads(payload)


def cluster_by_similarity(embeddings, threshold):
    """ORDER-INDEPENDENT (adversarial-review fix): connected components of the >=threshold cosine graph
    via union-find. Two answers are same-meaning if cosine>=threshold; equivalence is
    transitive. Arrival order never changes the result. Returns clusters as sorted index
    lists, ordered by smallest member. Known property: single-link CAN chain near-duplicates
    into one component (biases toward FEWER clusters / lower dispersion) -- which is why
    CONSISTENT is the weaker verdict and SCATTERED the stronger one."""
    n = len(embeddings)
    if n == 0:
        return []

    def cos(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return 0.0 if na == 0.0 or nb == 0.0 else dot / (na * nb)

    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    for i in range(n):
        for j in range(i + 1, n):
            if cos(embeddings[i], embeddings[j]) >= threshold:
                union(i, j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return [sorted(g) for _, g in sorted(groups.items())]


def semantic_entropy(cluster_sizes, n):
    """Shannon entropy (bits) over p_i = size_i/n. 0.0 for n<=0 or a single cluster.
    adversarial-review fix: raises ValueError if sizes don't sum to n (catches the caller-contract
    violation at the source instead of returning nonsense like negative entropy)."""
    if n <= 0 or len(cluster_sizes) <= 1:
        return 0.0
    if sum(cluster_sizes) != n:
        raise ValueError(f"cluster_sizes {cluster_sizes} do not sum to n={n}")
    return -sum((s / n) * math.log2(s / n) for s in cluster_sizes if s > 0)


def entropy_verdict(entropy_bits, n_clusters, n):
    """adversarial-review fix: now USES entropy_bits (was dead -- verdict keyed only on cluster count).
    Bands on the NORMALIZED entropy ratio H/log2(n) as the primary signal, cluster-count
    as support. Returns exactly one of CONSISTENT / MIXED / SCATTERED."""
    if n <= 1 or n_clusters <= 1:
        return "CONSISTENT"
    max_h = math.log2(n)
    ratio = entropy_bits / max_h if max_h > 0 else 0.0
    if ratio >= 0.5 or n_clusters >= max(3, (n + 1) // 2):
        return "SCATTERED"
    return "MIXED"


# ── v0.2 deterministic units (pure -- covered by self-test) ───────────────────
FAMILY_KEYS = ["qwen", "gemma", "mistral", "llama", "phi", "minimax", "granite", "deepseek"]
# adversarial-review HIGH finding fix (2026-07-03): non-chat roles must never become a "family answer" -- a reranker's
# score-string would embed + cluster as a fake semantic position and manufacture a false
# ATTRACTOR-FLAG. Substring role-exclusion + the _prose_ok gate below (belt and suspenders).
NONCHAT_KEYS = ["embed", "rerank", "tts", "whisper", "docling", "voxtral", "ocr"]


def pick_families(model_ids, max_f):
    """Deterministic family selection: first loaded CHAT model per family, FAMILY_KEYS order,
    non-chat roles (NONCHAT_KEYS) excluded. Returns [(family, model_id)]. Same input → same
    output. (The all(f != fam...) guard is belt-and-suspenders for a future refactor that
    loosens the one-fam-per-outer-iteration structure -- it cannot fire today.)"""
    picked = []
    for fam in FAMILY_KEYS:
        if len(picked) >= max_f:
            break
        for mid in sorted(model_ids):
            low = mid.lower()
            if any(k in low for k in NONCHAT_KEYS):
                continue
            if fam in low and all(f != fam for f, _ in picked):
                picked.append((fam, mid))
                break
    return picked


def _prose_ok(text):
    """A trusted family/paraphrase answer must look like prose, not a score dump or empty
    completion (adversarial-review HIGH finding companion gate: category errors degrade the axis, never enter it)."""
    t = (text or "").strip()
    return len(t) >= 15 and " " in t


def dedupe_by_cosine(vecs, ceiling):
    """Keep indices whose vector is NOT >= ceiling-similar to an already-kept one (first-kept
    wins; deterministic in input order). adversarial-review MED finding fix: K near-identical paraphrases must not
    masquerade as K independent probes."""
    kept = []
    for i, v in enumerate(vecs):
        if not any(_cos(v, vecs[j]) >= ceiling for j in kept):
            kept.append(i)
    return kept


def validate_paraphrase(orig_norm, para_norm, cos_sim, floor):
    """A paraphrase is usable iff it is NOT the same string (post-whitespace-normalize,
    case-folded) and its question-embedding cosine to the original is >= floor (it must
    still ASK the same thing). Pure: caller supplies the cosine."""
    if not para_norm or para_norm.lower() == orig_norm.lower():
        return False
    return cos_sim >= floor


def combined_verdict(self_v, para_v, fam_divergent, para_avail, fam_avail):
    """v0.2 banding. Precedence: self-SCATTERED wins (v0.1 already caught it); any
    AVAILABLE axis firing => ATTRACTOR-FLAG (the case v0.1 structurally misses);
    STABLE-AGREED requires BOTH axes available and clean (never fake agreement from a
    missing axis); one axis missing but the rest clean => STABLE-PARTIAL / MIXED-PARTIAL;
    both axes missing => DEGRADED-<self> (v0.1 fallback, marked)."""
    if self_v == "SCATTERED":
        return "SCATTERED"
    fired = (fam_avail and fam_divergent) or (para_avail and para_v != "CONSISTENT")
    if fired:
        return "ATTRACTOR-FLAG"
    if not para_avail and not fam_avail:
        return "DEGRADED-" + self_v
    if para_avail and fam_avail:
        return "STABLE-AGREED" if self_v == "CONSISTENT" else "MIXED"
    return "STABLE-PARTIAL" if self_v == "CONSISTENT" else "MIXED-PARTIAL"


def parse_numbered_lines(text, k):
    """Extract up to k items from a numbered-list completion ('1. ...' / '2) ...').
    Pure parser; tolerant of leading chatter, ignores blank/unnumbered lines.
    Fallback (smoke-caught 2026-07-03): if the list arrived whitespace-collapsed onto
    ONE line ('1. A 2. B 3. C'), split on the inline numbering instead -- without it the
    whole list parses as a single item and the axis goes UNAVAILABLE."""
    items = []
    for line in text.splitlines():
        m = re.match(r"\s*\d+\s*[.)]\s*(.+\S)\s*$", line)
        if m and len(items) < k:
            items.append(m.group(1).strip())
    if len(items) <= 1:
        inline = [p.strip() for p in re.split(r"\s*\d+\s*[.)]\s+", text) if p.strip()]
        if len(inline) >= 2 and len(inline) > len(items):   # >=2: unnumbered prose must not become an "item"
            items = inline[:k]
    return items


# ── I/O (template-owned) ──────────────────────────────────────────────────────
def _fleet_models():
    return [m["id"] for m in _json_request(_endpoint_url("models"), timeout=10)["data"]]


def _pick(models, prefs):
    for p in prefs:
        for m in models:
            if p in m.lower():
                return m
    return models[0] if models else None


def _re_ws(s):
    return re.sub(r"\s+", " ", s).strip()


def sample(question, model, n, temp):
    """Returns (answers, ok_flags) -- ok_flags[i] False if that sample errored.
    adversarial-review fix: failed samples are TAGGED, not silently mixed into the meaning-clusters."""
    answers, ok = [], []
    for _ in range(n):
        body = json.dumps({"model": model, "temperature": temp, "max_tokens": 400,
                           "messages": [{"role": "user", "content": question}]}).encode()
        try:
            r = _json_request(urllib.request.Request(
                _endpoint_url("chat/completions"), data=body,
                headers={"Content-Type": "application/json"}), timeout=120)
            answers.append(_re_ws(r["choices"][0]["message"]["content"]))
            ok.append(True)
        except Exception as e:
            answers.append(f"(error: {str(e)[:80]})")
            ok.append(False)
    return answers, ok


def embed(texts, model):
    body = json.dumps({"model": model, "input": texts}).encode()
    r = _json_request(urllib.request.Request(
        _endpoint_url("embeddings"), data=body,
        headers={"Content-Type": "application/json"}), timeout=120)
    return [d["embedding"] for d in r["data"]]


def _chat_once(model, prompt, temp, timeout=120, raw=False):
    """raw=True preserves newlines (needed for list-parsing -- _re_ws collapsing newlines
    was the smoke-caught bug that silently killed the paraphrase axis)."""
    body = json.dumps({"model": model, "temperature": temp, "max_tokens": 400,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    r = _json_request(urllib.request.Request(
        _endpoint_url("chat/completions"), data=body,
        headers={"Content-Type": "application/json"}), timeout=timeout)
    content = r["choices"][0]["message"]["content"]
    return content if raw else _re_ws(content)


def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return 0.0 if na == 0.0 or nb == 0.0 else dot / (na * nb)


def paraphrase_axis(question, gen, emb, k, floor, threshold):
    """K hidden rephrasings -> one low-temp answer each -> cluster the answers.
    Returns dict with available flag, per-axis verdict, clusters. Fail-loud on <2
    usable paraphrase-answers (axis UNAVAILABLE, never a fake verdict)."""
    out = {"available": False, "reason": "", "paraphrases": [], "verdict": None,
           "n_clusters": 0, "clusters": [], "entropy_bits": 0.0}
    try:
        raw = _chat_once(gen, "Rewrite the following question " + str(k) + " different ways. "
                         "Keep the meaning EXACTLY the same; change only the wording. "
                         "Output ONLY a numbered list, one rewrite per line.\n\nQuestion: "
                         + question, 0.7)
    except Exception as e:
        out["reason"] = "paraphrase generation failed: " + str(e)[:80]
        return out
    cands = parse_numbered_lines(raw, k)
    if len(cands) < 2:
        out["reason"] = "parsed <2 paraphrases from generator output"
        return out
    try:
        qvecs = embed([question] + cands, emb)
    except Exception as e:
        out["reason"] = "paraphrase-validation embed failed: " + str(e)[:80]
        return out
    if len(qvecs) != 1 + len(cands):
        out["reason"] = "embed count mismatch during validation -- aborting axis"
        return out
    orig_norm = _re_ws(question)
    vi = [i for i, c in enumerate(cands)
          if validate_paraphrase(orig_norm, _re_ws(c), _cos(qvecs[0], qvecs[1 + i]), floor)]
    # adversarial-review MED finding fix: near-duplicate paraphrases must not count as independent probes
    kept = dedupe_by_cosine([qvecs[1 + i] for i in vi], 0.97)
    valid = [cands[vi[k]] for k in kept]
    n_dropped_dup = len(vi) - len(valid)
    if len(valid) < 2:
        out["reason"] = ("<2 paraphrases survived validation+dedupe (floor " + str(floor) +
                         ", " + str(n_dropped_dup) + " near-duplicate(s) dropped)")
        return out
    out["n_near_dup_dropped"] = n_dropped_dup
    answers = []
    for p in valid:
        try:
            a = _chat_once(gen, p, 0.2)
            if _prose_ok(a):
                answers.append(a)
        except Exception:
            pass
    out["n_para_attempted"] = len(valid)
    out["n_para_answered"] = len(answers)
    if len(answers) < 2:
        out["reason"] = "<2 prose paraphrase answers returned (" + \
            str(len(answers)) + "/" + str(len(valid)) + ")"
        return out
    try:
        avecs = embed(answers, emb)
    except Exception as e:
        out["reason"] = "answer embed failed: " + str(e)[:80]
        return out
    if len(avecs) != len(answers):
        out["reason"] = "answer embed count mismatch -- aborting axis"
        return out
    clusters = cluster_by_similarity(avecs, threshold)
    sizes = [len(c) for c in clusters]
    H = semantic_entropy(sizes, len(answers))
    out.update({"available": True, "paraphrases": valid,
                "verdict": entropy_verdict(H, len(clusters), len(answers)),
                "n_clusters": len(clusters), "entropy_bits": round(H, 3),
                "clusters": [[answers[i][:160] for i in c] for c in clusters]})
    return out


def family_axis(question, families, emb, threshold):
    """One low-temp answer per model family -> cluster together. Divergent = >1
    meaning-cluster across families. Requires >=2 families ANSWERING, else UNAVAILABLE."""
    out = {"available": False, "reason": "", "families": [], "divergent": None,
           "n_clusters": 0, "clusters": [], "grouping": []}
    got = []
    for fam, mid in families:
        try:
            a = _chat_once(mid, question, 0.2, timeout=180)
            if _prose_ok(a):                      # adversarial-review HIGH finding companion: score-dumps never enter the panel
                got.append((fam, mid, a))
        except Exception:
            pass
    out["n_attempted"] = len(families)            # adversarial-review MED finding fix: panel shrink must be visible
    out["n_answered"] = len(got)
    if len(got) < 2:
        out["reason"] = "<2 families gave prose answers (" + str(len(got)) + "/" + \
            str(len(families)) + " attempted: " + ",".join(f for f, _ in families) + ")"
        return out
    answers = [a for _, _, a in got]
    try:
        vecs = embed(answers, emb)
    except Exception as e:
        out["reason"] = "family-answer embed failed: " + str(e)[:80]
        return out
    if len(vecs) != len(answers):
        out["reason"] = "family-answer embed count mismatch -- aborting axis"
        return out
    clusters = cluster_by_similarity(vecs, threshold)
    out.update({"available": True, "families": [(f, m) for f, m, _ in got],
                "divergent": len(clusters) > 1, "n_clusters": len(clusters),
                "clusters": [[got[i][2][:160] for i in c] for c in clusters],
                "grouping": [[got[i][0] for i in c] for c in clusters]})
    return out


def run(question, n, threshold, temp, model, as_json,
        crossexam=False, k_para=4, max_fam=3, para_floor=0.60):
    models = _fleet_models()
    gen = model or _pick(models, ["qwen3.6-35b", "qwen3.6-27b", "mistral", "gemma-4-31b"])
    emb = _pick(models, ["nomic", "embedding"])
    if not gen or not emb:
        print("ERROR: need a generator + embedding model loaded on the fleet.", file=sys.stderr)
        return 2

    answers, ok = sample(question, gen, n, temp)
    good = [answers[i] for i in range(len(answers)) if ok[i]]     # adversarial-review fix: exclude failed samples
    n_failed = len(answers) - len(good)
    if not good:
        print("ERROR: all fleet samples failed.", file=sys.stderr)
        return 2
    embs = embed(good, emb)
    if len(embs) != len(good):                                    # adversarial-review fix: guard silent-corruption path
        print(f"ERROR: embed returned {len(embs)} vectors for {len(good)} inputs -- aborting "
              f"(would bias entropy toward CONSISTENT).", file=sys.stderr)
        return 3

    n_eff = len(good)
    clusters = cluster_by_similarity(embs, threshold)
    sizes = [len(c) for c in clusters]
    H = semantic_entropy(sizes, n_eff)
    verdict = entropy_verdict(H, len(clusters), n_eff)

    result = {
        "question": question, "n_requested": n, "n_effective": n_eff, "n_failed": n_failed,
        "gen_model": gen, "embed_model": emb, "threshold": threshold, "temp": temp,
        "semantic_entropy_bits": round(H, 3),
        "max_entropy_bits": round(math.log2(n_eff), 3) if n_eff > 1 else 0.0,
        "n_meaning_clusters": len(clusters), "cluster_sizes": sizes, "verdict": verdict,
        "clusters": [[good[i][:220] for i in c] for c in clusters],
    }

    if crossexam:
        para = paraphrase_axis(question, gen, emb, k_para, para_floor, threshold)
        fams = pick_families(models, max_fam)
        fam = family_axis(question, fams, emb, threshold)
        combined = combined_verdict(verdict, para["verdict"], bool(fam["divergent"]),
                                    para["available"], fam["available"])
        result["paraphrase_axis"] = para
        result["family_axis"] = fam
        result["combined_verdict"] = combined
        result["scope_note"] = ("stability+agreement, not truth; local-family panel is the $0 "
                                "approximation of cross-vendor -- does not catch universal "
                                "misconceptions (v0.3 scope)")

    if as_json:
        print(json.dumps(result, indent=1))
    else:
        deg = f"  (DEGRADED: {n_failed} of {n} samples failed)" if n_failed else ""
        print(f"SEMANTIC ENTROPY: {H:.3f} / {result['max_entropy_bits']:.3f} max bits -- "
              f"{len(clusters)} meaning-cluster(s) from {n_eff} samples{deg}")
        print(f"SELF VERDICT: {verdict}  (dispersion, not truth -- see --help scope)")
        for c in clusters:
            print(f"  [{len(c)}] {good[c[0]][:140]}")
        if crossexam:
            p, f = result["paraphrase_axis"], result["family_axis"]
            print(f"PARAPHRASE AXIS: " + (f"{p['verdict']} ({p['n_clusters']} cluster(s) across "
                  f"{p['n_para_answered']}/{p['n_para_attempted']} rephrasing(s), "
                  f"{p.get('n_near_dup_dropped', 0)} near-dup dropped)" if p["available"]
                  else f"UNAVAILABLE -- {p['reason']}"))
            print(f"FAMILY AXIS: " + ((("DIVERGENT " + str(f['grouping'])) if f["divergent"]
                  else f"agreed across {f['n_answered']}/{f['n_attempted']} families") if f["available"]
                  else f"UNAVAILABLE -- {f['reason']}"))
            print(f"COMBINED: {result['combined_verdict']}  ({result['scope_note']})")
    return 0


def self_test():
    import itertools
    checks = []

    def ck(name, cond):
        checks.append((name, cond))

    # cluster: order-independence (the adversarial review-caught HIGH defect)
    a = [[1.0, 0.0], [0.966, 0.259], [0.866, 0.5]]  # 0deg,15deg,30deg
    counts = {len(cluster_by_similarity([a[i] for i in perm], 0.90)) for perm in itertools.permutations(range(3))}
    ck("cluster: order-independent cluster COUNT across all permutations", len(counts) == 1)
    ck("cluster: identical+orthogonal", cluster_by_similarity([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]], 0.9) == [[0, 1], [2]])
    ck("cluster: empty", cluster_by_similarity([], 0.9) == [])
    ck("cluster: zero-norm not merged", cluster_by_similarity([[0.0, 0.0], [1.0, 0.0]], 0.9) == [[0], [1]])
    # entropy
    ck("entropy: single cluster 0.0", semantic_entropy([4], 4) == 0.0)
    ck("entropy: 2-2 = 1 bit", semantic_entropy([2, 2], 4) == 1.0)
    ck("entropy: 4x1 = 2 bits", round(semantic_entropy([1, 1, 1, 1], 4), 4) == 2.0)
    ck("entropy: 3-1", round(semantic_entropy([3, 1], 4), 4) == 0.8113)
    try:
        semantic_entropy([10, 10], 8)
        ck("entropy: bad-sum raises", False)
    except ValueError:
        ck("entropy: bad-sum raises ValueError", True)
    # verdict USES entropy (the CRITICAL fix)
    ck("verdict: uses entropy -- same clusters, diff entropy => diff verdict",
       entropy_verdict(2.4, 3, 8) != entropy_verdict(0.6, 3, 8))
    ck("verdict: consistent (1 cluster)", entropy_verdict(0.0, 1, 8) == "CONSISTENT")
    ck("verdict: scattered (high ratio)", entropy_verdict(3.0, 8, 8) == "SCATTERED")
    ck("verdict: mixed", entropy_verdict(1.0, 3, 8) == "MIXED")
    ck("verdict: scattered by cluster-count", entropy_verdict(2.0, 4, 8) == "SCATTERED")

    # ── v0.2 pure units ──
    mids = ["qwen3.6-35b", "qwen3.6-27b", "gemma-4-31b", "nomic-embed-text",
            "mistral-small-4", "text-embedding-qwen3-embedding-8b"]
    pf = pick_families(mids, 3)
    ck("families: one per family, key order", [f for f, _ in pf] == ["qwen", "gemma", "mistral"])
    ck("families: embedders excluded", all("embed" not in m for _, m in pf))
    ck("families: deterministic first-sorted pick", pf[0][1] == "qwen3.6-27b")
    ck("families: max_f respected", len(pick_families(mids, 2)) == 2)
    ck("families: empty input", pick_families([], 3) == [])
    ck("paraphrase-validate: identical string rejected",
       not validate_paraphrase("What is X?", "what is x?", 0.99, 0.60))
    ck("paraphrase-validate: below-floor rejected",
       not validate_paraphrase("What is X?", "Tell me about Y", 0.30, 0.60))
    ck("paraphrase-validate: good accepted",
       validate_paraphrase("What is X?", "Could you say what X is?", 0.85, 0.60))
    ck("paraphrase-validate: empty rejected", not validate_paraphrase("Q?", "", 0.99, 0.60))
    ck("parse-numbered: basic",
       parse_numbered_lines("Sure!\n1. Alpha one\n2) Beta two\nnoise\n3. Gamma", 2) == ["Alpha one", "Beta two"])
    ck("parse-numbered: none", parse_numbered_lines("no list here", 4) == [])
    ck("parse-numbered: whitespace-collapsed inline list recovers (smoke-caught bug)",
       parse_numbered_lines("1. Which city is the capital? 2. Name the capital city. 3. Identify the capital.", 3)
       == ["Which city is the capital?", "Name the capital city.", "Identify the capital."])
    # combined_verdict truth table -- every branch
    ck("combined: self-SCATTERED wins", combined_verdict("SCATTERED", "CONSISTENT", False, True, True) == "SCATTERED")
    ck("combined: family divergence fires ATTRACTOR-FLAG",
       combined_verdict("CONSISTENT", "CONSISTENT", True, True, True) == "ATTRACTOR-FLAG")
    ck("combined: paraphrase instability fires ATTRACTOR-FLAG",
       combined_verdict("CONSISTENT", "MIXED", False, True, True) == "ATTRACTOR-FLAG")
    ck("combined: unavailable axis can NOT fire (no fake divergence)",
       combined_verdict("CONSISTENT", "MIXED", True, False, False) == "DEGRADED-CONSISTENT")
    ck("combined: both clean + both available = STABLE-AGREED",
       combined_verdict("CONSISTENT", "CONSISTENT", False, True, True) == "STABLE-AGREED")
    ck("combined: one axis missing never claims full agreement",
       combined_verdict("CONSISTENT", "CONSISTENT", False, True, False) == "STABLE-PARTIAL")
    ck("combined: self-MIXED + clean axes = MIXED",
       combined_verdict("MIXED", "CONSISTENT", False, True, True) == "MIXED")
    ck("combined: self-MIXED + one axis = MIXED-PARTIAL",
       combined_verdict("MIXED", None, False, False, True) == "MIXED-PARTIAL")
    ck("combined: degraded fallback marks itself",
       combined_verdict("MIXED", None, False, False, False) == "DEGRADED-MIXED")
    ck("combined: fam-only divergence fires (para absent)",
       combined_verdict("CONSISTENT", None, True, False, True) == "ATTRACTOR-FLAG")
    ck("combined: SCATTERED wins even with both axes unavailable",
       combined_verdict("SCATTERED", None, False, False, False) == "SCATTERED")
    # adversarial-review HIGH finding fix: non-chat roles excluded from family panel
    live_ish = ["qwen3-reranker-8b-mxfp8", "qwen/qwen3.6-27b", "voxtral-4b-tts-2603-mlx",
                "mistral-small-3.2", "text-embedding-nomic-embed-text-v1.5", "gemma-4-31b"]
    pf2 = pick_families(live_ish, 3)
    ck("families: reranker never picked as qwen rep", pf2[0][1] == "qwen/qwen3.6-27b")
    ck("families: tts/voxtral never picked", all("voxtral" not in m for _, m in pf2))
    ck("prose-ok: real answer passes", _prose_ok("Paris is the capital of France."))
    ck("prose-ok: score dump rejected", not _prose_ok("0.9732"))
    ck("prose-ok: empty rejected", not _prose_ok("  "))
    # adversarial-review MED finding fix: near-duplicate paraphrase vectors deduped
    ck("dedupe: near-identical collapsed",
       dedupe_by_cosine([[1.0, 0.0], [0.999, 0.02], [0.0, 1.0]], 0.97) == [0, 2])
    ck("dedupe: distinct all kept",
       dedupe_by_cosine([[1.0, 0.0], [0.7, 0.7], [0.0, 1.0]], 0.97) == [0, 1, 2])
    ck("dedupe: empty", dedupe_by_cosine([], 0.97) == [])

    ok = all(c for _, c in checks)
    for name, c in checks:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}")
    print(f"{'ALL PASS' if ok else 'FAILURES'} ({sum(1 for _, c in checks if c)}/{len(checks)})")
    return 0 if ok else 1


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    ap = argparse.ArgumentParser(prog="semantic-entropy")
    ap.add_argument("--question", required=True)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--threshold", type=float, default=0.80,
                    help="cosine same-meaning cutoff -- UNVALIDATED default for nomic-embed; tune per model")
    ap.add_argument("--temp", type=float, default=0.5)
    ap.add_argument("--model", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--crossexam", action="store_true",
                    help="v0.2: add paraphrase-stability + cross-family-divergence axes")
    ap.add_argument("--paraphrases", type=int, default=4, help="K hidden rephrasings (crossexam)")
    ap.add_argument("--families", type=int, default=3, help="max model families to poll (crossexam)")
    ap.add_argument("--para-floor", type=float, default=0.60,
                    help="min question-cosine for a paraphrase to count as the same question")
    a = ap.parse_args()
    return run(a.question, a.n, a.threshold, a.temp, a.model, a.json,
               crossexam=a.crossexam, k_para=a.paraphrases, max_fam=a.families,
               para_floor=a.para_floor)


if __name__ == "__main__":
    sys.exit(main())
