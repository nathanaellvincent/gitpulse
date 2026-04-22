# GitPulse

A web tool that turns any public GitHub repository into an at-a-glance analytics dashboard. Paste a repo URL, see commit cadence over time, the top contributors, the language breakdown, and a rough "bus factor" — no setup, no auth required for public repos.

Built with **Python**, **Streamlit**, **pandas**, and **Plotly**, on top of the public GitHub REST API.

**Live:** [gitpulse.streamlit.app](https://gitpulse.streamlit.app) *(deploy pending)*

## What it shows

- **Repo header** — stars, forks, open issues, commits sampled, bus factor — as a single-glance metric row.
- **Weekly commit activity** — commits bucketed into ISO weeks, area-filled over the sampled window. Reindexed against a continuous week range so quiet periods read as literal zeroes rather than gaps in the x-axis.
- **Top contributors** — horizontal bar chart, height scaled to the number of contributors so the layout stays tight on small repos and doesn't squeeze on large ones.
- **Language breakdown** — donut chart over GitHub's per-language byte counts. Donut form keeps single-language repos readable.
- **Bus factor** — the minimum number of top contributors responsible for ≥50% of commits. A surprisingly good smoke test for key-person risk on unfamiliar dependencies.

## Architecture

```
app.py                      Streamlit controller — sidebar + layout only.
gitpulse/
├── github_client.py        Session-based REST wrapper with pagination
│                           and typed errors (RepoNotFound, RateLimit).
├── analysis.py             Pure pandas: commits_to_dataframe,
│                           weekly_activity, top_contributors,
│                           bus_factor. No I/O — trivially testable.
└── charts.py               Plotly builders, themed to the Streamlit
                            palette.
.streamlit/config.toml      Dark-navy theme.
```

The controller / client / analysis / chart split keeps each file short and single-purpose. The analysis functions are pure, the client is the only place that touches the network, and the charts only know about DataFrames — so every layer is independently swappable.

## Rate limits

The GitHub REST API allows:

- **60 requests/hour** for anonymous callers — enough for a handful of interactive sessions.
- **5000 requests/hour** with a personal access token.

GitPulse prompts for an optional token in the sidebar. It's stored only in the active Streamlit session; nothing is logged or persisted server-side. If you do hit the limit, the UI surfaces a clear message including the reset time pulled from GitHub's `X-RateLimit-Reset` header.

Create a fine-grained PAT at [github.com/settings/tokens](https://github.com/settings/tokens) — public-repo read is all GitPulse needs.

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

No environment variables, no database, no accounts. The app opens on `http://localhost:8501`.

## Deploying

The repo is a zero-config deploy on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push this repo to GitHub.
2. Connect it on Streamlit Cloud, pointing at `app.py`.
3. Done — `requirements.txt` and `.streamlit/config.toml` are picked up automatically.

Also deploys cleanly to Hugging Face Spaces (Streamlit runtime) or any container host that speaks Python.

## Author

**Vincent Nathanael** — BSc Computer Science with Artificial Intelligence, Coventry University. Portfolio: [vincentnathanael.vercel.app](https://vincentnathanael.vercel.app)
