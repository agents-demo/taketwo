"""gui1 entry point.

    streamlit run taketwo/surfaces/gui1/ui.py
"""

from __future__ import annotations

import streamlit as st

from taketwo.bootstrap import setup
from taketwo.surfaces.gui1 import config
from taketwo.surfaces.gui1.app_pages import pages

setup()

st.set_page_config(page_title="TakeTwo — video in, proof out", page_icon=str(config.LOGO), layout="wide")

try:
    st.logo(str(config.LOGO), size="large")
except Exception:
    pass

pages.navigation()
