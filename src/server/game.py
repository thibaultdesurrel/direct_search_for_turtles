from leaderboard import Leaderboard
from function_generator import FunctionGenerator


class Game:
    """
    Defines a game
    """

    def __init__(self, dim: int, player_list: list, nb_round: int):
        self.nb_round = nb_round
        self.player_list = player_list
        self.current_round = 0
        self.started = False

        self.leaderboard = None
        self.function_generator = FunctionGenerator(dim)
        self.function_list = [
            self.function_generator.generate()
            for _ in range(nb_round)
        ]

        for player in player_list:
            player.game = self

    def send_function(self, current_round: int):
        """
        Returns the function for the given round
        """
        return self.function_list[current_round]

    def compute_score(self, player, score: float, current_round: int):
        """
        Register a player's score for a round
        """
        self.leaderboard.update_function_score(player, current_round, score)

        if self._round_complete(current_round):
            self.leaderboard.update_player_scores(current_round)
            self.current_round += 1

    def _round_complete(self, current_round: int) -> bool:
        """
        Check if all players submitted a score for the round
        """
        for player in self.player_list:
            if self.leaderboard.player_function_scores[player.id][current_round] is None:
                return False
        return True

    def ready_to_start(self):
        return len(self.player_list) >= 1

    def start(self):
        
        for player in self.player_list:
            player.handler.send(f"GAME start {self.nb_round}")
        self.started = True
        self.leaderboard = Leaderboard(self.player_list, self.nb_round)

    def round_finished(self, current_round: int):
        for player in self.player_list:
            if self.leaderboard.player_function_scores[player.id][current_round] is None:
                return False
        return True

    def get_player_result(self, player, current_round):
        scores = self.leaderboard.player_scores[player.id][current_round]

        ranked = sorted(
            self.player_list,
            key=lambda p: self.leaderboard.player_function_scores[p.id][current_round],
            reverse=True
        )

        position = ranked.index(player) + 1
        points = scores
        return position, points


