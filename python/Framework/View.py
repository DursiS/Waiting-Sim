from Adapters import Controller, Presenter


class View:

    def __init__(self, controller: Controller, presenter: Presenter) -> None:
        pass

    def on_simulate_selected(self, raw_n: str) -> None:
        if self._busy:
            return
        self._busy = True
        try:
            self._controller.handle_simulate(raw_n)
        finally:
            self._busy = False


if __name__ == "__main__":
    view = View(Controller(), Presenter())
