# Dateline

For any date, Dateline shows the most important event that happened on that day in history, with every other year that shares the date laid out beneath it.

**Live:** https://andersbjorkh.github.io/dateline/

## How it works

- `data/MM.json` holds one month of events from Wikipedia's [On this day](https://api.wikimedia.org/wiki/Feed_API/Reference/On_this_day) feed, deduplicated. Each event carries a "languages" count: the number of Wikipedia editions with an article on its main subject (from Wikidata sitelinks).
- The headline for each date is an editorial pick stored in `picks.json`. Popularity signals alone kept choosing articles like "World War II" or a country page, so `shortlist.py` narrows each date to about 15 candidates and the headline is picked by hand from those.
- `index.html` is a static page with no build step. It loads only the month it needs and keeps the date in the URL (`#07-20`).

## Rebuilding the data

```sh
pip install requests pillow
python3 build_data.py   # fetches the feed and Wikidata counts into .cache/, writes data/
python3 shortlist.py    # optional: regenerates candidate lists in .cache/shortlist.txt
```

To change a headline, edit `picks.json` and run `build_data.py` again.

Event text comes from Wikipedia under CC BY-SA 4.0. Images come from Wikimedia Commons.
