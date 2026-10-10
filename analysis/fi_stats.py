#!/usr/bin/env python3
"""PREREG 修订 44: Fi(InternVL 确认的 63 张漏手例子) vs O 种子 1 / Ri / 原 F(v5f) / R(v5r), 大集(训练的人 × 抱书 a8 / 拿花 a9 × 3 噪声), 8B 裁判。
P28a 抱书 Fi < O(McNemar p<0.05); P28b 抱书 Fi < Ri(同上); P28c Fi 多手不多于 O(描述)。另报按人置换 p、拿花、合并。
注意: O/F/R/底座 的图在 108 上出, Fi/Ri 在 151 上出(都是 3090); Fi vs Ri 同机, 是最干净的一对。
输入 20T gen_v3/vl8b*.json + fi44/vl8b_dd_{Fi,Ri}.json; 输出 20T paper/fi_stats.json。"""
import json, random, collections
from math import comb
R = "DATA/"
def cls(v): T = v.get("TOTAL"); return "ok" if v.get("ok") else ("extra" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
def load(p): return {k.split("/", 1)[1]: cls(v) for k, v in json.load(open(R + p)).items()}
g = json.load(open(R + "gen_v3/vl8b.json"))
J = {"base": {k.split("/", 1)[1]: cls(v) for k, v in g.items() if k.startswith("base/")}, "O": {k.split("/", 1)[1]: cls(v) for k, v in g.items() if k.startswith("dd_v2/")},
     "F": load("gen_v3/vl8b_v5f.json"), "R": load("gen_v3/vl8b_v5r.json"), "Fi": load("fi44/vl8b_dd_Fi.json"), "Ri": load("fi44/vl8b_dd_Ri.json")}
import os   # 修订 45: 151 同机对照, 出来了才加
for a in ("O151", "F151", "O151s2", "O151s3", "Ris2", "Ris3"):   # 修订 46 种子 2/3
    if os.path.exists(R + f"fi44/vl8b_dd_{a}.json"): J[a] = load(f"fi44/vl8b_dd_{a}.json")
def mc(b, c): n = b + c; return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def perm(d, it=20000):
    rng = random.Random(0); o = abs(sum(d)); return (sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= o - 1e-9 for _ in range(it)) + 1) / (it + 1)
out = {}
for act in ("a8", "a9", "all"):
    ks = sorted(k for k in J["base"] if (act == "all" or f"_{act}_" in k) and all(k in J[a] for a in J))
    r = {"n": len(ks), "counts": {a: dict(collections.Counter(J[a][k] for k in ks)) for a in J}, "tests": {}}
    for a1, a2 in (("O", "Fi"), ("Ri", "Fi"), ("F", "Fi"), ("R", "Ri"), ("O", "F"), ("base", "Fi")) + ((("O151", "Fi"), ("O151", "Ri"), ("O151", "F151"), ("O", "O151"), ("F", "F151")) if "O151" in J and "F151" in J else ()):
        b = sum(J[a1][k] == "omit" and J[a2][k] != "omit" for k in ks); c = sum(J[a2][k] == "omit" and J[a1][k] != "omit" for k in ks)
        cl = collections.defaultdict(int)
        for k in ks: cl[k.split("_")[0]] += (J[a1][k] == "omit") - (J[a2][k] == "omit")
        r["tests"][f"{a1}_{a2}"] = {"a1_only": b, "a2_only": c, "p_mcnemar": mc(b, c), "p_perm": perm(list(cl.values()))}
    out[act] = r
t = out["a8"]["tests"]; c8 = out["a8"]["counts"]
out["predictions"] = {"P28a": {"pass": t["O_Fi"]["a1_only"] > t["O_Fi"]["a2_only"] and t["O_Fi"]["p_mcnemar"] < 0.05, **t["O_Fi"]},
                      "P28b": {"pass": t["Ri_Fi"]["a1_only"] > t["Ri_Fi"]["a2_only"] and t["Ri_Fi"]["p_mcnemar"] < 0.05, **t["Ri_Fi"]},
                      "P28c": {"extra_Fi": c8["Fi"].get("extra", 0), "extra_O": c8["O"].get("extra", 0)}}
if "O151" in J and "F151" in J:
    out["predictions"].update({k: {"pass": t[p]["a1_only"] > t[p]["a2_only"] and t[p]["p_mcnemar"] < 0.05, **t[p]} for k, p in (("P29a", "O151_Fi"), ("P29b", "O151_Ri"), ("P29c", "O151_F151"))})
# 修订 46 P30: 三种子合并, 每人把各种子 (O151 - Ri) 漏手差相加后按人翻符号置换
_pairs = [("O151", "Ri")] + [(f"O151s{s}", f"Ris{s}") for s in (2, 3) if f"O151s{s}" in J and f"Ris{s}" in J]
if len(_pairs) > 1:
    ks = sorted(k for k in J["base"] if "_a8_" in k and all(k in J[a] for p in _pairs for a in p))
    cl = collections.defaultdict(int); b = c = 0; per = {}
    for a1, a2 in _pairs:
        bb = sum(J[a1][k] == "omit" and J[a2][k] != "omit" for k in ks); cc = sum(J[a2][k] == "omit" and J[a1][k] != "omit" for k in ks)
        per[f"{a1}_{a2}"] = {"a1_only": bb, "a2_only": cc, "p_mcnemar": mc(bb, cc), "omit_a1": sum(J[a1][k] == "omit" for k in ks), "omit_a2": sum(J[a2][k] == "omit" for k in ks)}
        b += bb; c += cc
        for k in ks: cl[k.split("_")[0]] += (J[a1][k] == "omit") - (J[a2][k] == "omit")
    pp = perm(list(cl.values()))
    out["predictions"]["P30"] = {"pass": b > c and pp < 0.05, "n_seeds": len(_pairs), "O_only": b, "Ri_only": c, "p_perm": pp, "per_seed": per}
json.dump(out, open(R + "paper/fi_stats.json", "w"), indent=1)
print(json.dumps(out["predictions"], indent=1)); print({a: out["a8"]["counts"][a] for a in J}); print({a: out["all"]["counts"][a] for a in J})
