# Dateline

For any date, Dateline shows the most important event that happened on that day in history, with every other year that shares the date laid out beneath it.

**Live:** https://andersbjorkh.github.io/dateline/

## Using the page

- Move between days with the ← / → buttons or arrow keys, pick a date from the calendar, or jump back with **Today**.
- The date lives in the URL (`#07-20`), so any day can be linked or bookmarked.
- The timeline ruler places every event of the date by year; click a mark to jump to its entry.
- **Curated only** hides everything except Wikipedia's featured "selected" events. **Oldest first** / **Newest first** sets the list order. Both choices are remembered in `localStorage`.
- **Make headline** promotes any event to the top for the current visit; **Restore pick** puts the editorial pick back.
- **EN / NO** switches the interface between English and Norwegian (bokmål). The first visit follows the browser language, and the choice is remembered in `localStorage`. Event text stays in English, since Wikipedia's feed has no Norwegian edition, but in Norwegian mode article links go to no.wikipedia.org when a Norwegian article exists.
- Light and dark themes follow the system setting, and animations respect reduced-motion preferences.

## How it works

- `data/MM.json` holds one month of events from Wikipedia's [On this day](https://api.wikimedia.org/wiki/Feed_API/Reference/On_this_day) feed, deduplicated. Each event carries a score: the number of Wikipedia editions with an article on its main subject (from Wikidata sitelinks).
- The headline for each date is an editorial pick stored in `picks.json`. Popularity signals alone kept choosing articles like "World War II" or a country page, so `shortlist.py` narrows each date to about 15 candidates and the headline is picked by hand from those. A date without a pick falls back to the highest score, with a small boost for curated events.
- Only the headline's image is kept, resized to 300 px and inlined as a JPEG data URI, so the page makes no requests to Wikimedia at runtime in English. In Norwegian, the page asks the English Wikipedia API (`prop=langlinks`) for the day's Norwegian article titles, a few batched requests per date. If the lookup fails, the English links stay.
- `index.html` is a static page with no build step and no dependencies. It loads only the month it needs.

### Data format

Each `data/MM.json` maps a two-digit day to an object like this one for `07.json` → `"20"`:

```jsonc
{
  "top": 55,                 // index of the headline in `events`
  "img": "data:image/jpeg;base64,…",  // headline image, or null
  "events": [                // sorted by year, oldest first
    {
      "y": 1969,
      "text": "The Apollo 11 Lunar Module Eagle landed on the Sea of Tranquility…",
      "score": 105,          // Wikidata sitelink count of the main article
      "sel": true,           // in Wikipedia's curated "selected" list
      "main": { "t": "Apollo 11", "desc": "First crewed Moon landing (1969)", "url": "https://en.wikipedia.org/wiki/Apollo_11" },
      "links": [{ "t": "…", "url": "…" }]   // up to five related articles
    }
  ]
}
```

`picks.json` maps `MM-DD` to `{ "year", "text" }`; `text` must match an event's text exactly.

## Running locally

The page fetches its data, so serve it over HTTP rather than opening the file directly:

```sh
python3 -m http.server 8000
# open http://localhost:8000/
```

## Rebuilding the data

```sh
pip install requests pillow
python3 build_data.py   # fetches the feed and Wikidata counts into .cache/, writes data/
python3 shortlist.py    # optional: writes candidate lists to .cache/shortlist.txt (needs .cache/ from build_data.py)
```

API responses are cached in `.cache/` (git-ignored), so later runs are fast. Delete it to fetch fresh data.

To change a headline, edit `picks.json` and run `build_data.py` again.

## Deployment

The site is a set of static files served by GitHub Pages from the repository root. `.nojekyll` turns off Jekyll processing so the files are published as-is.

## Credits

Event text comes from Wikipedia under CC BY-SA 4.0. Images come from Wikimedia Commons.
