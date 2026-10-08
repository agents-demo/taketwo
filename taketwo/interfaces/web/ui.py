"""TakeTwo web app entry point.

    streamlit run taketwo/interfaces/web/ui.py
"""

from __future__ import annotations

import streamlit as st

from taketwo.bootstrap import setup
from taketwo.interfaces.web.app_pages import pages

setup()

st.set_page_config(page_title="TakeTwo", page_icon=":material/movie:", layout="wide")

pages.navigation()
