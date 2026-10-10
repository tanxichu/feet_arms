#!/usr/bin/env python3
"""事后诊断(探索性): FLUX 上各检测器(v2 = O 组奖励, v7f = F 组, v7r = R 组)对 8B 判「漏手 / 多手 / 画对」的图打多少分。
奖励 = 检测器分(越高越罚)。检测器若对漏手图打分不高于画对图, 漏手在奖励里就是「免费」的, 补漏手例子也就没起作用。
报: 各类均值、漏手 vs 画对 AUC(>0.5 = 漏手被罚得更多)、多手 vs 画对 AUC。输入 20T flux40/detscore40.json + vl8b_*.json。"""
import json, collections
D = "DATA/flux40/"
def cls(v): T = v.get("TOTAL"); return "ok" if v.get("ok") else ("extra" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
S = json.load(open(D + "detscore40.json")); L = {}
for arm in ("base", "base_big", "O1000", "O1000_big", "F40", "F40_big"):
    for k, v in json.load(open(f"{D}vl8b_{arm}.json")).items(): L[f"{arm}/{k.split('/', 1)[-1]}"] = cls(v)
def auc(pos, neg): return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / max(len(pos) * len(neg), 1)
out = {"n_scored": len(S), "n_joined": sum(k in L for k in S)}
for grp, arms in (("base", ("base", "base_big")), ("all", None)):
    keys = [k for k in S if k in L and (arms is None or k.split("/")[0] in arms)]
    r = {"counts": dict(collections.Counter(L[k] for k in keys))}
    for d in ("v2", "v7f", "v7r"):
        by = {c: [S[k][d] for k in keys if L[k] == c] for c in ("omit", "extra", "ok")}
        r[d] = {"mean": {c: sum(v) / max(len(v), 1) for c, v in by.items()}, "auc_omit_vs_ok": auc(by["omit"], by["ok"]), "auc_extra_vs_ok": auc(by["extra"], by["ok"])}
    out[grp] = r
json.dump(out, open("DATA/paper/flux_detdiag.json", "w"), indent=1); print(json.dumps(out, indent=1))
