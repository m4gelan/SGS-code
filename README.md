# SGS code: AMOC figures

Python scripts that produce the figures for my Small Group Seminar on the Atlantic Meridional Overturning Circulation (AMOC).

## Scripts

| Script | What it does | Output |
|---|---|---|
| `amoc_proxies.py` | Plots four palaeo-proxies of AMOC strength on a shared timeline (400-2020 CE): SST reconstruction, gorgonian coral δ15N, sortable-silt grain size and Greenland ice-core methanesulfonic acid. | `figures/amoc_proxies.png` |
| `amoc_google_trends.py` | Plots UK Google Trends interest in "Atlantic meridional overturning circulation" (2025-2026), joining monthly and weekly downloads on one 0-100 scale and marking two media articles. | `figures/amoc_google_trends.png` |

Run from the repository root:

```bash
pip install pandas matplotlib openpyxl
python amoc_proxies.py
python amoc_google_trends.py
```

## Data

- `data/caesar2021/` - proxy compilation from Caesar et al. (2021), *Current Atlantic Meridional Overturning Circulation weakest in last millennium*, Nature Geoscience. Copied from [ncahill89/AMOC-Analysis](https://github.com/ncahill89/AMOC-Analysis).
- `data/google_trends/` - Google Trends exports (United Kingdom), accessed 13/10/2026.

## Articles marked on the Google Trends figure

- The Guardian (April line): https://www.theguardian.com/environment/2026/apr/15/critical-atlantic-current-significantly-more-likely-to-collapse-than-thought

- The Guardian (June line): https://www.theguardian.com/commentisfree/2026/jun/14/amoc-collapse-europe-climate


- BBC : https://www.bbc.co.uk/news/articles/c992e8g10nmo
