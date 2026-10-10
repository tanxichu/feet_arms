#!/usr/bin/env python3
"""PREREG 修订 35: Pixtral-12B 第二裁判(非 Qwen 家族)重判。
P19a 人评主块 Klein 200 张: 第二裁判判「漏手」的图里人多数票也判漏手的比例 ≥ 0.8(另报各类精度/召回, 与 8B 裁判对照)。
P19b 抱书大评测集三种子合并, 第二裁判下 F 漏手少于 O(按人翻符号置换 p<0.05)。
P19c 底座多手图(第二裁判自己的标签)在 O 里变漏手的配对多于在 F 里(三种子合并, McNemar p<0.05); 另报底座多手按 8B 标签取的版本。
输入: 20T paper/j2/out_*.json(云机四份合并); 输出 20T paper/j2_stats.json。"""
import json, glob, random, collections
from math import comb
R = "DATA/"; RM = "PRIVATE_RATINGS/"
def cls(v): T = v.get("TOTAL"); return "ok" if v.get("ok") else ("extra" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
P = {}
for f in glob.glob(R + "paper/j2/out_*.json"): P.update(json.load(open(f)))
P = {k: cls(v) for k, v in P.items()}
def mc(b, c): n = b + c; return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def perm(d, it=20000):
    rng = random.Random(0); o = abs(sum(d)); return (sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= o - 1e-9 for _ in range(it)) + 1) / (it + 1)
out = {"n_labels": len(P)}
# ---- P19a: 人评主块(五人过半, 同 human_stats.py 的读法)
key = {r["code"]: r for r in json.load(open(RM + "ann_main_key.json"))}
RAT = json.load(open(RM + "rater_files_ann_main.json"))   # 标注者代号 → 答卷文件; 对照表只在本机私有目录, 不进 git(真名不入库)
def marks(p):
    d = json.load(open(p)); d = d["marks"] if isinstance(d, dict) else d; return {x["c"]: x["tags"] for x in d if x.get("tags")}
def h(t): return "extra" if "extra" in t else "omit" if "missing" in t else "ok" if "ok" in t else "other"
H = {r: {c: h(t) for c, t in marks(p).items()} for r, p in RAT.items()}
maj = {}
for c, r in key.items():
    if r["set"] != "val" or r["model"] != "klein" or not all(c in H[x] for x in H): continue
    (m, n), = collections.Counter(H[x][c] for x in H).most_common(1); maj[c] = m if n >= 3 else "none"
Q = {c: {"unheld": "omit", "extra": "extra", "ok": "ok"}.get(key[c]["mcls"], key[c]["mcls"]) for c in maj}   # 8B 裁判(分层标签)
J2 = {c: P.get(f"hum/{c}_a{key[c]['act']}_x") for c in maj}
def pr(lab):
    r = {}
    for nm, L in (("pixtral", J2), ("qwen8b", Q)):
        said = [c for c in maj if L[c] == lab]; true = [c for c in maj if maj[c] == lab]
        r[nm] = {"precision": sum(maj[c] == lab for c in said) / max(len(said), 1), "n_said": len(said),
                 "recall": sum(L[c] == lab for c in true) / max(len(true), 1), "n_true": len(true)}
    return r
out["human"] = {"n": len(maj), "missing_j2": sum(v is None for v in J2.values()), **{lab: pr(lab) for lab in ("omit", "extra", "ok")},
                "agree_all_pixtral": sum(J2[c] == maj[c] for c in maj) / len(maj), "agree_all_qwen8b": sum(Q[c] == maj[c] for c in maj) / len(maj)}
out["P19a"] = {"value": out["human"]["omit"]["pixtral"]["precision"], "pass": out["human"]["omit"]["pixtral"]["precision"] >= 0.8}
# ---- P19b / P19c: 抱书大评测集
def arm(t): return {k.split("/", 1)[1]: v for k, v in P.items() if k.startswith(t + "/")}
A = {t: arm(t) for t in ("s1base", "s3base", "s1O", "s1F", "s1R", "s2O", "s2F", "s2R", "s3O", "s3F", "s3R")}
def q8(p, pre=None):
    return {k.split("/", 1)[1]: cls(v) for k, v in json.load(open(R + p)).items() if "_a8_" in k and (pre is None or k.startswith(pre))}
Q8base = {1: q8("gen_v3/vl8b.json", "base/"), 2: q8("gen_v3/vl8b.json", "base/"), 3: q8("seeds/vl8b_base_a100.json")}
out["counts"] = {t: dict(collections.Counter(v.values())) for t, v in A.items()}
def pair_test(a1, a2):
    b = c = 0; cl = collections.defaultdict(int)
    for s in (1, 2, 3):
        X, Y = A[f"s{s}{a1}"], A[f"s{s}{a2}"]
        for k in sorted(set(X) & set(Y)):
            x, y = X[k] == "omit", Y[k] == "omit"; b += x and not y; c += y and not x; cl[k.split("_")[0]] += x - y
    return {"a1_only": b, "a2_only": c, "p_mcnemar": mc(b, c), "p_perm": perm(list(cl.values())),
            "omit_a1": sum(A[f"s{s}{a1}"][k] == "omit" for s in (1, 2, 3) for k in A[f"s{s}{a1}"]), "omit_a2": sum(A[f"s{s}{a2}"][k] == "omit" for s in (1, 2, 3) for k in A[f"s{s}{a2}"])}
out["tests"] = {f"{a}_{b}": pair_test(a, b) for a, b in (("O", "F"), ("R", "F"), ("O", "R"))}
out["P19b"] = {"pass": out["tests"]["O_F"]["a1_only"] > out["tests"]["O_F"]["a2_only"] and out["tests"]["O_F"]["p_perm"] < 0.05, **out["tests"]["O_F"]}
def trans(base_src):
    b = c = 0; n = 0; to = {"O": 0, "F": 0, "R": 0}
    for s in (1, 2, 3):
        B = A["s3base" if s == 3 else "s1base"] if base_src == "pixtral" else Q8base[s]
        for k, v in B.items():
            if v != "extra" or k not in A[f"s{s}O"] or k not in A[f"s{s}F"]: continue
            n += 1; o, f = A[f"s{s}O"][k] == "omit", A[f"s{s}F"][k] == "omit"; b += o and not f; c += f and not o
            for a in to: to[a] += A[f"s{s}{a}"].get(k) == "omit"
    return {"n_base_extra": n, "to_omit": to, "O_only": b, "F_only": c, "p_mcnemar": mc(b, c)}
out["trans_pixtral_base"] = trans("pixtral"); out["trans_qwen_base"] = trans("qwen")
t = out["trans_pixtral_base"]; out["P19c"] = {"pass": t["O_only"] > t["F_only"] and t["p_mcnemar"] < 0.05, **t}
json.dump(out, open(R + "paper/j2_stats.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ("n_labels", "P19a", "P19b", "P19c", "trans_qwen_base")}, indent=1))
print(json.dumps(out["human"], indent=1)); print(out["counts"])
