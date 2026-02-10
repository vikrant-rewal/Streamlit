# Ammy's Choice Meal Planner

This repository now includes a standalone GitHub Pages-ready planner at:

- `docs/index.html`

## What is implemented in the HTML page

- 5-day selector (today + next 4 days)
- Auto-generate menu for a day if missing
- Whole-menu shuffle
- Individual meal swap (`Breakfast`, `Lunch`, `Dinner`)
- Preference save/clear
- Voice output (speech synthesis)
- Ingredients section for ordering
- Dish images for all 3 meals (via Pexels lookup)
- Uniqueness guard across 5-day planning (used in both full generation and single-meal reshuffle prompts)

## GitHub Pages hosting

In GitHub repo settings:

1. Go to **Settings → Pages**
2. Set Source to **Deploy from a branch**
3. Select branch `main` and folder `/docs`

Your page will be served from your GitHub Pages URL.

## Local run

```bash
python3 -m http.server 8080
```

Open:

```text
http://localhost:8080/docs/
```
