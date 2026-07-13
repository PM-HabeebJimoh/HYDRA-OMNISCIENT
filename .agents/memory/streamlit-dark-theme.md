---
name: Streamlit dark theme
description: How to force a true dark terminal theme in Streamlit without white bleed-through
---

# Streamlit Dark Theme — HYDRA-S3

**Rule:** Two layers required — config.toml theme block AND a full CSS override injected via st.markdown.

**config.toml must have:**
```toml
[theme]
base = "dark"
backgroundColor = "#05070a"
secondaryBackgroundColor = "#0d1117"
textColor = "#e6edf3"
primaryColor = "#00ffcc"
font = "monospace"
```

**CSS override targets:** html/body/.main/[data-testid="stAppViewContainer"]/[data-testid="stMain"]/[data-testid="block-container"] all need `background-color: #05070a !important`. Sidebar needs its own rule targeting `[data-testid="stSidebar"]`.

**KPI font sizes:** Use `clamp(14px, 1.5vw, 22px)` with `white-space:nowrap; overflow:hidden; text-overflow:ellipsis` for 6-column layouts — prevents wrapping and overflow.

**Deprecation:** Streamlit 1.59.2 — replace `use_container_width=True` with `width="stretch"` on plotly_chart and dataframe. Keep `use_container_width=True` on form_submit_button (different API).

**Why:** Without `base="dark"` in config.toml, Streamlit's React skeleton renders white during hydration, causing flash. Without the CSS override, intermediate containers bleed through.
