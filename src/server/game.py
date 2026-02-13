from .leaderboard import Leaderboard
from ..shared.function_generator_claude import FunctionGenerator

class Game:
    """
    Defines a game
    """

    def __init__(self, dim: int, player_list: list, nb_round: int):
        self.nb_round = nb_round
        self.player_list = player_list
        self.current_round = 0
        self.started = False
        self.dim = dim

        self.leaderboard = None
        self.function_generator = None
        self.function_list = None

        self.submissions = {}  # track who submitted score for current round

        for player in player_list:
            player.game = self

    def send_function(self, current_round: int):
        """
        Returns the function for the given round
        """
        return self.function_list[current_round]

    def compute_score(self, player, score: float):
        if self.submissions[player.id]:
            return

        # register player's score
        self.leaderboard.update_function_score(player, self.current_round, score)
        self.submissions[player.id] = True

        # check if all players submitted
        if all(self.submissions.values()):
            # compute points
            self.leaderboard.update_player_scores(self.current_round)

            # broadcast results
            for p in self.player_list:
                pos, pts = self.get_player_result(p, self.current_round)

            # move to next round if any
            if self.current_round + 1 < self.nb_round:
                self.current_round += 1
                print(f"Going to round {self.current_round}")
                # reset submissions for next round
                self.submissions = {p.id: False for p in self.player_list}

                # send next function
                for p in self.player_list:
                    p.handler.send(f"FUNC {self.send_function(self.current_round).seed}")
            else:
                # game over
                for p in self.player_list:
                    p.handler.send("GAME over")

                # reset game state so players must rejoin
                self.reset_game(kick=True)

    def _round_complete(self, current_round: int) -> bool:
        """
        Check if all players submitted a score for the round
        """
        for player in self.player_list:
            if (
                self.leaderboard.player_function_scores[player.id][current_round]
                is None
            ):
                return False
        return True

    def ready_to_start(self):
        return len(self.player_list) >= 1

    def start(self, dim: int = None):
        if dim is None:
            dim = self.dim  # fallback to stored dim
        self.dim = dim
        if self.leaderboard is None:
            self.leaderboard = Leaderboard(self.player_list, self.nb_round)
        else:
            self.leaderboard.unfreeze(self.player_list, self.nb_round)
        self.started = True
        self.current_round = 0
        self.submissions = {p.id: False for p in self.player_list}
        self.function_generator = FunctionGenerator(dim)
        self.function_list = [
            self.function_generator.generate() for _ in range(self.nb_round)
        ]

        # broadcast game start
        for player in self.player_list:
            player.handler.send(f"GAME start {self.nb_round} {self.dim} {self.function_generator._difficulty} {self.function_generator._domain}")
            function_seed = self.send_function(self.current_round).seed
            player.handler.send(f"FUNC {function_seed}")

    def round_finished(self, current_round: int):
        for player in self.player_list:
            if (
                self.leaderboard.player_function_scores[player.id][current_round]
                is None
            ):
                return False
        return True

    def get_player_result(self, player, current_round):
        scores = self.leaderboard.player_scores[player.id][current_round]

        ranked = sorted(
            self.player_list,
            key=lambda p: self.leaderboard.player_function_scores[p.id][current_round],
            reverse=True,
        )

        position = ranked.index(player) + 1
        points = scores
        return position, points

    def reset_game(self, kick=False):
        self.started = False
        self.current_round = 0
        self.submissions = {}
        if kick:
            self.player_list = []  # Kick all players from the game
        if self.leaderboard:
            self.leaderboard.freeze()

    def remove_player(self, player):
        """
        Remove a player from the game, updating submissions and leaderboard
        """
        if player in self.player_list:
            self.player_list.remove(player)
            # Remove from submissions tracking
            if player.id in self.submissions:
                del self.submissions[player.id]
            # Optional: remove player from leaderboard
            if self.leaderboard:
                self.leaderboard.remove_player(player)
            print(f"Player {player.id} removed from the game.")

            # If no players left, reset the game
            if not self.player_list:
                self.reset_game(kick=True)
