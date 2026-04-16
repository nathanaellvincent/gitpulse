"""GitPulse — Streamlit entry point."""

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="GitPulse", page_icon=":bar_chart:")
    st.title("GitPulse")
    st.caption("GitHub repository analytics.")


if __name__ == "__main__":
    main()
