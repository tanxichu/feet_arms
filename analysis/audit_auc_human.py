#!/usr/bin/env python3
"""指标体检 · 人评真值版(PREREG 修订 6 的主分析)。真值 = 有效标注者(修订 27 起 R1/R2/R4/R5/R6 五人)的过半票, 主类口径 多手 > 漏手 > 画对 > 其它;
不过半的剔除; 多数票为「其它」的不进 AUC。只用第一部分 360 张里的 val 300 张(已确认多手的 60 张是另选的, 不进)。
每个指标定向成「分越高越像有毛病」, 对「画对」分别算 AUC_多手 与 AUC_漏手, 按图自助法 2000 次 95% CI。分 Klein / SANA / 合并。
输出 20T paper/audit_scores/audit_auc_human.json。标注文件路径只在本机, 名字不进输出。"""
import json, random, os, glob, collections
D = "DATA/paper/audit_scores/"; RM = "PRIVATE_RATINGS/"
items = {x["code"]: x for x in json.load(open(D + "audit_items.json"))}
ARMS = [a for a in os.environ.get("AUDIT_ARMS", "").split(",") if a]; TAG = os.environ.get("AUDIT_TAG", "")
RATERS = json.load(open(RM + "rater_files_ann_main.json"))   # 标注者代号 → 答卷文件; 对照表只在本机私有目录, 不进 git  # 修订 27: 五位盲评
def marks(p):
    d = json.load(open(p)); d = d["marks"] if isinstance(d, dict) else d; return {x["c"]: x["tags"] for x in d if x.get("tags")}
H = {r: marks(p) for r, p in RATERS.items()}
def h(t): return "comm" if "extra" in t else "omit" if "missing" in t else "clean" if "ok" in t else "other"
lab = {}; ties = 0
for c, it in items.items():
    if it["set"] != "val": continue
    if ARMS and it["arm"] not in ARMS: continue   # 10-06 审稿意见: 只用某些组的图(如只用冻结模型的图, 排除被检测器当奖励优化过的组)
    v = [h(H[r][c]) for r in H if c in H[r]]
    if len(v) < len(H): continue
    (m, n), = collections.Counter(v).most_common(1)
    if n < len(H) // 2 + 1: ties += 1; continue  # 过半(5 人里 ≥3)才算, 否则剔除
    if m != "other": lab[c] = m
# 复用 audit_auc_judge.py 的指标装载与 AUC 函数
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_auc_judge.py")).read()
ns = {"__file__": __file__}; exec(src.split("out = {}")[0].replace('lab[code] =', '_unused ='), ns)
M, auc, boot = ns["M"], ns["auc"], ns["boot"]
out = {"_n": {"labeled": len(lab), "ties_dropped": ties, "dist": dict(collections.Counter(lab.values()))}}
print("多数票:", out["_n"])
for name, sc in M.items():
    for model in ("klein", "sana", "all"):
        codes = [c for c in sc if c in lab and (model == "all" or items[c]["model"] == model)]
        g = {l: [sc[c] for c in codes if lab[c] == l] for l in ("clean", "comm", "omit")}
        r = {"n": {l: len(v) for l, v in g.items()}}
        for l in ("comm", "omit"):
            a = auc(g[l], g["clean"]); r["auc_" + l] = None if a is None else round(a, 3); r["ci_" + l] = boot(g[l], g["clean"]) if a is not None else None
        r["gap"] = None if None in (r["auc_comm"], r["auc_omit"]) else round(r["auc_comm"] - r["auc_omit"], 3)
        out[f"{name}|{model}"] = r
        print(f"{name:16s} {model:5s} n={r['n']}  多手 {r['auc_comm']} {r['ci_comm']}  漏手 {r['auc_omit']} {r['ci_omit']}  差 {r['gap']}", flush=True)
json.dump(out, open(D + f"audit_auc_human{TAG}.json", "w"), indent=1)
