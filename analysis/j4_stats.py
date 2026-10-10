#!/usr/bin/env python3
"""PREREG 修订 39: InternVL3.5-8B 在 SANA 上当保守漏手计数器。门槛: 100 张 SANA 人评图(五人过半)上判漏手精度 ≥0.8 且 ≥10 张。
过门槛才算 P23: SANA 拿花 三种子合并 F2 漏手少于 O(按人翻符号置换 p<0.05)。输出 20T paper/j4_stats.json。"""
import json, glob, random, collections, os
from math import comb
R = "DATA/"; RM = "PRIVATE_RATINGS/"
def cls(v): T = v.get("TOTAL"); return "ok" if v.get("ok") else ("extra" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
key = {r["code"]: r for r in json.load(open(RM + "ann_main_key.json"))}
RAT = json.load(open(RM + "rater_files_ann_main.json"))   # 标注者代号 → 答卷文件; 对照表只在本机私有目录, 不进 git(真名不入库)
def marks(p):
    d = json.load(open(p)); d = d["marks"] if isinstance(d, dict) else d; return {x["c"]: x["tags"] for x in d if x.get("tags")}
def h(t): return "extra" if "extra" in t else "omit" if "missing" in t else "ok" if "ok" in t else "other"
H = {r: {c: h(t) for c, t in marks(p).items()} for r, p in RAT.items()}
maj = {}
for c, r in key.items():
    if r["set"] != "val" or r["model"] != "sana" or not all(c in H[x] for x in H): continue
    (m, n), = collections.Counter(H[x][c] for x in H).most_common(1); maj[c] = m if n >= 3 else "none"
L = {k.split("/", 1)[1].split("_a")[0]: cls(v) for k, v in json.load(open(R + "paper/j3/ivl_sana_hum.json")).items()}
said = [c for c in maj if L.get(c) == "omit"]
gate = {"n": len(maj), "omit_said": len(said), "omit_precision": sum(maj[c] == "omit" for c in said) / max(len(said), 1),
        "omit_recall": sum(L.get(c) == "omit" for c in maj if maj[c] == "omit") / max(sum(maj[c] == "omit" for c in maj), 1),
        "agree": sum(L.get(c) == maj[c] for c in maj) / len(maj)}
gate["pass"] = gate["omit_precision"] >= 0.8 and gate["omit_said"] >= 10
out = {"gate": gate}
F = R + "paper/j3/ivl_sana_arms.json"
if gate["pass"] and os.path.exists(F):
    P = {k: cls(v) for k, v in json.load(open(F)).items()}
    A = collections.defaultdict(dict)
    for k, v in P.items(): t, i = k.split("/", 1); A[t][i] = v
    def mc(b, c): n = b + c; return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
    def perm(d, it=20000):
        rng = random.Random(0); o = abs(sum(d)); return (sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= o - 1e-9 for _ in range(it)) + 1) / (it + 1)
    def arm(a, s): return A[a if s == 1 else f"{a}_s{s}"]
    def test(a1, a2):
        b = c = 0; cl = collections.defaultdict(int)
        for s in (1, 2, 3):
            X, Y = arm(a1, s), arm(a2, s)
            for k in sorted(set(X) & set(Y)):
                x, y = X[k] == "omit", Y[k] == "omit"; b += x and not y; c += y and not x; cl[k.split("_")[0]] += x - y
        return {"a1_only": b, "a2_only": c, "p_mcnemar": mc(b, c), "p_perm": perm(list(cl.values()))}
    out["omit"] = {t: sum(x == "omit" for x in v.values()) for t, v in A.items()}
    out["tests"] = {f"{a}_{b}": test(a, b) for a, b in (("O", "F2"), ("R2", "F2"), ("O", "R2"))}
    t = out["tests"]["O_F2"]; out["P23"] = {"pass": t["a1_only"] > t["a2_only"] and t["p_perm"] < 0.05, **t}
json.dump(out, open(R + "paper/j4_stats.json", "w"), indent=1); print(json.dumps(out, indent=1)[:1500])
