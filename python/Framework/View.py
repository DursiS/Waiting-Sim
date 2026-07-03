from Adapters import Controller, Presenter


class View:

    def __init__(self, controller: Controller, presenter: Presenter) -> None:
        pass


if __name__ == "__main__":
    view = View(Controller(), Presenter())
