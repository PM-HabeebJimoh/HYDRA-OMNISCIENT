"""
Parse the long-history Investing.com daily OHLC that fetch_page returns
into data/raw/oos/. The sandbox has no direct internet, so the JSON blobs
are written here by hand from fetch_page output (same method used for the
FRED series and the calendar).
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data/raw/oos'
OUT.mkdir(parents=True, exist_ok=True)

def save(name, raw):
    d = json.loads(raw)
    assert d.get('s') == 'ok', d.get('s')
    n = len(d['t'])
    assert all(len(d[k]) == n for k in 'ohlc'), 'ragged arrays'
    json.dump(dict(symbol=name, t=d['t'], o=d['o'], h=d['h'],
                   l=d['l'], c=d['c']), open(OUT / f'{name}.json', 'w'))
    print(f"{name}: {n} bars")

if __name__ == '__main__':
    save(sys.argv[1], open(sys.argv[2]).read())
