import pandas as pd
from pathlib import Path
p=next(Path(r'C:\Users\user\Downloads').glob('https___kibernetiki.com.ua_-Performance-on-Search-2026-07-11.xlsx'))
d=pd.read_excel(p,sheet_name='Діаграма')
d.columns=['date','clicks','impressions','ctr','position']; d.date=pd.to_datetime(d.date)
def stat(a,b):
 x=d[(d.date>=a)&(d.date<=b)]; c=x.clicks.sum(); i=x.impressions.sum()
 return {'range':f'{a}..{b}','days':len(x),'clicks':int(c),'avg_clicks':round(c/len(x),1),'impressions':int(i),'ctr_pct':round(c/i*100,3),'position_imp_weighted':round((x.position*x.impressions).sum()/i,2)}
windows={
'core_pre':('2026-05-07','2026-05-20'),'core_rollout':('2026-05-21','2026-06-02'),'core_post':('2026-06-03','2026-06-16'),
'spam_pre':('2026-06-10','2026-06-23'),'spam_rollout':('2026-06-24','2026-06-26'),'spam_post':('2026-06-27','2026-07-09')}
for n,(a,b) in windows.items():print(n,stat(a,b))
print('DAILY 2026-05-15 onward')
print(d[d.date>='2026-05-15'].to_string(index=False))
