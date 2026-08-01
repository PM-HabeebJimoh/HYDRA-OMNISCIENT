"""Store 5-minute Investing.com bars fetched via fetch_page into one file."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'data/raw/m5/xauusd_m5.json'
DB.parent.mkdir(parents=True, exist_ok=True)

def load():
    return json.load(open(DB)) if DB.exists() else {}

def add(raw):
    """raw = the JSON text returned by the tvc4 history endpoint."""
    txt = raw.strip()
    txt = txt.replace('\\/', '/').replace('\\[', '[').replace('\\]', ']')
    txt = re.sub(r'"n/a"', 'null', txt)
    d = json.loads(txt)
    if d.get('s') != 'ok':
        return 0
    db = load()
    n = 0
    for i, t in enumerate(d['t']):
        k = str(t)
        if k not in db:
            n += 1
        db[k] = [d['o'][i], d['h'][i], d['l'][i], d['c'][i]]
    json.dump(db, open(DB, 'w'))
    return n

if __name__ == '__main__':
    total = 0
    for p in sys.argv[1:]:
        total += add(open(p).read())
    print(f"added {total} new bars; db now {len(load())}")
