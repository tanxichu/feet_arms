#!/usr/bin/env python3
"""PREREG 修订 37 门槛: 候选独立裁判在 Klein 人评主块 200 张(五人过半)上的总一致率与漏手精度。门槛: 一致 ≥0.85 且漏手精度 ≥0.80。
输出 20T paper/j3_gate.json。"""
import json, glob, collections
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
    if r["set"] != "val" or r["model"] != "klein" or not all(c in H[x] for x in H): continue
    (m, n), = collections.Counter(H[x][c] for x in H).most_common(1); maj[c] = m if n >= 3 else "none"
out = {}
for nm, f in (("internvl35_8b", "j3_ivl_hum.json"), ("mistral_small31_24b", "j3_ms_hum.json"), ("pixtral12b", None)):
    if f: L = {k.split("/", 1)[1].split("_a")[0]: cls(v) for k, v in json.load(open(R + "paper/j2/" + f)).items()}
    else:
        L = {}
        for g in glob.glob(R + "paper/j2/out_*.json"):
            L.update({k.split("/", 1)[1].split("_a")[0]: cls(v) for k, v in json.load(open(g)).items() if k.startswith("hum/")})
    said = [c for c in maj if L.get(c) == "omit"]
    r = {"n": sum(c in L for c in maj), "agree": sum(L.get(c) == maj[c] for c in maj) / len(maj),
         "omit_precision": sum(maj[c] == "omit" for c in said) / max(len(said), 1), "omit_said": len(said),
         "omit_recall": sum(L.get(c) == "omit" for c in maj if maj[c] == "omit") / max(sum(maj[c] == "omit" for c in maj), 1)}
    r["pass"] = r["agree"] >= 0.85 and r["omit_precision"] >= 0.80; out[nm] = r; print(nm, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
json.dump(out, open(R + "paper/j3_gate.json", "w"), indent=1)
