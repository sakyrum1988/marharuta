import json
from pathlib import Path
d=json.loads(Path('gsc_analysis.json').read_text(encoding='utf-8'))
for period,p in d['periods'].items():
    print('\n###',period)
    print('TOTAL',p['exact_total_devices'],'DECOMP',p['decomposition_clicks'])
    print('QUERY GROUPS',p['query_groups'])
    print('LANG',p['language_groups'])
    print('PAGE GROUPS',p['page_groups'][:12])
    for section in ['devices','appearance','query_losers','query_winners','page_losers','page_winners']:
        print('\n',section.upper())
        for r in p[section][:12]:
            print(r)
