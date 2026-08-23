"""Browser (pygbag/WASM) entry point for the Thingamabob/Metro Simulator.

Kept separate from python/app/main.py so the desktop entry stays untouched.
The deploy workflow copies the python/ source tree in beside this file before
building, so the `app` and `features` packages import normally in the browser.
"""
import asyncio
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _candidate in (os.path.join(_HERE, "python"), os.path.join(_HERE, "..", "python")):
    if os.path.isdir(_candidate):
        sys.path.insert(0, _candidate)
        break


async def main() -> None:
    """Boot the app, then yield to the browser event loop each frame."""
    from app.builder import WaitingSimulatorBuilder

    WaitingSimulatorBuilder()
    while True:
        await asyncio.sleep(0)


asyncio.run(main())
