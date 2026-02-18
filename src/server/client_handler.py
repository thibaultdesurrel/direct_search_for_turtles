from .player import Player

class ClientHandler:
    def __init__(self, id: int, connection, addr, game, lock):
        self.id = id
        self.connection = connection
        self.addr = addr
        self.player = Player("", id, self)
        self.game = game
        self.lock = lock
        self.current_round = 0
        self.running = True

    def run(self):
        try:
            while self.running:
                data = self.connection.recv(1024)
                if not data:
                    break

                message = data.decode().strip()
                self.handle_message(message)

        except Exception as e:
            # Optional: log the error
            print(f"Error with player {self.id}: {e}")

        finally:
            self.running = False
            self.connection.close()
            # Remove the player from the game
            if self.game:
                with self.lock:  # if your game uses a lock for thread safety
                    self.game.remove_player(self.player)
            print(f"Player {self.id} has left the game")

    def handle_message(self, message: str):
        parts = message.split(" ")
        code = parts[0]
        args = parts[1:]

        print(f"Connection {self.id} sends {message}")

        if code == "USERNAME":
            self.handle_username(args)
        elif code == "GAME":
            self.handle_game()
        elif code == "SCORE":
            self.handle_score(args)
        else:
            self.send("ERROR unknown")

    def handle_username(self, args):
        if not args:
            self.send("USERNAME taken")
            return

        username = args[0]

        with self.lock:
            for p in self.game.player_list:
                if p.username == username:
                    self.send("USERNAME taken")
                    return

            self.player.update_username(username)
            self.send("USERNAME ok")

    def handle_game(self):
        with self.lock:
            if self.game.started:
                self.send("GAME unavailable")
                return

            if self.player not in self.game.player_list:
                self.game.player_list.append(self.player)
                self.player.game = self.game

            self.send("GAME ok")


    def handle_score(self, args):
        if not args:
            return

        score = float(args[0])
        pos_str = args[1] if len(args) > 1 else ""

        with self.lock:
            if not self.game.started:
                self.send("ERROR game not started")
                return
            self.game.compute_score(self.player, score, pos_str)


    def send(self, message: str):
        print(f"Sending {message} to player {self.player.id}")
        self.connection.sendall(f'"{message}"\n'.encode())
