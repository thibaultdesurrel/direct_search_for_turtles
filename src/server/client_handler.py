from player import Player

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

                raw = data.decode().strip()
                if not raw.startswith('C"') or not raw.endswith('"'):
                    self.send("ERROR protocol")
                    continue

                message = raw[2:-1]
                self.handle_message(message)

        finally:
            self.connection.close()

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

        with self.lock:
            if not self.game.started:
                self.send("ERROR game not started")
                return
            self.game.compute_score(self.player, score)


    def send(self, message: str):
        self.connection.sendall(f'S"{message}"\n'.encode())
