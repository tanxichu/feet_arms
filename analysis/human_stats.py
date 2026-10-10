#!/usr/bin/env python3
"""人评第一部分主分析(PREREG 修订 6/27): 校验集 300 张, 五位盲评 R1/R2/R4/R5/R6, 过半(≥3)为多数票。
① 表: 生成器 × 裁判分层类别 → 人的多数票分布; ② Krippendorff α(名义, 四类 + 每类二值); ③ 式(strat) 人校正漏手率 = Σ N_s/N · q̂_s,
   层内按图自助 2 万次给 95% CI, 并给 F−O、F−R 差值的 CI。只读代号文件, 输出只含汇总: 20T paper/human_stats.json。"""
import json, glob, random, collections, itertools
R = "DATA/"; RM = "PRIVATE_RATINGS/"
key = {r["code"]: r for r in json.load(open(RM + "ann_main_key.json"))}
strata = json.load(open(R + "paper/ann_main_valsel.json"))["strata"]
RAT = json.load(open(RM + "rater_files_ann_main.json"))   # 标注者代号 → 答卷文件; 对照表只在本机私有目录, 不进 git(真名不入库)
def marks(p):
    d = json.load(open(p)); d = d["marks"] if isinstance(d, dict) else d; return {x["c"]: x["tags"] for x in d if x.get("tags")}
def h(t): return "comm" if "extra" in t else "omit" if "missing" in t else "clean" if "ok" in t else "other"
H = {r: {c: h(t) for c, t in marks(p).items()} for r, p in RAT.items()}
val = [c for c, r in key.items() if r["set"] == "val" and all(c in H[x] for x in H)]
need = len(H) // 2 + 1; maj = {}
for c in val:
    (m, n), = collections.Counter(H[r][c] for r in H).most_common(1); maj[c] = m if n >= need else "none"
out = {"n_val": len(val), "raters": len(H)}
tab = collections.defaultdict(collections.Counter)
for c in val: tab[f"{key[c]['model']}|{key[c]['mcls']}"][maj[c]] += 1
out["table"] = {k: dict(v) for k, v in tab.items()}
for k, v in sorted(tab.items()): print(k, dict(v))
def alpha(units):   # Krippendorff α, 名义, 无缺失
    vals = sorted({x for u in units for x in u}); o = collections.Counter()
    for u in units:
        m = len(u)
        for a, b in itertools.permutations(range(m), 2): o[(u[a], u[b])] += 1 / (m - 1)
    n = sum(o.values()); nc = collections.Counter()
    for (a, b), w in o.items(): nc[a] += w
    do = sum(w for (a, b), w in o.items() if a != b) / n; de = sum(nc[a] * nc[b] for a in vals for b in vals if a != b) / (n * (n - 1))
    return 1 - do / de
units = [[H[r][c] for r in H] for c in val]
out["alpha"] = {"all": alpha(units)}
for cl in ("clean", "comm", "omit"): out["alpha"][cl] = alpha([[x == cl for x in u] for u in units])
print("alpha", {k: round(v, 3) for k, v in out["alpha"].items()})
# 裁判在每类上的精度(人多数票同意裁判的比例), 裁判类别 unheld→omit, extra→comm, ok→clean
jm = {"unheld": "omit", "extra": "comm", "ok": "clean"}
out["judge_precision"] = {}
for model in ("klein", "sana"):
    for mc, hc in jm.items():
        cs = [c for c in val if key[c]["model"] == model and key[c]["mcls"] == mc]; out["judge_precision"][f"{model}|{hc}"] = [sum(maj[c] == hc for c in cs), len(cs)]
print("precision", out["judge_precision"])
# 式(strat): 人校正漏手率
def est(model, arm, sample):
    tot = sum(v["N"] for k, v in strata.items() if k.startswith(f"{model}|{arm}|")); r = 0.0
    for mc in ("unheld", "extra", "ok"):
        s = sample[(model, arm, mc)]; N = strata[f"{model}|{arm}|{mc}"]["N"]
        r += N / tot * (sum(maj[c] == "omit" for c in s) / len(s) if s else 0)
    return 100 * r
base = {(m, a, mc): [c for c in val if (key[c]["model"], key[c]["arm"], key[c]["mcls"]) == (m, a, mc)] for m, a, mc in {(key[c]["model"], key[c]["arm"], key[c]["mcls"]) for c in val}}
arms = {"klein": ["before", "O", "F", "R"], "sana": ["before", "O", "F2", "R2"]}
rng = random.Random(0); boots = collections.defaultdict(list)
# 10-06 审稿意见: 层内全中(q̂=1)时按图重抽方差为零、区间偏窄 ⇒ 改为每层 q ~ Beta(k+½, n−k+½)(Jeffreys 先验)抽样
def est_q(model, arm, qd):
    tot = sum(v["N"] for k, v in strata.items() if k.startswith(f"{model}|{arm}|"))
    return 100 * sum(strata[f"{model}|{arm}|{mc}"]["N"] / tot * qd[(model, arm, mc)] for mc in ("unheld", "extra", "ok"))
kq = {k: (sum(maj[c] == "omit" for c in v), len(v)) for k, v in base.items()}
for _ in range(20000):
    qd = {k: rng.betavariate(a + 0.5, n - a + 0.5) for k, (a, n) in kq.items()}
    for m, aa in arms.items():
        e = {a: est_q(m, a, qd) for a in aa}
        for a in aa: boots[f"{m}|{a}"].append(e[a])
        boots[f"{m}|O-F"].append(e["O"] - e[aa[2]]); boots[f"{m}|R-F"].append(e[aa[3]] - e[aa[2]])
out["strat"] = {}
for m, aa in arms.items():
    pt = {a: est(m, a, base) for a in aa}
    for k in [*aa, "O-F", "R-F"]:
        v = pt[k] if k in pt else (pt["O"] - pt[aa[2]] if k == "O-F" else pt[aa[3]] - pt[aa[2]])
        b = sorted(boots[f"{m}|{k}"]); out["strat"][f"{m}|{k}"] = {"est": v, "ci95": (b[500], b[19499])}
    print(m, {k: (round(v["est"], 1), [round(x, 1) for x in v["ci95"]]) for k, v in out["strat"].items() if k.startswith(m)})
json.dump(out, open(R + "paper/human_stats.json", "w"), indent=1)
