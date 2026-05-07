import json
data = json.load(open('tender_extracted.json'))
p0 = data['pages'][0]
ocr = p0.get('ocr', [])
print('ocr type:', type(ocr), 'len:', len(ocr))
if ocr:
    item = ocr[0]
    print('ocr[0] keys:', list(item.keys()))
    res = item.get('res', {})
    print('res keys:', list(res.keys())[:15])
    if 'rec_texts' in res:
        print('rec_texts sample:', res['rec_texts'][:5])
print('Type:', type(data))
if isinstance(data, dict):
    print('Keys:', list(data.keys())[:15])
    for k,v in list(data.items())[:5]:
        print(f'  {k}: {type(v).__name__}', str(v)[:150] if not isinstance(v,(list,dict)) else f'len={len(v)}')
    if 'pages' in data and data['pages']:
        p0 = data['pages'][0]
        print('First page keys:', list(p0.keys()))
        print('First page sample:', str(p0)[:300])
elif isinstance(data, list):
    print('List len:', len(data))
    print('First item keys:', list(data[0].keys())[:10])
    print('First item:', str(data[0])[:300])
