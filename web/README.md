# Web build (GitHub Pages)

This directory holds the framework for running Waiting-Sim **live in the
browser**. The desktop app is a `pygame` program, so it is compiled to
WebAssembly with [pygbag](https://pygame-web.github.io/) (pygame-on-web via
Pyodide) and published to GitHub Pages.

Nothing under `python/` is modified — `web/main.py` is a separate entry point
and the deploy workflow copies the source tree in beside it at build time.

## How it deploys

`.github/workflows/deploy-pages.yml` runs on every push to `main` (and on
manual dispatch):

1. Copies `python/` to `web/python/` so the packaged bundle can import
   `App`, `Data`, `Entities`, `Features`.
2. `pip install pygbag`, then `python -m pygbag --build web/main.py`, which
   emits a static site to `web/build/web/`.
3. Uploads that folder and deploys it to GitHub Pages.

### One-time setup (in the repo, not code)

Enable Pages once: **Settings → Pages → Build and deployment → Source →
GitHub Actions**. The site then publishes to
`https://<user>.github.io/<repo>/` after the workflow runs.

## Preview locally

```bash
cp -r python web/python        # or rely on the ../python fallback in main.py
python -m pip install pygbag
python -m pygbag web/main.py    # serves at http://localhost:8000
```

## Known limitations (needed for full interactivity)

This branch sets up the pipeline without touching game code. To make the app
actually *playable* in-browser, follow-ups are required (on their own,
non-additive branch):

1. **Async game loop.** The desktop loops (`ViewFacade` menu, `GameView`,
   `SimulationView`) block with `while` + `time.sleep`. A browser tab freezes
   unless the loop `await asyncio.sleep(0)`s each frame. This needs a small
   refactor of the view loops.
2. **scipy.** The app draws wait times from `scipy.stats`. scipy is large and
   slow to load under Pyodide; a lightweight pure-Python replacement for the
   handful of discrete distributions used would make the build far leaner.
3. **Persistence.** `player_data.json` / `highscores.json` writes land in the
   in-memory virtual filesystem and do not survive a reload without wiring up
   IndexedDB.
