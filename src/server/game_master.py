import tkinter as tk
from tkinter import ttk


class GameMasterGUI:
    def __init__(self, game, lock):
        self.game = game
        self.lock = lock

        self.root = tk.Tk()
        self.root.title("Game Master Console")

        # Top frame: game settings
        self.frame_settings = ttk.Frame(self.root, padding=10)
        self.frame_settings.pack(fill="x")

        # Number of rounds
        ttk.Label(self.frame_settings, text="Number of rounds:").pack(side="left")
        self.round_var = tk.IntVar(value=self.game.nb_round)
        self.spin_rounds = ttk.Spinbox(
            self.frame_settings, from_=1, to=100, width=5, textvariable=self.round_var
        )
        self.spin_rounds.pack(side="left", padx=5)

        # Dimension selection
        ttk.Label(self.frame_settings, text="Function dim:").pack(
            side="left", padx=(10, 0)
        )
        self.dim_var = tk.StringVar(value="1")
        self.combo_dim = ttk.Combobox(
            self.frame_settings,
            textvariable=self.dim_var,
            values=["1", "2"],
            state="readonly",
            width=3,
        )
        self.combo_dim.pack(side="left", padx=5)

        # Difficulty selection
        ttk.Label(self.frame_settings, text="Difficulty:").pack(
            side="left", padx=(10, 0)
        )
        self.difficulty_var = tk.StringVar(value=self.game.difficulty)
        self.combo_difficulty = ttk.Combobox(
            self.frame_settings,
            textvariable=self.difficulty_var,
            values=["easy", "medium", "hard"],
            state="readonly",
            width=6,
        )

        self.combo_difficulty.pack(side="left", padx=5)

        # Number of step selection
        ttk.Label(self.frame_settings, text="Number of steps:").pack(
            side="left", padx=(10, 0)
        )
        self.nb_step_var = tk.IntVar(value=self.game.nb_step)
        self.combo_nb_step = ttk.Spinbox(
            self.frame_settings,
            textvariable=self.nb_step_var,
            from_=1,
            to=100,
            width=6,
        )
        self.combo_nb_step.pack(side="left", padx=5)

        # Number of step selection
        ttk.Label(self.frame_settings, text="Reveal radius:").pack(
            side="left", padx=(10, 0)
        )
        self.reveal_radius_var = tk.DoubleVar(value=self.game.reveal_radius)
        self.combo_reveal_radius = ttk.Spinbox(
            self.frame_settings,
            textvariable=self.reveal_radius_var,
            from_=0.1,
            to=10.0,
            width=6,
            increment=0.1,
        )
        self.combo_reveal_radius.pack(side="left", padx=5)

        # Force finish button
        self.button_force = ttk.Button(
            self.frame_settings, text="Force Finish", command=self.force_finish
        )
        self.button_force.pack(side="left", padx=10)

        # Connected players
        self.label_players = ttk.Label(self.root, text="Connected players: []")
        self.label_players.pack(anchor="w", padx=10)

        # Number of connected players
        self.label_players_count = ttk.Label(self.root, text="Number of players: 0")
        self.label_players_count.pack(anchor="w", padx=10, pady=5)

        # Game state frame
        self.frame_state = ttk.Frame(self.root, padding=10)
        self.frame_state.pack(fill="x")

        self.label_round = ttk.Label(self.frame_state, text="Round: 0")
        self.label_round.pack(anchor="w")

        self.label_function = ttk.Label(self.frame_state, text="Function: N/A")
        self.label_function.pack(anchor="w")

        self.label_submissions = ttk.Label(self.frame_state, text="Submissions: {}")
        self.label_submissions.pack(anchor="w")

        self.label_leaderboard = ttk.Label(self.frame_state, text="Leaderboard: N/A")
        self.label_leaderboard.pack(anchor="w")

        # Buttons frame
        self.frame_buttons = ttk.Frame(self.root, padding=10)
        self.frame_buttons.pack(fill="x")

        self.button_start = ttk.Button(
            self.frame_buttons, text="Start Game", command=self.start_game
        )
        self.button_start.pack(side="left", padx=5)

        self.button_reset = ttk.Button(
            self.frame_buttons, text="Reset Game", command=self.reset_game
        )
        self.button_reset.pack(side="left", padx=5)

        # Start periodic GUI update
        self.update_gui()

    def show_status(self, text, duration=3000):
        """
        Show a temporary message in the leaderboard label
        """
        self.label_leaderboard.config(text=f"Status: {text}")
        self.root.after(
            duration, self.update_leaderboard
        )  # restore leaderboard after duration

    def update_leaderboard(self):
        if self.game.leaderboard:
            leaderboard_text = {
                p.username: self.game.leaderboard.player_scores.get(p.id, [])
                for p in self.game.player_list
            }
        else:
            leaderboard_text = "N/A"
        self.label_leaderboard.config(text=f"Leaderboard: {leaderboard_text}")

    def start_game(self):
        with self.lock:
            if self.game.started:
                self.show_status("Game already started")
                return

            if len(self.game.player_list) == 0:
                self.show_status("No players connected!")
                return

            # Read the number of rounds **directly from the Spinbox text**
            try:
                self.game.nb_round = int(self.spin_rounds.get())
            except ValueError:
                self.show_status("Invalid number of rounds!")
                return

            try:
                self.game.difficulty = self.difficulty_var.get()
            except ValueError:
                self.show_status("Invalid difficulty!")
                return

            try:
                self.game.nb_step = int(self.nb_step_var.get())
            except ValueError:
                self.show_status("Invalid number of steps!")
                return

            try:
                self.game.reveal_radius = float(self.reveal_radius_var.get())
            except ValueError:
                self.show_status("Invalid reveal radius!")
                return

            selected_dim = int(self.dim_var.get())
            print(f"### dim is {selected_dim} ###")
            self.game.start(dim=selected_dim)

            print(
                f"Game started with {len(self.game.player_list)} players, {self.game.nb_round} rounds, dim={selected_dim}"
            )
            self.show_status(f"Game started (dim={selected_dim})")

    def reset_game(self):
        with self.lock:
            self.game.reset_game()
            print("Game has been reset")

    def force_finish(self):
        with self.lock:
            if not self.game.started:
                # Instead of a modal messagebox, show a temporary status
                self.label_leaderboard.config(text="Status: Game is not running")
                return

            # Mark all rounds as finished
            self.game.current_round = self.game.nb_round - 1
            # Send GAME over to all clients
            for p in self.game.player_list:
                try:
                    p.handler.send("GAME over")
                except e:
                    self.show_status("Error while ending the game")
            self.game.reset_game()
            print("Game was force finished")
            self.label_leaderboard.config(text="Status: Game force finished")

    def update_gui(self):
        with self.lock:
            # Update connected players
            players = [p.username or f"id{p.id}" for p in self.game.player_list]
            self.label_players.config(text=f"Connected players: {players}")
            self.label_players_count.config(text=f"Number of players: {len(players)}")

            # Update round
            self.label_round.config(
                text=f"Round: {self.game.current_round + 1 if self.game.started else 0}"
            )

            # Update current function
            current_func = (
                self.game.send_function(self.game.current_round).seed
                if self.game.started
                else "N/A"
            )
            self.label_function.config(text=f"Function: {current_func}")

            # Update submissions
            if self.game.started:
                submissions = {
                    p.username: self.game.submissions.get(p.id, False)
                    for p in self.game.player_list
                }
            else:
                submissions = {}
            self.label_submissions.config(text=f"Submissions: {submissions}")

            # Update leaderboard
            if self.game.leaderboard:
                leaderboard_text = {
                    p.username: self.game.leaderboard.player_scores.get(p.id, [])
                    for p in self.game.player_list
                }
            else:
                leaderboard_text = "N/A"
            self.label_leaderboard.config(text=f"Leaderboard: {leaderboard_text}")

        # Refresh every 1 second
        self.root.after(1000, self.update_gui)
