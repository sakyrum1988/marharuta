import json, re
from pathlib import Path
from urllib.parse import urlparse
import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\user\Downloads")
FILES = sorted(ROOT.glob("https___kibernetiki.com.ua_-Performance-on-Search-2026-07-11*.xlsx"))

def load_file(path):
    sheets = pd.read_excel(path, sheet_name=None)
    filt = sheets.get("Фільтри", pd.DataFrame())
    period = "unknown"
    if not filt.empty:
        d = dict(zip(filt.iloc[:,0].astype(str), filt.iloc[:,1].astype(str)))
        period = d.get("Дата", "unknown")
    return period, sheets

books = {}
for f in FILES:
    period, sheets = load_file(f)
    books[period] = {"path": str(f), "sheets": sheets}

def comp_cols(df):
    cols = list(df.columns)
    key = cols[0]
    cclick = next(c for c in cols if "Звертання" in str(c) and "Попередні" not in str(c))
    pclick = next(c for c in cols if "Звертання" in str(c) and "Попередні" in str(c))
    cimp = next(c for c in cols if "Покази" in str(c) and "Попередні" not in str(c))
    pimp = next(c for c in cols if "Покази" in str(c) and "Попередні" in str(c))
    cctr = next(c for c in cols if "CTR" in str(c) and "Попередні" not in str(c))
    pctr = next(c for c in cols if "CTR" in str(c) and "Попередні" in str(c))
    cpos = next(c for c in cols if "Позиція" in str(c) and "Попередні" not in str(c))
    ppos = next(c for c in cols if "Позиція" in str(c) and "Попередні" in str(c))
    return key, cclick, pclick, cimp, pimp, cctr, pctr, cpos, ppos

def tidy(df):
    key,*m = comp_cols(df)
    x=df[[key]+m].copy()
    x.columns=["key","clicks_cur","clicks_prev","imp_cur","imp_prev","ctr_cur","ctr_prev","pos_cur","pos_prev"]
    for c in x.columns[1:]: x[c]=pd.to_numeric(x[c],errors="coerce").fillna(0)
    x["dclicks"]=x.clicks_cur-x.clicks_prev
    x["dimps"]=x.imp_cur-x.imp_prev
    x["dctr_pp"]=(x.ctr_cur-x.ctr_prev)*100
    x["dpos"]=x.pos_cur-x.pos_prev
    x["demand_effect"]=(x.imp_cur-x.imp_prev)*x.ctr_prev
    x["ctr_effect"]=x.imp_cur*(x.ctr_cur-x.ctr_prev)
    return x

def pct(a,b): return None if b==0 else (a/b-1)*100
def rnd(v,n=2): return None if v is None or pd.isna(v) else round(v,n)

def aggregate_rows(x, label_col=None):
    a=x[["clicks_cur","clicks_prev","imp_cur","imp_prev"]].sum()
    ctrc=a.clicks_cur/a.imp_cur if a.imp_cur else 0
    ctrp=a.clicks_prev/a.imp_prev if a.imp_prev else 0
    return {"clicks_cur":round(a.clicks_cur,1),"clicks_prev":round(a.clicks_prev,1),"clicks_pct":rnd(pct(a.clicks_cur,a.clicks_prev),2),
            "imp_cur":round(a.imp_cur,1),"imp_prev":round(a.imp_prev,1),"imp_pct":rnd(pct(a.imp_cur,a.imp_prev),2),
            "ctr_cur":round(ctrc*100,3),"ctr_prev":round(ctrp*100,3),"ctr_rel_pct":rnd(pct(ctrc,ctrp),2)}

def recs(df,n=15,sort="dclicks",asc=True):
    cols=["key","clicks_cur","clicks_prev","dclicks","imp_cur","imp_prev","dimps","ctr_cur","ctr_prev","dctr_pp","pos_cur","pos_prev","dpos","demand_effect","ctr_effect"]
    q=df.sort_values(sort,ascending=asc).head(n)[cols].copy()
    for c in cols[1:]: q[c]=q[c].round(3)
    return q.to_dict("records")

summary={"files":{k:v["path"] for k,v in books.items()},"periods":{}}
for period,book in books.items():
    if period=="Останні 16 місяців": continue
    s=book["sheets"]
    dev=tidy(s["Пристрої"])
    countries=tidy(s["Країни"])
    queries=tidy(s["Запити"])
    pages=tidy(s["Сторінки"])
    appearance=tidy(s["Вигляд у результатах пошуку"])
    total=aggregate_rows(dev)
    # Exact decomposition at device total level
    demand=((dev.imp_cur-dev.imp_prev)*dev.ctr_prev).sum()
    ctr=(dev.imp_cur*(dev.ctr_cur-dev.ctr_prev)).sum()
    # query labels
    brand_re=re.compile(r"кібернет|кибернет|kibernet|kiber net|кибер нет",re.I)
    queries["brand"]=queries.key.astype(str).str.contains(brand_re,na=False)
    qgroups=[]
    for name,grp in queries.groupby("brand"):
        z=aggregate_rows(grp); z["group"]="brand" if name else "nonbrand"; qgroups.append(z)
    # page type / language
    def ptype(u):
        p=urlparse(str(u)).path.strip("/")
        if p in ("","ru"): return "homepage"
        seg=p.split("/")
        if seg[0]=="ru" and len(seg)>1: seg=seg[1:]
        if not seg: return "homepage"
        if seg[0] in ("articles","article","blog"): return "article"
        if seg[0] in ("product","products","p","item"): return "product"
        if seg[0] in ("catalog","category","categories","c"): return "category"
        return seg[0]
    pages["type"]=pages.key.map(ptype)
    pages["lang"]=pages.key.map(lambda u:"ru" if urlparse(str(u)).path.startswith("/ru") else "uk")
    pgroups=[]
    for name,grp in pages.groupby("type"):
        z=aggregate_rows(grp);z["group"]=name;z["rows"]=len(grp);pgroups.append(z)
    langgroups=[]
    for name,grp in pages.groupby("lang"):
        z=aggregate_rows(grp);z["group"]=name;langgroups.append(z)
    summary["periods"][period]={
        "exact_total_devices":total,
        "decomposition_clicks":{"demand":round(demand,1),"ctr":round(ctr,1),"sum":round(demand+ctr,1)},
        "devices":recs(dev,5),"countries_losers":recs(countries,10),"countries_winners":recs(countries,5,asc=False),
        "appearance":recs(appearance,10),"query_groups":qgroups,
        "query_losers":recs(queries,25),"query_winners":recs(queries,15,asc=False),
        "page_groups":sorted(pgroups,key=lambda r:r["clicks_cur"],reverse=True),"language_groups":langgroups,
        "page_losers":recs(pages,30),"page_winners":recs(pages,15,asc=False),
    }

# Daily 16-month trend
daily=books["Останні 16 місяців"]["sheets"]["Діаграма"].copy()
daily.columns=["date","clicks","impressions","ctr","position"]
daily["date"]=pd.to_datetime(daily.date)
daily=daily.sort_values("date")
daily["dow"]=daily.date.dt.day_name()
last=daily.date.max()
def window_stats(end,days):
    d=daily[(daily.date>end-pd.Timedelta(days=days))&(daily.date<=end)]
    return {"start":str(d.date.min().date()),"end":str(d.date.max().date()),"days":len(d),"clicks":int(d.clicks.sum()),"impressions":int(d.impressions.sum()),
            "ctr":round(d.clicks.sum()/d.impressions.sum()*100,3),"avg_position":round(np.average(d.position,weights=d.impressions),2),"avg_daily_clicks":round(d.clicks.mean(),1)}
trend={"range":[str(daily.date.min().date()),str(last.date())],"windows":{}}
for days in [7,28,90,180]:
    cur=window_stats(last,days); prev=window_stats(last-pd.Timedelta(days=days),days)
    trend["windows"][str(days)]={"cur":cur,"prev":prev,"clicks_pct":round(pct(cur["clicks"],prev["clicks"]),2),"impressions_pct":round(pct(cur["impressions"],prev["impressions"]),2),"ctr_rel_pct":round(pct(cur["ctr"],prev["ctr"]),2)}
# YoY comparable 28 days
yoy_cur=window_stats(last,28); yoy_prev=window_stats(last-pd.DateOffset(years=1),28)
trend["yoy_28"]={"cur":yoy_cur,"prev":yoy_prev,"clicks_pct":round(pct(yoy_cur["clicks"],yoy_prev["clicks"]),2),"impressions_pct":round(pct(yoy_cur["impressions"],yoy_prev["impressions"]),2),"ctr_rel_pct":round(pct(yoy_cur["ctr"],yoy_prev["ctr"]),2)}
# weekly series recent 20 weeks and strongest week-over-week drops
d=daily.set_index("date")
w=pd.DataFrame({"clicks":d.clicks.resample("W-SUN").sum(),"impressions":d.impressions.resample("W-SUN").sum()})
w["ctr"]=w.clicks/w.impressions
w["clicks_wow_pct"]=w.clicks.pct_change()*100
trend["recent_weeks"]=w.tail(20).reset_index().round({"ctr":5,"clicks_wow_pct":2}).assign(date=lambda x:x.date.dt.strftime("%Y-%m-%d")).to_dict("records")
trend["largest_weekly_drops"]=w.dropna().nsmallest(10,"clicks_wow_pct").reset_index().round({"ctr":5,"clicks_wow_pct":2}).assign(date=lambda x:x.date.dt.strftime("%Y-%m-%d")).to_dict("records")
summary["daily_trend"]=trend

def json_default(o):
    if isinstance(o, np.generic): return o.item()
    if isinstance(o, pd.Timestamp): return o.isoformat()
    raise TypeError(type(o).__name__)
Path("gsc_analysis.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=json_default),encoding="utf-8")
print(json.dumps({"periods":list(summary["periods"]),"daily_trend":trend},ensure_ascii=False,indent=2))
