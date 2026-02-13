import tkinter as tk
from tkinter import ttk

class LeaderboardDisplay:
    """
    Large leaderboard display for all players.
    Freezes final scores until a new game starts.
    """

    def __init__(self, game, lock):
        self.game = game
        self.lock = lock

        self.last_started_state = False
        self.frozen_data = []

        # Create window as a secondary Toplevel (requires a Tk root to exist already)
        self.root = tk.Toplevel()
        self.root.title("Game Leaderboard")

        screen_width = self.root.winfo_screenwidth() // 3
        screen_height = self.root.winfo_screenheight() // 3
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.root.resizable(False, False)

        # Header
        self.label_title = tk.Label(
            self.root,
            text="🏆 Game Leaderboard 🏆",
            font=("Arial", 48),
            fg="white",
            bg="black"
        )
        self.label_title.pack(fill="x")

        # Treeview
        self.tree = ttk.Treeview(self.root, columns=("name", "score"), show="headings")
        self.tree.heading("name", text="Player")
        self.tree.heading("score", text="Score")
        self.tree.pack(fill="both", expand=True)

        # Style
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 36), rowheight=60)
        style.configure("Treeview.Heading", font=("Arial", 44, "bold"))

        self.update_leaderboard()

    def update_leaderboard(self):
        with self.lock:
            data = self._collect_scores()
            self._render(data)

        self.root.after(1000, self.update_leaderboard)
        
    def _collect_scores(self):
        # Frozen state → show snapshot
        if self.game.leaderboard and self.game.leaderboard.frozen:
            data = []
            for pid, score in self.game.leaderboard.frozen_snapshot:
                name = f"id{pid}"
                for p in self.game.leaderboard.player_list:
                    if p.id == pid:
                        name = p.username
                data.append((name, score))
            return sorted(data, key=lambda x: x[1], reverse=True)

        # Live game
        data = []
        for player in self.game.player_list:
            total_score = 0
            if self.game.leaderboard:
                scores = self.game.leaderboard.player_scores.get(player.id, [])
                total_score = sum(score or 0 for score in scores)
            data.append((player.username or f"id{player.id}", total_score))

        return sorted(data, key=lambda x: x[1], reverse=True)

    def _render(self, data):
        # Clear rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insert rows
        for name, score in data:
            self.tree.insert("", "end", values=(name, score))

        # Highlight winner
        if data:
            top_item = self.tree.get_children()[0]
            self.tree.item(top_item, tags=("top",))
            self.tree.tag_configure(
                "top",
                background="gold",
                font=("Arial", 48, "bold")
            )
