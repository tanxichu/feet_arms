#!/usr/bin/env python3
"""论文里所有机器判定的数字都从这里算出来, 写成 numbers.tex 的宏; 正文不许手改数字。
来源: DATA/ 下各 vl8b_*.json(Qwen3-VL-8B 按动作判「两件事各几只手」)。
用法: python3 paper_numbers.py  →  numbers.tex"""
import json, collections
from math import comb
R = "DATA/"
def cls(v):
    T = v.get("TOTAL"); return "ok" if v.get("ok") else ("extra" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
def load(p, prefix=None, act=None):
    d = json.load(open(R + p)); d = {k: v for k, v in d.items() if (prefix is None or k.startswith(prefix)) and (act is None or f"_{act}_" in k)}
    c = collections.Counter(cls(v) for v in d.values()); c["n"] = len(d); return c
def fisher(a, n1, b, n2):
    n = n1 + n2; c1 = a + b; den = comb(n, c1); p0 = comb(n1, a) * comb(n2, c1 - a) / den; s = 0
    for x in range(max(0, c1 - n2), min(n1, c1) + 1):
        p = comb(n1, x) * comb(n2, c1 - x) / den
        if p <= p0 * (1 + 1e-9): s += p
    return s
M = {}
def put(name, v): M[name] = v
K = {("base", 1): ("gen_v3/vl8b.json", "base/"), ("O", 1): ("gen_v3/vl8b.json", "dd_v2/"), ("F", 1): ("gen_v3/vl8b_v5f.json", None), ("R", 1): ("gen_v3/vl8b_v5r.json", None),
     ("O", 2): ("seeds/vl8b_dd_O_s2.json", None), ("F", 2): ("seeds/vl8b_dd_F_s2.json", None), ("R", 2): ("seeds/vl8b_dd_R_s2.json", None),
     ("O", 3): ("seeds/vl8b_dd_O_s3_a100.json", None), ("F", 3): ("seeds/vl8b_dd_F_s3_a100.json", None), ("R", 3): ("seeds/vl8b_dd_R_s3_a100.json", None)}
roman = {1: "i", 2: "ii", 3: "iii"}
for (arm, s), (p, pre) in K.items():
    for act, an in (("a8", "Book"), ("a9", "Flower")):
        c = load(p, pre, act); tag = f"K{an}{arm}{roman[s]}"
        for k in ("ok", "extra", "omit", "n"): put(tag + {"ok": "Ok", "extra": "Extra", "omit": "Omit", "n": "N"}[k], c[k])
b = load(*K[("base", 1)], "a8")
for s in (1, 2, 3):
    o, f, r = (load(*K[(a, s)], "a8") for a in ("O", "F", "R"))
    put(f"pOF{roman[s]}", f"{fisher(o['omit'], o['n'], f['omit'], f['n']):.2g}"); put(f"pRF{roman[s]}", f"{fisher(r['omit'], r['n'], f['omit'], f['n']):.2g}")
    put(f"pOR{roman[s]}", f"{fisher(o['omit'], o['n'], r['omit'], r['n']):.2g}"); put(f"pBO{roman[s]}", f"{fisher(b['omit'], b['n'], o['omit'], o['n']):.2g}")
    put(f"pBF{roman[s]}", f"{fisher(b['omit'], b['n'], f['omit'], f['n']):.2g}")
for arm, f in (("base", "vl8b_base"), ("O", "vl8b_limbs_dd_v2_s2000"), ("F", "vl8b_limbs_dd_v5f_s2000"), ("R", "vl8b_limbs_dd_v5r_s2000")):
    c = load(f"klein_hold_judge/{f}.json", None, "a8")
    for k in ("ok", "extra", "omit", "n"): put("H" + arm + {"ok": "Ok", "extra": "Extra", "omit": "Omit", "n": "N"}[k], c[k])
h = {a: load(f"klein_hold_judge/{f}.json", None, "a8") for a, f in (("O", "vl8b_limbs_dd_v2_s2000"), ("F", "vl8b_limbs_dd_v5f_s2000"), ("B", "vl8b_base"))}
put("pHOF", f"{fisher(h['O']['omit'], h['O']['n'], h['F']['omit'], h['F']['n']):.2g}"); put("pHBO", f"{fisher(h['B']['omit'], h['B']['n'], h['O']['omit'], h['O']['n']):.2g}")
S = {("base", 1): "base", ("O", 1): "O", ("F", 1): "F2", ("R", 1): "R2", ("O", 2): "O_s2", ("F", 2): "F2_s2", ("R", 2): "R2_s2", ("O", 3): "O_s3", ("F", 3): "F2_s3", ("R", 3): "R2_s3", ("Fk", 1): "F", ("Rk", 1): "R"}
for (arm, s), f in S.items():
    for act, an in (("a8", "Book"), ("a9", "Flower")):
        c = load(f"sana_paper/vl8b_{f}.json", None, act); tag = f"S{an}{arm}{roman[s]}"
        for k in ("ok", "extra", "omit", "n"): put(tag + {"ok": "Ok", "extra": "Extra", "omit": "Omit", "n": "N"}[k], c[k])
for s in (1, 2, 3):
    o, f, r = (load(f"sana_paper/vl8b_{S[(a, s)]}.json", None, "a9") for a in ("O", "F", "R"))
    put(f"pSOF{roman[s]}", f"{fisher(o['omit'], o['n'], f['omit'], f['n']):.2g}"); put(f"pSRF{roman[s]}", f"{fisher(r['omit'], r['n'], f['omit'], f['n']):.2g}")

# 三个种子合并(每个种子同一批题, 合并后精确检验; 种子间差异另报范围)
def pool(getter, arms):
    return {a: (sum(getter(a, s)["omit"] for s in (1, 2, 3)), sum(getter(a, s)["n"] for s in (1, 2, 3)), sum(getter(a, s)["ok"] for s in (1, 2, 3))) for a in arms}
kp = pool(lambda a, s: load(*K[(a, s)], "a8"), ("O", "F", "R"))
for a, (om, n, ok) in kp.items(): put(f"KBookPool{a}Omit", om); put(f"KBookPool{a}N", n); put(f"KBookPool{a}Ok", ok)
put("pPoolOF", f"{fisher(kp['O'][0], kp['O'][1], kp['F'][0], kp['F'][1]):.2g}"); put("pPoolRF", f"{fisher(kp['R'][0], kp['R'][1], kp['F'][0], kp['F'][1]):.2g}"); put("pPoolOR", f"{fisher(kp['O'][0], kp['O'][1], kp['R'][0], kp['R'][1]):.2g}")
put("pPoolOkRF", f"{fisher(kp['R'][2], kp['R'][1], kp['F'][2], kp['F'][1]):.2g}"); put("pPoolOkOF", f"{fisher(kp['O'][2], kp['O'][1], kp['F'][2], kp['F'][1]):.2g}")
sp = pool(lambda a, s: load(f"sana_paper/vl8b_{S[(a, s)]}.json", None, "a9"), ("O", "F", "R"))
for a, (om, n, ok) in sp.items(): put(f"SFlowerPool{a}Omit", om); put(f"SFlowerPool{a}N", n)
put("pSPoolOF", f"{fisher(sp['O'][0], sp['O'][1], sp['F'][0], sp['F'][1]):.2g}"); put("pSPoolRF", f"{fisher(sp['R'][0], sp['R'][1], sp['F'][0], sp['F'][1]):.2g}")

# 配对转移: 同一 (人, 动作, 采样种子) 在 base 与各组下的判定(只用抱书 a8); 三个训练种子合并
import re
def labels(p, pre=None):
    d = json.load(open(R + p)); out = {}
    for k, v in d.items():
        if "_a8_" not in k or (pre and not k.startswith(pre)): continue
        out[k.split("/", 1)[1] if "/" in k else k] = cls(v)
    return out
BL = labels("gen_v3/vl8b.json", "base/"); BL3 = labels("seeds/vl8b_base_a100.json")
for arm in ("O", "F", "R"):
    t = collections.Counter()
    for s in (1, 2, 3):
        L = labels(*K[(arm, s)]) if K[(arm, s)][1] is None else labels(K[(arm, s)][0], K[(arm, s)][1])
        BLs = BL3 if s == 3 else BL   # 种子 3 在 A100 上出图, 用 A100 上同噪声的底座
        for k, b in BLs.items():
            if k in L: t[(b, L[k])] += 1
    for b in ("extra", "ok", "omit"):
        for x in ("extra", "ok", "omit"):
            put(f"T{arm}{ {'extra':'C','ok':'K','omit':'M'}[b]}{ {'extra':'C','ok':'K','omit':'M'}[x]}", t[(b, x)])
    put(f"T{arm}CN", sum(t[("extra", x)] for x in ("extra", "ok", "omit", "other")))
# 训练曲线: 各组自己的奖励(检测器最高分均值, 固定池前 60 个)随步数; 三个种子取均值
import glob as _g
LG = R + "train_logs/"
runs = {"O": ["limbs_dd_v2", "limbs_dd_O_s2", "limbs_dd_O_s3"], "F": ["limbs_dd_v5f", "limbs_dd_F_s2", "limbs_dd_F_s3"], "R": ["limbs_dd_v5r", "limbs_dd_R_s2", "limbs_dd_R_s3"]}
for arm, rs in runs.items():
    acc = collections.defaultdict(list)
    for r in rs:
        for ln in open(LG + r + ".log"):
            m = re.search(r"\[固定样本 (s?\w+)\] 最高分均值 ([0-9.]+)", ln)
            if m: acc[0 if m.group(1) == "base" else int(m.group(1)[1:])].append(float(m.group(2)))
    for st, v in acc.items(): put(f"Curve{arm}{ {0:'a',500:'b',1000:'c',1500:'d',2000:'e'}[st]}", f"{sum(v)/len(v):.3f}")

# 公开检测器 HADM-G 独立复核(留出的人, 全部 10 个动作, 每组 516 张, 种子 1): 判「多 X」/「缺 X」的张数
hs = json.load(open(R + "hadm_hold_summary.json"))
for k, tag in (("base", "Base"), ("O1", "O"), ("F1", "F"), ("R1", "R")):
    put(f"Hadm{tag}Extra", hs[k]["extra50"]); put(f"Hadm{tag}Miss", hs[k]["missing30"]); put(f"Hadm{tag}N", hs[k]["n"])
hm = json.load(open(R + "paper/heatmap_max.json")); hv = list(hm.values())
put("HeatBaseVtwo", hv[0]["v2"]); put("HeatBaseVfive", hv[0]["v5f"]); put("HeatOaVtwo", hv[1]["v2"]); put("HeatOaVfive", hv[1]["v5f"]); put("HeatObVfive", hv[2]["v5f"])

for arm in ("O", "F", "R"):
    put(f"KBookPool{arm}Extra", sum(load(*K[(arm, s)], "a8")["extra"] for s in (1, 2, 3)))
put("KBookbasePoolExtra", 3 * load(*K[("base", 1)], "a8")["extra"])
put("KBookbasePoolOmit", 3 * load(*K[("base", 1)], "a8")["omit"])   # 汇总表用, 同 Extra 的口径(种子 1 冻结图 ×3)

put("PoolOFdiffpp", f"{100*(kp['O'][0]-kp['F'][0])/kp['O'][1]:.1f}")
put("HoldIds", len({k.split("/")[1].split("_")[0] for k in json.load(open(R + "klein_hold_judge/vl8b_base.json")) if "_a8_" in k}))  # 只数有抱书题的人(10-05 修: 原来含拿花题的人, 写成 28, 与配对检验的 21 对不上)

# 配对检验(paired_stats.py 生成 paper/paired_stats.json): 每种子精确 McNemar + 三种子合并按人聚类置换检验
P = json.load(open(R + "paper/paired_stats.json"))
fp = lambda p: "<10^{-4}" if p < 1e-4 else ("=" + f"{p:.2g}")
for key, v in P.items():
    model, mode, pair = key.split("_"); tag = {"klein": "K", "sana": "S", "hold": "H"}[model] + {"strict": "", "loose": "L"}[mode] + pair.replace("base", "B")
    put(f"pp{tag}", fp(v["pooled"]["p_perm_by_person"])); put(f"pp{tag}Clus", v["pooled"]["clusters"])
    for x in v["per_seed"]:
        put(f"pm{tag}{roman[x['seed']]}", fp(x["p"])); put(f"pm{tag}{roman[x['seed']]}b", x["a1_only"]); put(f"pm{tag}{roman[x['seed']]}c", x["a2_only"])
    put(f"pp{tag}A", v["pooled"]["a1"]); put(f"pp{tag}Bn", v["pooled"]["a2"])
    put(f"dd{tag}", f"{v['pooled']['diff_pp']:.1f}"); put(f"ci{tag}", f"[{v['pooled']['ci95_pp_by_person'][0]:.1f}, {v['pooled']['ci95_pp_by_person'][1]:.1f}]")
# 式(2) 宽口径下只画出一只手(或零只)而判不对的张数
import glob as _gg
def _fewer(globs):
    n = 0
    for gp in globs:
        for p in _gg.glob(R + gp):
            for v in json.load(open(p)).values():
                T = v.get("TOTAL")
                if not v.get("ok") and T is not None and T < 2: n += 1
    return n
put("FewerKlein", _fewer(["gen_v3/vl8b*.json", "seeds/vl8b*.json"])); put("FewerSana", _fewer(["sana_paper/vl8b*.json"]))
# 转移表: 补 other 行与确切分母
for arm in ("O", "F", "R"):
    t = collections.Counter()
    for s in (1, 2, 3):
        L = labels(*K[(arm, s)]) if K[(arm, s)][1] is None else labels(K[(arm, s)][0], K[(arm, s)][1])
        for k, b in (BL3 if s == 3 else BL).items():
            if k in L: t[(b, L[k])] += 1
    put(f"T{arm}CO", t[("extra", "other")]); put(f"T{arm}KN", sum(t[("ok", x)] for x in ("extra", "ok", "omit", "other")))

# 留出的人(种子 1)也按同一张题配对: 精确 McNemar
from math import comb as _c
def _mc(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(_c(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def _hl(f):
    d = json.load(open(R + f"klein_hold_judge/{f}.json")); return {k.split("/", 1)[-1]: cls(v) == "omit" for k, v in d.items() if "_a8_" in k}
_HB, _HO, _HF = _hl("vl8b_base"), _hl("vl8b_limbs_dd_v2_s2000"), _hl("vl8b_limbs_dd_v5f_s2000")
def _hp(A, B):
    ks = set(A) & set(B); b = sum(A[k] and not B[k] for k in ks); c = sum(B[k] and not A[k] for k in ks); return fp(_mc(b, c))
put("pmHOF", _hp(_HO, _HF)); put("pmHBO", _hp(_HB, _HO)); put("pmHKeys", len(set(_HO) & set(_HF)))
for v_ in P.values(): pass
put("ppHOFN", P["hold_strict_OF"]["pooled"]["n"])
_hb = {k: v for k, v in json.load(open(R + "klein_hold_judge/vl8b_base_a100.json")).items() if "_a8_" in k}
put("HbaseAOmit", sum(cls(v) == "omit" for v in _hb.values()))
# 同一噪声、两种显卡(RTX 3090 / A100)出的底座图, 裁判判定一致的张数(抱书)
_g = {k: cls(v) for k, v in json.load(open(R + "gen_v3/vl8b.json")).items() if k.startswith("base/") and "_a8_" in k}
_g = {k.split("/", 1)[1]: v for k, v in _g.items()}
_a = {k.split("/", 1)[1]: cls(v) for k, v in json.load(open(R + "seeds/vl8b_base_a100.json")).items() if "_a8_" in k}
_ks = set(_g) & set(_a); put("GpuAgree", sum(_g[k] == _a[k] for k in _ks)); put("GpuN", len(_ks))

# 人评(PREREG 修订 6/24/27): 第一部分 360 张五位盲评两两 κ; 错误去向复核 120 张四位盲评多数票。只读代号文件, 不输出名字。
import glob as _gl, itertools as _it, collections as _co
_RM = "PRIVATE_RATINGS/"
def _marks(p_):
    d_ = json.load(open(p_)); d_ = d_["marks"] if isinstance(d_, dict) else d_; return {x["c"]: x["tags"] for x in d_ if x.get("tags")}
def _h4(t): return "extra" if "extra" in t else "missing" if "missing" in t else "ok" if "ok" in t else "other"
_HR = json.load(open(_RM + "rater_files_ann_main.json"))   # 标注者代号 → 答卷文件; 对照表只在本机私有目录, 不进 git(真名不入库)
_HL = {r: {c: _h4(t) for c, t in _marks(f).items()} for r, f in _HR.items()}
_cm = set.intersection(*[set(v) for v in _HL.values()])
def _kap(a, b):
    n = len(_cm); po = sum(a[c] == b[c] for c in _cm) / n; ca = _co.Counter(a[c] for c in _cm); cb = _co.Counter(b[c] for c in _cm)
    pe = sum(ca[x] * cb[x] for x in ca) / n / n; return (po - pe) / (1 - pe)
_ks = [_kap(_HL[a], _HL[b]) for a, b in _it.combinations(_HL, 2)]
put("HumN", len(_HL)); put("HumImgs", len(_cm)); put("HumKmin", f"{min(_ks):.2f}"); put("HumKmax", f"{max(_ks):.2f}")
_T = json.load(open(R + "paper/ann_trans_result.json"))
put("TrHumN", len(_T["raters"])); _mj = _T["majority"]
put("TrHumOMiss", _mj["trans"]["O"].get("missing", 0)); put("TrHumFMiss", _mj["trans"]["F"].get("missing", 0))
put("TrHumOOnly", _mj["paired"]["O_only_missing"]); put("TrHumFOnly", _mj["paired"]["F_only_missing"]); put("TrHumP", fp(_mj["paired"]["p_mcnemar"]))
put("TrHumPairs", 60); put("TrJudOOnly", _T["judge"]["paired"]["O_only_missing"]); put("TrJudFOnly", _T["judge"]["paired"]["F_only_missing"])
# 指标体检(人评真值版, Klein): 对「画对」的 AUC
_A = json.load(open(R + "paper/audit_scores/audit_auc_human.json"))
for _k, _n in (("locdet_v2", "VTwo"), ("neg_pickscore", "Pick"), ("diffdoctor_max", "DD"), ("artifactreward", "AR"), ("hadm_g_any", "HADM"), ("locdet_v5f", "VFiveF")):
    put(f"Aud{_n}Cm", f"{_A[_k + '|klein']['auc_comm']:.2f}"); put(f"Aud{_n}Om", f"{_A[_k + '|klein']['auc_omit']:.2f}")

# OP 组(修订 15)三种子与新动作测试(修订 16)
_OP = json.load(open(R + "paper/op_stats.json"))["rates"]
put("OPExtra", sum(_OP[f"OP{s}"]["extra"] for s in (1, 2, 3))); put("OPBaseExtra", sum(_OP[f"base{s}"]["extra"] for s in (1, 2, 3)))
put("OPOmit", sum(_OP[f"OP{s}"]["omit"] for s in (1, 2, 3))); put("OPBaseOmit", sum(_OP[f"base{s}"]["omit"] for s in (1, 2, 3)))
put("OPN", sum(_OP[f"OP{s}"]["n"] for s in (1, 2, 3)))
_NA = json.load(open(R + "paper/newact_stats.json"))
put("NAppRF", fp(_NA["all|all|strict|RF"]["pooled"]["p_perm_by_person"])); put("NAppOF", fp(_NA["all|all|strict|OF"]["pooled"]["p_perm_by_person"]))
put("NAOPTenOmit", _NA["10|all|strict|baseOP"]["pooled"]["a2"]); put("NABaseTenOmit", _NA["10|all|strict|baseOP"]["pooled"]["a1"]); put("NATenN", _NA["10|all|strict|baseOP"]["pooled"]["n"])

# 人评第一部分主分析(human_stats.py)、指标体检全表、FLUX(flux_stats.py)
_HS = json.load(open(R + "paper/human_stats.json"))
_rn = {"clean": "Cl", "comm": "Cm", "omit": "Om", "other": "Ot", "none": "No"}
for _k, _v in _HS["table"].items():
    _m, _c = _k.split("|"); _p = ("K" if _m == "klein" else "S") + {"unheld": "Om", "extra": "Cm", "ok": "Cl"}[_c]
    put(f"HT{_p}N", sum(_v.values()))
    for _h, _s in _rn.items(): put(f"HT{_p}{_s}", _v.get(_h, 0))
for _k, _v in _HS["alpha"].items(): put("HA" + {"all": "All", "clean": "Cl", "comm": "Cm", "omit": "Om"}[_k], f"{_v:.2f}")
for _k, _v in _HS["strat"].items():
    _m, _a = _k.split("|"); _n = ("K" if _m == "klein" else "S") + {"before": "base", "O": "O", "F": "F", "R": "R", "F2": "F", "R2": "R", "O-F": "OF", "R-F": "RF"}[_a]
    put(f"HS{_n}", f"{_v['est']:.1f}"); put(f"HS{_n}ci", f"[{_v['ci95'][0]:.1f}, {_v['ci95'][1]:.1f}]")
for _k, _v in _HS["judge_precision"].items():
    put("JP" + ("K" if _k.startswith("klein") else "S") + {"omit": "Om", "comm": "Cm", "clean": "Cl"}[_k.split("|")[1]], f"{_v[0]}/{_v[1]}")
for _k, _n in (("hadm_g_any", "HADM"), ("locdet_v2", "VTwo"), ("locdet_v5f", "VFiveF"), ("neg_imagereward", "IR"), ("neg_hpsv2", "HPS"), ("neg_pickscore", "Pick"), ("neg_clip", "CLIP"), ("diffdoctor_max", "DD"), ("artifactreward", "AR"), ("neg_vqascore", "VQA"), ("neg_hpsv3", "HPSthree")):
    _r = _A[_k + "|klein"]; put(f"Aud{_n}Cm", f"{_r['auc_comm']:.2f}"); put(f"Aud{_n}Om", f"{_r['auc_omit']:.2f}"); put(f"Aud{_n}G", f"{_r['gap']:+.2f}".replace("+", "$+$").replace("-", "$-$"))
    put(f"Aud{_n}Cmci", "{{\\tiny[{:.2f}, {:.2f}]}}".format(*_r["ci_comm"])); put(f"Aud{_n}Omci", "{{\\tiny[{:.2f}, {:.2f}]}}".format(*_r["ci_omit"]))
put("AudNcl", _A["locdet_v2|klein"]["n"]["clean"]); put("AudNcm", _A["locdet_v2|klein"]["n"]["comm"]); put("AudNom", _A["locdet_v2|klein"]["n"]["omit"])
_FX = json.load(open(R + "paper/flux_stats.json"))
_fr = _FX["train|a8"]["rate"]
for _a in ("base", "O", "F", "R"): put(f"FX{_a}Omit", _fr[_a]["omit"]); put(f"FX{_a}Extra", _fr[_a]["extra"])
put("FXN", _fr["base"]["n"]); put("FXpOF", fp(_FX["train|a8"]["tests"]["OF"]["p_perm_by_person"])); put("FXpBO", fp(_FX["train|a8"]["tests"]["baseO"]["p_perm_by_person"]))
_na = json.load(open(R + "paper/newact_stats.json"))
put("NAOOmit", _na["all|all|strict|OF"]["pooled"]["a1"]); put("NAFOmit", _na["all|all|strict|OF"]["pooled"]["a2"]); put("NAROmit", _na["all|all|strict|RF"]["pooled"]["a1"]); put("NAN", _na["all|all|strict|OF"]["pooled"]["n"])
put("NAciOF", "[{:.1f}, {:.1f}]".format(*_na["all|all|strict|OF"]["pooled"]["ci95_pp_by_person"])); put("NAppBO", fp(_na["all|all|strict|baseO"]["pooled"]["p_perm_by_person"]))
put("NABaseOmit", _na["all|all|strict|baseO"]["pooled"]["a1"])
put("NAElevenOPOmit", _na["11|all|strict|baseOP"]["pooled"]["a2"]); put("NAElevenBaseOmit", _na["11|all|strict|baseOP"]["pooled"]["a1"])
_op = json.load(open(R + "paper/op_stats.json"))
put("OPppOOP", fp(_op["OOP"]["pooled"]["p_perm_by_person"])); put("OPciOPF", "[{:.1f}, {:.1f}]".format(*_op["OPF"]["pooled"]["ci95_pp_by_person"])); put("OPOOmit", _op["OOP"]["pooled"]["a1"]); put("OPFOmit", _op["OPF"]["pooled"]["a2"])
put("OPOk", sum(_OP[f"OP{s}"]["ok"] for s in (1, 2, 3))); put("OPBaseOk", sum(_OP[f"base{s}"]["ok"] for s in (1, 2, 3)))

# 漏手探针(配对: 同人同提示同噪声, 画对 vs 漏手/多手; paper/probe/probe_result.json)
_PB = json.load(open(R + "paper/probe/probe_result.json"))["metrics"]
put("PbNom", _PB["locdet_v2"]["omit"]["all"]["n_pairs"]); put("PbNcm", _PB["locdet_v2"]["comm"]["all"]["n_pairs"])
for _k, _n in (("locdet_v2", "VTwo"), ("diffdoctor_mean", "DDm"), ("neg_pickscore", "Pick"), ("artifactreward", "AR"), ("hadm_g_any", "HADM")):
    _o = _PB[_k]["omit"]["all"]; _c = _PB[_k]["comm"]["all"]
    put(f"Pb{_n}Om", f"{_o['acc']:.2f}"); put(f"Pb{_n}Omci", "[{:.2f}, {:.2f}]".format(*_o["ci95"])); put(f"Pb{_n}Cm", f"{_c['acc']:.2f}")
_x = _PB["locdet_v2"]["omit"]["excl_arm_O"]; put("PbVTwoOmExcl", f"{_x['acc']:.2f}"); put("PbVTwoOmExclN", _x["n_pairs"])

# 四个新训练动作(修订 29)
_N4 = json.load(open(R + "paper/new4_stats.json"))
for _a in ("12", "14", "all"):
    _t = _N4[_a]["tests"]["baseO"]; _n = {"12": "Tw", "14": "Fo", "all": "All"}[_a]
    put(f"NF{_n}BO", f"{_t['a1_only']}"); put(f"NF{_n}OB", f"{_t['a2_only']}"); put(f"NF{_n}pBO", fp(_t["p_mcnemar"]))
    put(f"NF{_n}OF", f"{_N4[_a]['tests']['OF']['a1_only']}"); put(f"NF{_n}FO", f"{_N4[_a]['tests']['OF']['a2_only']}"); put(f"NF{_n}pOF", fp(_N4[_a]["tests"]["OF"]["p_mcnemar"]))
put("NFTwBase", _N4["12"]["counts"]["base"]["omit"]); put("NFTwO", _N4["12"]["counts"]["O"]["omit"]); put("NFTwF", _N4["12"]["counts"]["F"]["omit"])

# 修订 33/34: 给新动作补自己的漏手例子(v9f)后的 F9 / R9 与第二种子(new9_stats.py)
_N9 = json.load(open(R + "paper/new9_stats.json")); _c9 = _N9["all"]["counts"]; _t9 = _N9["all"]["tests"]
put("NNN", _N9["all"]["n"]); put("NNHeld", 112)
for _arm, _m in (("base", "Base"), ("O", "O"), ("F", "F"), ("F9", "FN"), ("R9", "RN"), ("F9s2", "FNs"), ("Os2", "Os")):
    put(f"NN{_m}Omit", _c9[_arm]["omit"]); put(f"NN{_m}Extra", _c9[_arm]["extra"])
for _k, _m in (("O_F9", "OF"), ("R9_F9", "RF"), ("O_R9", "OR"), ("Os2_F9s2", "SdTwo"), ("O+Os2_F9+F9s2", "Pool"), ("F_F9", "FF")):
    put(f"NN{_m}A", _t9[_k]["a1_only"]); put(f"NN{_m}B", _t9[_k]["a2_only"]); put(f"NN{_m}p", fp(_t9[_k]["p_perm"]))
_t12 = _N9["12"]["tests"]["O_F9"]; put("NNTwA", _t12["a1_only"]); put("NNTwB", _t12["a2_only"]); put("NNTwp", fp(_t12["p_mcnemar"]))
_t14 = _N9["14"]["tests"]["O_F9"]; put("NNFoA", _t14["a1_only"]); put("NNFoB", _t14["a2_only"]); put("NNFop", fp(_t14["p_mcnemar"]))
for _k, _m in (("s34", "SdNew"), ("s1234", "Four")):
    put(f"NN{_m}A", _t9[_k]["a1_only"]); put(f"NN{_m}B", _t9[_k]["a2_only"]); put(f"NN{_m}p", fp(_t9[_k]["p_perm"]))
_t15 = _N9["15"]["tests"]["Os2_F9s2"]; put("NNFiA", _t15["a1_only"]); put("NNFiB", _t15["a2_only"]); put("NNFip", fp(_t15["p_mcnemar"]))

# 修订 35: Pixtral-12B 第二裁判(j2_stats.py)
_J2 = json.load(open(R + "paper/j2_stats.json")); _h2 = _J2["human"]
put("JTwoAgree", f"{100*_h2['agree_all_pixtral']:.0f}"); put("JTwoQAgree", f"{100*_h2['agree_all_qwen8b']:.1f}")
put("JTwoOmPrec", f"{_h2['omit']['pixtral']['precision']:.2f}"); put("JTwoQOmPrec", f"{_h2['omit']['qwen8b']['precision']:.2f}")
put("JTwoOkRec", f"{_h2['ok']['pixtral']['recall']:.2f}")
put("JTwoBaseOmit", _J2["counts"]["s1base"]["omit"]); put("JTwoBaseN", sum(_J2["counts"]["s1base"].values()))
_b = _J2["P19b"]; put("JTwoOmitO", _b["omit_a1"]); put("JTwoOmitF", _b["omit_a2"]); put("JTwoOF", _b["a1_only"]); put("JTwoFO", _b["a2_only"]); put("JTwoOFp", fp(_b["p_perm"]))
_c = _J2["P19c"]; put("JTwoTrO", _c["O_only"]); put("JTwoTrF", _c["F_only"]); put("JTwoTrp", fp(_c["p_mcnemar"]))

# 修订 37/38: 带门槛的独立裁判; InternVL3.5-8B 当保守漏手计数器(j3_gate.py, j3_stats.py)
_G3 = json.load(open(R + "paper/j3_gate.json")); _J3 = json.load(open(R + "paper/j3_stats.json"))
put("JThrIvAgree", f"{100*_G3['internvl35_8b']['agree']:.0f}"); put("JThrIvPrec", f"{_G3['internvl35_8b']['omit_precision']:.2f}")
put("JThrIvRec", f"{_G3['internvl35_8b']['omit_recall']:.2f}"); put("JThrIvSaid", _G3["internvl35_8b"]["omit_said"])
put("JThrMsAgree", f"{100*_G3['mistral_small31_24b']['agree']:.0f}")
put("JThrO", _J3["pooled_omit"]["O"]); put("JThrF", _J3["pooled_omit"]["F"]); put("JThrR", _J3["pooled_omit"]["R"])
for _k, _m in (("O_F", "OF"), ("R_F", "RF"), ("O_R", "OR")):
    put(f"JThr{_m}A", _J3["tests"][_k]["a1_only"]); put(f"JThr{_m}B", _J3["tests"][_k]["a2_only"]); put(f"JThr{_m}p", fp(_J3["tests"][_k]["p_perm"]))

# 新动作的配对转移(trans_new9.py): 底座多手 → 漏手
_TN = json.load(open(R + "paper/trans_new9.json"))
for _a, _m in (("12", "Tw"), ("all", "All")):
    for _arm, _x in (("O", "O"), ("F9", "FN"), ("R9", "RN")):
        _v = _TN[_a][_arm]; put(f"TN{_m}{_x}Pct", f"{_v['pct_to_omit']:.0f}"); put(f"TN{_m}{_x}Bc", _v["base_comm"]); put(f"TN{_m}{_x}Co", _v["comm_to_omit"])

# 修订 39: InternVL 在 SANA 上当保守漏手计数器(j4_stats.py)
_J4 = json.load(open(R + "paper/j4_stats.json")); _g4 = _J4["gate"]; _o4 = _J4["omit"]
put("SvPrec", f"{_g4['omit_precision']:.2f}"); put("SvSaid", _g4["omit_said"]); put("SvRight", round(_g4["omit_precision"] * _g4["omit_said"]))
put("SvO", _o4["O"] + _o4["O_s2"] + _o4["O_s3"]); put("SvF", _o4["F2"] + _o4["F2_s2"] + _o4["F2_s3"]); put("SvR", _o4["R2"] + _o4["R2_s2"] + _o4["R2_s3"]); put("SvBase", _o4["base"])
for _k, _m in (("O_F2", "OF"), ("R2_F2", "RF"), ("O_R2", "OR")):
    put(f"Sv{_m}A", _J4["tests"][_k]["a1_only"]); put(f"Sv{_m}B", _J4["tests"][_k]["a2_only"]); put(f"Sv{_m}p", fp(_J4["tests"][_k]["p_perm"]))

# 修订 40: FLUX.1-schnell 加大训练量(NF4), O 第 1000 步(flux40_stats.py)
_F40 = json.load(open(R + "paper/flux40_stats.json"))["all|all"]; _f40r = _F40["rate"]; _f40t = _F40["tests"]["base_O1000"]
put("FXNExtraB", _f40r["base"]["extra"]); put("FXNExtraO", _f40r["O1000"]["extra"]); put("FXNOmitB", _f40r["base"]["omit"]); put("FXNOmitO", _f40r["O1000"]["omit"]); put("FXNN", _f40r["base"]["n"])
put("FXNBonly", _f40t["omit_base_only"]); put("FXNOonly", _f40t["omit_arm_only"]); put("FXNp", fp(_f40t["p_perm_by_person"]))
put("FXNOmitF", _f40r["F40"]["omit"]); put("FXNExtraF", _f40r["F40"]["extra"])
# 修订 40 P24a-c: 三组都到第 3000 步
for _a, _m in (("O3000", "O"), ("F40", "F"), ("R40", "R")): put(f"FXT{_m}Omit", _f40r[_a]["omit"]); put(f"FXT{_m}Extra", _f40r[_a]["extra"])
_t3 = _F40["tests"]
for _k, _m in (("O3000_F40", "OF"), ("O3000_R40", "OR"), ("R40_F40", "RF")): put(f"FXT{_m}A", _t3[_k]["omit_a1_only"]); put(f"FXT{_m}B", _t3[_k]["omit_a2_only"]); put(f"FXT{_m}p", fp(_t3[_k]["p_perm_by_person"]))
put("FXTBOp", fp(_t3["base_O3000"]["p_perm_by_person"]))
# 修订 43 起因(事后诊断, 探索性): v7f 对底座漏手 vs F40 自己漏手的打分(tex/flux_detdiag.py + 逐组拆分)
import collections as _co
_DS = json.load(open(R + "flux40/detscore40.json"))
def _lab(arm):
    o = {}
    for s in ("", "_big"):
        for k, v in json.load(open(f"{R}flux40/vl8b_{arm}{s}.json")).items():
            T = v.get("TOTAL"); o[f"{arm}{s}/{k.split('/', 1)[-1]}"] = "ok" if v.get("ok") else ("extra" if (T or 0) >= 3 else ("omit" if T == 2 else "other"))
    return o
def _mean(arm, c):
    L = _lab(arm); v = [_DS[k]["v7f"] for k in L if L[k] == c]; return sum(v) / len(v)
put("FXDetBaseOmit", f"{_mean('base', 'omit'):.2f}"); put("FXDetFOmit", f"{_mean('F40', 'omit'):.3f}"); put("FXDetFOk", f"{_mean('F40', 'ok'):.3f}")

# 配对转移推广(transitions_all.py): 总错误率掩盖交换
_TA = json.load(open(R + "paper/transitions_all.json"))
for _nm, _arm, _m in (("Klein book (3 seeds)", "O", "BkO"), ("Klein book (3 seeds)", "F", "BkF"), ("Klein book (3 seeds)", "R", "BkR"),
                      ("Klein glasses+bottle (trained)", "O", "GlO"), ("Klein glasses+bottle (trained)", "F", "GlF"),
                      ("Klein book, DiffDoctor reward (final image)", "DD_fin", "DDf"), ("SANA flower (3 seeds, judge unreliable)", "O", "SaO")):
    _r = _TA[_nm][_arm]
    put(f"TA{_m}Cb", _r["base_comm_total"]); put(f"TA{_m}Ca", _r["arm_comm_total"]); put(f"TA{_m}Ob", _r["base_omit"]); put(f"TA{_m}Oa", _r["arm_omit"])
    put(f"TA{_m}Eb", f"{_r['err_base_pct']:.1f}"); put(f"TA{_m}Ea", f"{_r['err_arm_pct']:.1f}"); put(f"TA{_m}CM", f"{100 * _r['comm_to_omit'] / max(_r['base_comm'], 1):.0f}"); put(f"TA{_m}N", _r["n"])

# 参考照身份数(gen_conds 用的同一份 limbs_meta.json; 10-06 清 TODO)
_LM = json.load(open("INTERNAL/limbs_meta.json")); _cb = {}
for _v in _LM.values(): _cb.setdefault(f"{_v['id']}_a{_v['action']}", _v)
_ids = {_v["id"] for _v in _cb.values()}
put("NPairs", f"{len(_cb):,}".replace(",", "{,}")); put("NIds", len(_ids)); put("NHoldIdsAll", sum(int(i) % 8 == 0 for i in _ids))

# 堆叠柱图(总错误率掩盖交换): 多手 / 漏手 占比(%)
for _nm, _arm, _m in (("Klein book (3 seeds)", "O", "BkO"), ("Klein book (3 seeds)", "F", "BkF"), ("Klein glasses+bottle (trained)", "O", "GlO"), ("Klein glasses+bottle (trained)", "F", "GlF")):
    _r = _TA[_nm][_arm]; _n = _r["n"]; _p = _m[:2]
    put(f"Pct{_p}BC", f"{100 * _r['base_comm_total'] / _n:.1f}"); put(f"Pct{_p}BO", f"{100 * _r['base_omit'] / _n:.1f}")
    put(f"Pct{_p}{_arm}C", f"{100 * _r['arm_comm_total'] / _n:.1f}"); put(f"Pct{_p}{_arm}O", f"{100 * _r['arm_omit'] / _n:.1f}")

# 审稿修订(10-06): 每种子冻结图张数与转移百分比; 只用冻结模型图 / 排除 O 组的体检
put("TOCNimg", round(int(M["TOCN"]) / 3)); put("TOCMpct", round(100 * int(M["TOCM"]) / int(M["TOCN"]))); put("TFCMpct", round(100 * int(M["TFCM"]) / int(M["TOCN"])))
_AB = json.load(open(R + "paper/audit_scores/audit_auc_human_base.json")); _AN = json.load(open(R + "paper/audit_scores/audit_auc_human_noO.json"))
put("AudBaseVTwoOm", f"{_AB['locdet_v2|klein']['auc_omit']:.2f}"); put("AudBaseVTwoOmci", "[{:.2f}, {:.2f}]".format(*_AB["locdet_v2|klein"]["ci_omit"]))
put("AudNoOVTwoOm", f"{_AN['locdet_v2|klein']['auc_omit']:.2f}"); put("AudBaseDDOm", f"{_AB['diffdoctor_max|klein']['auc_omit']:.2f}")
put("AudBaseVQAOm", f"{_AB['neg_vqascore|klein']['auc_omit']:.2f}"); put("AudBaseVQAOmci", "[{:.2f}, {:.2f}]".format(*_AB["neg_vqascore|klein"]["ci_omit"]))
put("AudBaseN", "{}/{}/{}".format(_AB["locdet_v2|klein"]["n"]["clean"], _AB["locdet_v2|klein"]["n"]["comm"], _AB["locdet_v2|klein"]["n"]["omit"]))

# 修订 44~46: 151 同机复现(fi_stats.py), 抱书 537 张
_FS = json.load(open(R + "paper/fi_stats.json")); _fc = _FS["a8"]["counts"]; _fp = _FS["predictions"]; _ft = _FS["a8"]["tests"]
for _a, _m in (("O151", "Ooc"), ("F151", "Foc"), ("Fi", "Fi"), ("Ri", "Ri")): put(f"Rep{_m}Omit", _fc[_a].get("omit", 0))
put("RepN", _FS["a8"]["n"])
put("RepFiOA", _fp["P29a"]["a1_only"]); put("RepFiOB", _fp["P29a"]["a2_only"]); put("RepFiOp", fp(_fp["P29a"]["p_mcnemar"]))
put("RepFOA", _fp["P29c"]["a1_only"]); put("RepFOB", _fp["P29c"]["a2_only"]); put("RepFOp", fp(_fp["P29c"]["p_mcnemar"]))
_p30 = _fp["P30"]; put("RepRiA", _p30["O_only"]); put("RepRiB", _p30["Ri_only"]); put("RepRip", fp(_p30["p_perm"]))
put("RepRiSeedp", "/".join(f"{v['p_mcnemar']:.2g}" for v in _p30["per_seed"].values()))
put("RepParityN", json.load(open(R + "paper/base_parity_151_108.json"))["n"])

with open("numbers.tex", "w") as fo:
    fo.write("% 由 paper_numbers.py 生成, 不要手改\n")
    for k, v in sorted(M.items()): fo.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(len(M), "个宏")
