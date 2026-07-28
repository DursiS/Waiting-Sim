"""Browser (pygbag/WASM) entry point for Waiting-Sim.

Kept separate from python/App/main.py so the desktop entry stays untouched.
The deploy workflow copies the python/ source tree in beside this file before
building, so App, Data, Entities and Features import normally in the browser.
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
    from App import WaitingSimulatorBuilder

    WaitingSimulatorBuilder()
    while True:
        await asyncio.sleep(0)


asyncio.run(main())
