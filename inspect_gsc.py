import json
from pathlib import Path
import pandas as pd

files = sorted(Path(r"C:\Users\user\Downloads").glob("https___kibernetiki.com.ua_-Performance-on-Search-2026-07-11*.xlsx"))
out = []
for path in files:
    xls = pd.ExcelFile(path)
    wb = {"file": str(path), "size": path.stat().st_size, "sheets": []}
    for sheet in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        rec = {
            "sheet": sheet,
            "shape": list(df.shape),
            "columns": [str(c) for c in df.columns],
            "head": df.head(4).where(pd.notna(df), None).to_dict("records"),
        }
        wb["sheets"].append(rec)
    out.append(wb)
print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
