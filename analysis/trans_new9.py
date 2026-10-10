#!/usr/bin/env python3
"""修订 33/34/36 的配对转移表: 四个新动作, 底座 → O / F9(四种子合并) / R9(种子 1)。底座多手图变成漏手的张数与比例。输出 20T paper/trans_new9.json。"""
import json
D4 = "DATA/new4/"; D9 = "DATA/new9/"
def cls(v): T = v.get("TOTAL"); return "ok" if v.get("ok") else ("extra" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
def L(p): return {k.split("/", 1)[1]: cls(v) for k, v in json.load(open(p)).items()}
B = L(D4 + "vl8b_base.json")
ARMS = {"O": [L(D4 + "vl8b_O.json")] + [L(f"{D9}vl8b_Os{s}.json") for s in (2, 3, 4)], "F9": [L(f"{D9}vl8b_F9.json")] + [L(f"{D9}vl8b_F9s{s}.json") for s in (2, 3, 4)], "R9": [L(D9 + "vl8b_R9.json")]}
out = {}
for act in ("12", "13", "14", "15", "all"):
    r = {}
    for a, Xs in ARMS.items():
        n = bc = co = cc = 0
        for X in Xs:
            for k, b in B.items():
                if (act != "all" and f"_a{act}_" not in k) or k not in X: continue
                n += 1
                if b == "extra": bc += 1; co += X[k] == "omit"; cc += X[k] == "ok"
        r[a] = {"seeds": len(Xs), "n": n, "base_comm": bc, "comm_to_omit": co, "comm_to_clean": cc, "pct_to_omit": round(100 * co / max(bc, 1), 1)}
    out[act] = r
json.dump(out, open("DATA/paper/trans_new9.json", "w"), indent=1)
for act, r in out.items(): print(act, {a: (v["base_comm"], v["comm_to_omit"], v["pct_to_omit"]) for a, v in r.items()})
