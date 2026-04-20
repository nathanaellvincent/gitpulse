"""GitPulse — Streamlit entry point.

Thin controller layer. Keeps all heavy lifting in gitpulse.* modules
so the UI is easy to read and the analysis is easy to unit-test.
"""

from __future__ import annotations

import streamlit as st

from gitpulse.analysis import (
    bus_factor,
    commits_to_dataframe,
    top_contributors,
    weekly_activity,
)
from gitpulse.charts import weekly_activity_chart
from gitpulse.github_client import GitHubClient, RepoRef, parse_repo_url


st.set_page_config(
    page_title="GitPulse — Repo Analytics",
    page_icon=":bar_chart:",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Sidebar: input + optional auth token
# ---------------------------------------------------------------------------

st.sidebar.title("GitPulse")
st.sidebar.caption("Repo analytics from the GitHub REST API.")

raw_input_url = st.sidebar.text_input(
    "Repository",
    value="facebook/react",
    help="Full GitHub URL, git@ SSH form, or owner/name shorthand.",
)

token = st.sidebar.text_input(
    "GitHub token (optional)",
    type="password",
    help=(
        "Without a token the GitHub API allows 60 requests/hour. "
        "Paste a fine-grained personal access token to bump that to 5000/hour. "
        "Tokens stay in your browser session — nothing is logged or persisted."
    ),
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Built by [Vincent Nathanael](https://vincentnathanael.vercel.app)."
)


# ---------------------------------------------------------------------------
# Data loading (cached per repo slug + token presence)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=600, show_spinner=False)
def load_repo_data(slug: str, token: str | None) -> dict:
    """Fetch everything we need for one repo in one go.

    Cached for 10 minutes per (slug, has-token) pair so repeat
    interactions don't re-hammer the API.
    """
    owner, name = slug.split("/", 1)
    ref = RepoRef(owner=owner, name=name)
    client = GitHubClient(token=token or None)

    return {
        "repo": client.get_repo(ref),
        "commits": client.get_commits(ref, limit=500),
        "contributors": client.get_contributors(ref, limit=30),
        "languages": client.get_languages(ref),
    }


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

ref = parse_repo_url(raw_input_url)
if ref is None:
    st.title("GitPulse")
    st.info(
        "Paste a GitHub repository URL in the sidebar to get started. "
        "Try `facebook/react`, `vercel/next.js`, or any public repo."
    )
    st.stop()

with st.spinner(f"Loading {ref.slug}…"):
    data = load_repo_data(ref.slug, token)

repo = data["repo"]
commits_df = commits_to_dataframe(data["commits"])
contributors = data["contributors"]

# --- Header block --------------------------------------------------------

st.title(repo.get("full_name", ref.slug))
if repo.get("description"):
    st.caption(repo["description"])

meta_cols = st.columns(5)
meta_cols[0].metric("Stars", f"{repo.get('stargazers_count', 0):,}")
meta_cols[1].metric("Forks", f"{repo.get('forks_count', 0):,}")
meta_cols[2].metric("Open issues", f"{repo.get('open_issues_count', 0):,}")
meta_cols[3].metric("Commits sampled", f"{len(commits_df):,}")
meta_cols[4].metric("Bus factor", bus_factor(contributors))


# --- Analysis panels -----------------------------------------------------

weekly_df = weekly_activity(commits_df)
contributors_df = top_contributors(contributors)

st.subheader("Weekly commit activity")
st.caption("ISO-week buckets across the sampled commit window.")
st.plotly_chart(weekly_activity_chart(weekly_df), use_container_width=True)

st.subheader("Top contributors")
st.dataframe(contributors_df, use_container_width=True, hide_index=True)

st.subheader("Language breakdown")
st.dataframe(
    {"language": list(data["languages"].keys()),
     "bytes": list(data["languages"].values())},
    use_container_width=True,
    hide_index=True,
)
