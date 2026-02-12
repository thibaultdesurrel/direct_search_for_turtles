from .player import Player


class Leaderboard:
    """
    Allow to follow the ranking of a game
    """

    def __init__(self, player_list: list[Player], nb_round: int):
        self.player_list = player_list
        self.nb_round = nb_round

        self.player_function_scores = {
            player.id: [None] * nb_round for player in player_list
        }

        self.player_scores = {
            player.id: [0] * nb_round for player in player_list
        }

    def __str__(self):
        return (
            f"Function scores: {self.player_function_scores}\n"
            f"Player scores: {self.player_scores}"
        )

    def update_function_score(self, player: Player, current_round: int, score: float):
        self.player_function_scores[player.id][current_round] = score

    def update_player_scores(self, current_round: int):
        """
        Compute the score for each player at the end of the round.
        Scoring: nb_players - position
        """
        nb_players = len(self.player_list)

        ranked_players = sorted(
            self.player_list,
            key=lambda p: self.player_function_scores[p.id][current_round],
            reverse=True
        )

        for idx, player in enumerate(ranked_players):
            points = nb_players - idx + 1
            self.player_scores[player.id][current_round] = points
