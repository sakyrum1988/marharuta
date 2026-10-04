import pandas as pd
from pathlib import Path
base=Path(r'C:\Users\user\Downloads')
for suffix,label in [(' (1)','7d'),(' (2)','28d'),(' (3)','3m'),(' (4)','6m')]:
 p=next(base.glob(f'https___kibernetiki.com.ua_-Performance-on-Search-2026-07-11{suffix}.xlsx'))
 print('\n',label,p)
 for sh,keys in {
  'Запити':['кібернетики','кибернетики','kibernetiki','скачать видео с ютуба'],
  'Сторінки':['https://kibernetiki.com.ua/','https://kibernetiki.com.ua/ru','https://kibernetiki.com.ua/ru/articles/yak-skachaty-video-z-youtube','https://kibernetiki.com.ua/articles/scho-robyty-yakscho-zlamaly-telegram-povnyy-gayd-z-vidnovlennya-dostupu','https://kibernetiki.com.ua/poverbanky','https://kibernetiki.com.ua/smartfony'],
 }.items():
  d=pd.read_excel(p,sheet_name=sh); col=d.columns[0]
  for k in keys:
   idx=d.index[d[col].astype(str).eq(k)].tolist()
   if idx: print(sh,idx[0]+2,k)
