from features.metro.inner import MetroInputData


class MetroOptionSelectionController:
    """Assembles a validated Metro request from the option-selection screen's
    raw field values, returning None and a message when the inputs are invalid."""

    def build_request(
        self,
        mode: str,
        name: str,
        map_id: int,
        rand_arrival: bool,
        animate: bool,
        bet_low: str,
        bet_high: str,
        bet_stake: str,
        balance: float,
    ) -> tuple[MetroInputData | None, str]:
        """Return a MetroInputData for the chosen mode, or (None, error)."""
        clean_name = name.strip() or "Player1"
        if mode == "play":
            return (
                MetroInputData(
                    name=clean_name,
                    map_id=map_id,
                    rand_arrival=rand_arrival,
                    gamble=False,
                    raw_bets=None,
                    animate=animate,
                ),
                "",
            )
        if mode == "gamble":
            bet, error = self._build_bet(bet_low, bet_high, bet_stake, balance)
            if bet is None:
                return None, error
            return (
                MetroInputData(
                    name=clean_name,
                    map_id=map_id,
                    rand_arrival=rand_arrival,
                    gamble=True,
                    raw_bets=[bet],
                    animate=animate,
                ),
                "",
            )
        return None, "Simulation isn't ready yet."

    def _build_bet(
        self, bet_low: str, bet_high: str, bet_stake: str, balance: float
    ) -> tuple[dict | None, str]:
        """Validate the interval bet fields into one raw bet, or (None, error)."""
        if not (bet_low.isdigit() and bet_high.isdigit()):
            return None, "Bet interval must be whole numbers."
        low, high = int(bet_low), int(bet_high)
        if low <= 0 or high < low:
            return None, "Bet interval needs 0 < from <= to."
        try:
            stake = float(bet_stake)
        except ValueError:
            return None, "Stake must be a number."
        if stake <= 0:
            return None, "Stake must be positive."
        if stake > balance:
            return None, "Stake exceeds your balance."
        return {"low": low, "high": high, "amount": stake}, ""
