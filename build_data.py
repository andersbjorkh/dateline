"""Build per-month JSON for the On This Day app from Wikipedia's feed.

Each event is scored by how many Wikipedia language editions cover its main
article (Wikidata sitelinks). The highest score of the day is the headline.
"""
import base64, io, json, time, calendar
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image

UA = {"User-Agent": "OnThisDayApp/1.0 (personal project; anders.bjorkhaug@gmail.com)"}
OUT = Path(__file__).parent / "data"
CACHE = Path(__file__).parent / ".cache"
OUT.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)
S = requests.Session()
S.headers.update(UA)


def get(url, **kw):
    for attempt in range(6):
        try:
            r = S.get(url, timeout=30, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(r.status_code)
            r.raise_for_status()
            return r
        except Exception:
            time.sleep(2 ** attempt)
    raise RuntimeError(url)


def fetch_day(md):
    m, d = md
    f = CACHE / f"{m:02d}-{d:02d}.json"
    if f.exists():
        return md, json.loads(f.read_text())
    url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/{m:02d}/{d:02d}"
    j = get(url).json()
    slim = {}
    for kind in ("selected", "events"):
        slim[kind] = [
            {
                "text": e["text"],
                "year": e.get("year"),
                "pages": [
                    {
                        "t": p["titles"]["normalized"],
                        "q": p.get("wikibase_item"),
                        "desc": p.get("description", ""),
                        "thumb": (p.get("thumbnail") or {}).get("source"),
                        "url": p["content_urls"]["desktop"]["page"],
                    }
                    for p in e.get("pages", [])
                ],
            }
            for e in j.get(kind, [])
        ]
    f.write_text(json.dumps(slim))
    return md, slim


def sitelinks(qids):
    f = CACHE / "sitelinks.json"
    known = json.loads(f.read_text()) if f.exists() else {}
    todo = [q for q in qids if q not in known]
    chunks = [todo[i:i + 50] for i in range(0, len(todo), 50)]

    def one(chunk):
        r = get("https://www.wikidata.org/w/api.php", params={
            "action": "wbgetentities", "ids": "|".join(chunk),
            "props": "sitelinks", "format": "json"})
        ents = r.json().get("entities", {})
        return {q: sum(1 for k in (e.get("sitelinks") or {}) if k.endswith("wiki") and k != "commonswiki")
                for q, e in ents.items()}

    with ThreadPoolExecutor(4) as ex:
        for i, res in enumerate(ex.map(one, chunks)):
            known.update(res)
            if i % 50 == 0:
                print(f"  sitelinks {i}/{len(chunks)}", flush=True)
    f.write_text(json.dumps(known))
    return known


def thumb_data_uri(url):
    try:
        img = Image.open(io.BytesIO(get(url).content))
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        img = img.convert("RGB")
        img.thumbnail((300, 300))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=72, optimize=True, progressive=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print("  thumb failed", url, e)
        return None


def main():
    days = [(m, d) for m in range(1, 13) for d in range(1, calendar.monthrange(2024, m)[1] + 1)]
    with ThreadPoolExecutor(6) as ex:
        raw = dict(ex.map(fetch_day, days))
    print("fetched", len(raw), "days")

    qids = sorted({p["q"] for day in raw.values() for k in day.values() for e in k for p in e["pages"] if p["q"]})
    print("qids", len(qids))
    links = sitelinks(qids)

    here = Path(__file__).parent
    picks = json.loads((here / "picks.json").read_text())

    months = {m: {} for m in range(1, 13)}
    for (m, d), day in raw.items():
        selected_texts = {e["text"] for e in day["selected"]}
        seen, events = set(), []
        for e in day["selected"] + day["events"]:
            if e["text"] in seen or e["year"] is None:
                continue
            seen.add(e["text"])
            pages = e["pages"]
            main = pages[0] if pages else None
            score = links.get(main["q"], 0) if main else 0
            events.append({
                "y": e["year"], "text": e["text"], "score": score,
                "sel": e["text"] in selected_texts,
                "main": main and {"t": main["t"], "desc": main["desc"], "url": main["url"], "thumb": main["thumb"]},
                "links": [{"t": p["t"], "url": p["url"]} for p in pages[1:6]],
            })
        # The headline is an editorial pick (picks.json, chosen from the
        # shortlist.py candidates); fall back to the sitelink score.
        key = f"{m:02d}-{d:02d}"
        top = None
        if key in picks:
            top = next((ev for ev in events if ev["text"] == picks[key]["text"]), None)
        if top is None:
            top = max(events, key=lambda ev: ev["score"] * (1.25 if ev["sel"] else 1))
        img = None
        for p in ([top["main"]] if top["main"] else []):
            if p.get("thumb"):
                img = thumb_data_uri(p["thumb"])
        for ev in events:
            if ev["main"]:
                ev["main"].pop("thumb", None)
        events.sort(key=lambda ev: ev["y"])
        months[m][f"{d:02d}"] = {"top": events.index(top), "img": img, "events": events}

    for m, data in months.items():
        (OUT / f"{m:02d}.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        print("wrote month", m, (OUT / f"{m:02d}.json").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
