# Web build (GitHub Pages)

This directory holds the framework for running the app **live in the browser**.
The desktop app is a `pygame` program, so it is compiled to WebAssembly with
[pygbag](https://pygame-web.github.io/) (pygame-on-web via Pyodide) and
published to GitHub Pages.

Nothing under `python/` is modified — `web/main.py` is a separate entry point
and the deploy workflow copies the source tree in beside it at build time.

## How it deploys

`.github/workflows/deploy-pages.yml` runs on every push to `main` (and on
manual dispatch):

1. Copies `python/` to `web/python/` so the packaged bundle can import
   `app` and `features`.
2. `pip install pygbag`, then `python -m pygbag --build web/main.py`, which
   emits a static site to `web/build/web/`.
3. Uploads that folder and deploys it to GitHub Pages.

### One-time setup (in the repo, not code)

Enable Pages once: **Settings -> Pages -> Build and deployment -> Source ->
GitHub Actions**. The site then publishes to
`https://<user>.github.io/<repo>/` after the workflow runs.

## Preview locally

```bash
cp -r python web/python        # or rely on the ../python fallback in main.py
python -m pip install pygbag
python -m pygbag web/main.py    # serves at http://localhost:8000
```

## Required for interactivity (async port)

The pipeline above builds and deploys, but the app will **freeze the browser
tab** until the control flow is made cooperative. A WASM tab is single-threaded
and cannot block, so these are needed (a real refactor of the view/game loops):

1. **Async loops.** Every view loop (`ViewFacade`, `MetroOptionSelectionView`,
   `MetroView`, `MetroSimulationView`, `FlyingView`) blocks with `while` +
   `pygame.display.flip()`. Each must `await asyncio.sleep(0)` per frame, and
   the nested "launch a sub-view" calls must `await` the sub-view's loop.
2. **No threads.** `MetroView` runs the game on a `threading.Thread`; WASM has
   no real threads, so the game must run cooperatively (the interactor's turn
   loop yielding between turns).
3. **No `time.sleep`.** The turn animation in `MetroPresenter` sleeps; it must
   `await asyncio.sleep(...)`, which makes `present_game_turn` and the
   interactor's `execute`/`_setup_game` loop async.
4. **scipy.** Wait-time distributions and the transition integrals use
   `scipy.stats`/`scipy.integrate`, which are heavy under Pyodide. A
   pure-Python replacement for the handful of discrete distributions used would
   make the bundle far leaner and faster to load.
