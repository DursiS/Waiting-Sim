from UseCases.PresenterGateway import PresenterGateway


class Presenter(PresenterGateway):
    def say_expected_times(self, expected_times: list[float]) -> None:
        """Display the expected wait times."""
        print(f"Expected wait times: {expected_times}")

    def say_sequenced_wait_times(self, wait_times: list[float]) -> None:
        """Display the sampled wait times in sequence."""
        print(f"Wait times: {wait_times}")

    def say_wait_time_metrics(self, wait_times: list[float]) -> None:
        """Display metrics summarizing the wait times."""
        print(f"Wait time metrics: {wait_times}")

    def prompt_to_continue(self) -> None:
        """Prompt the user to continue."""
        print("Press any key to continue...")

    def prompt_where_to_move(self) -> None:
        """Prompt the user for where to move next."""
        print("Where would you like to move?")
