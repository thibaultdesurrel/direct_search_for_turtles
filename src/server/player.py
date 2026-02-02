class Player:
    """
    Represents a player
    """

    def __init__(self, username: str, id: int, handler):
        self.username = username
        self.id = id
        self.game = None
        self.handler = handler

    def __str__(self):
        return f"Player {self.id}: {self.username}"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Player) and self.id == other.id

    def update_username(self, username: str):
        self.username = username
        print(f"Player {self.id} sets username to {self.username}")
