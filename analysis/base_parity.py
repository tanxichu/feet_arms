#!/usr/bin/env python3
"""跨机器对拍(10-09, 修订 44/45 的混淆检查): 151 上冻结 Klein 出的图 vs 108 上 gen_v3/base 同 key 图, 逐像素比。
用法: python3 base_parity.py <151 拉回的 base 目录> [<108 的 gen_v3/base 目录>]   输出每张最大差 / 平均差与逐像素相同的张数。"""
import sys, os, glob, json
import numpy as np
from PIL import Image
A = sys.argv[1]; B = sys.argv[2] if len(sys.argv) > 2 else "DATA/gen_v3/base"
rows = []
for d in sorted(glob.glob(A + "/*/img_00001_.png")):
    k = os.path.basename(os.path.dirname(d)); q = f"{B}/{k}/img_00001_.png"
    if not os.path.exists(q): continue
    x = np.asarray(Image.open(d).convert("RGB"), dtype=np.int16); y = np.asarray(Image.open(q).convert("RGB"), dtype=np.int16)
    if x.shape != y.shape: rows.append((k, None, None)); continue
    dd = np.abs(x - y); rows.append((k, int(dd.max()), float(dd.mean())))
ok = [r for r in rows if r[1] is not None]
out = {"n": len(rows), "identical": sum(r[1] == 0 for r in ok), "max_le_2": sum(r[1] <= 2 for r in ok), "mean_absdiff_median": float(np.median([r[2] for r in ok])) if ok else None, "shape_mismatch": len(rows) - len(ok), "rows": rows}
json.dump(out, open("DATA/paper/base_parity_151_108.json", "w"), indent=1)
print({k: v for k, v in out.items() if k != "rows"})
