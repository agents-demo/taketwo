"""TakeTwo web app entry point.

    streamlit run taketwo/interfaces/web/ui.py
"""

from __future__ import annotations

import streamlit as st

from taketwo.bootstrap import setup
from taketwo.interfaces.web import common
from taketwo.interfaces.web.app_pages import pages

setup()

st.set_page_config(page_title="TakeTwo — video in, proof out", page_icon=str(common.LOGO), layout="wide")

try:
    st.logo(str(common.LOGO), size="large")
except Exception:
    pass

pages.navigation()
