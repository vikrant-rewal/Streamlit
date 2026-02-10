# Ammy's Choice Meal Planner

You asked for a simpler approach: **no full app required**.

This repo now includes a standalone HTML page:

- `menu-planner.html` → open in browser and generate menus directly.

## Do we really need an app?

No. For your use case, a single HTML page is enough.

Use a full React/Android app only if you need app-store distribution, offline data sync, push notifications, or deep native integrations.

## Credentials needed

1. **Gemini API key (required)**
   - Used to generate menu text.
2. **Pexels API key (optional)**
   - Used to fetch a more accurate dish image matching the generated menu.

## Run the HTML page

Because browser APIs can block some calls from `file://`, run a tiny local server:

```bash
python3 -m http.server 8080
```

Then open:

```text
http://localhost:8080/menu-planner.html
```

On first load, paste your Gemini/Pexels keys and click **Save Keys Locally** so you won't be asked again in that browser.

## Why menu images were incorrect before

The earlier Streamlit flow used a fixed dish→image map. If the generated dish text didn’t exactly match map keys, image quality/match dropped.

The HTML page improves this by optionally doing live dish image search via Pexels.
