import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk


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

        self.label_round_status = ttk.Label(
            self.frame_state, text="", font=("Arial", 12, "bold")
        )
        self.label_round_status.pack(anchor="w", pady=(4, 0))

        self.label_leaderboard = ttk.Label(self.frame_state, text="Leaderboard: N/A")
        self.label_leaderboard.pack(anchor="w")

        # Buttons frame
        self.frame_buttons = ttk.Frame(self.root, padding=10)
        self.frame_buttons.pack(fill="x")

        self.button_start = ttk.Button(
            self.frame_buttons, text="Start Game", command=self.start_game
        )
        self.button_start.pack(side="left", padx=5)

        self.button_reveal = ttk.Button(
            self.frame_buttons, text="Reveal Function", command=self.reveal_function
        )
        self.button_reveal.pack(side="left", padx=5)

        self.button_next_round = ttk.Button(
            self.frame_buttons, text="Next Round", command=self.next_round
        )
        self.button_next_round.pack(side="left", padx=5)

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
            for p in self.game.player_list:
                try:
                    p.handler.send("GAME over")
                except Exception:
                    pass
            self.game.reset_game(kick=True)
            print("Game has been reset")

    def reveal_function(self):
        with self.lock:
            if not self.game.waiting_for_next_round:
                self.show_status("Round not finished yet")
                return
            self.game.reveal()

            # Collect data for server-side visualization
            func = self.game.function_list[self.game.current_round]
            domain = self.game.function_generator._domain
            dim = self.game.dim
            current_round = self.game.current_round
            players_data = []
            for p in self.game.player_list:
                pos_str = self.game.player_positions.get(p.id, "")
                score = self.game.leaderboard.player_function_scores[p.id][self.game.current_round]
                if score is None or score == float("inf") or not pos_str:
                    continue
                if dim == 1:
                    pos = float(pos_str)
                else:
                    x, y = pos_str.split(",")
                    pos = [float(x), float(y)]
                players_data.append((p.username, pos, score))

            self.show_status("Function revealed to all players")

        self._open_reveal_window(func, domain, dim, current_round, players_data)

    def _open_reveal_window(self, func, domain, dim, current_round, players_data):
        PLAYER_COLORS = [
            "#e74c3c", "#e67e22", "#27ae60", "#8e44ad",
            "#16a085", "#f39c12", "#124ef3", "#1df312",
        ]

        c_width, c_height = 800, 600
        min_x, max_x = domain

        win = tk.Toplevel(self.root)
        win.title(f"Function Reveal - Round {current_round + 1}")
        canvas = tk.Canvas(win, width=c_width, height=c_height, bg="white")
        canvas.pack()

        if dim == 1:
            # Compute adaptive Y scaling from full function range
            xs_full = np.linspace(min_x, max_x, 600)
            ys_full = func._raw_eval(xs_full)
            f_min, f_max = float(ys_full.min()), float(ys_full.max())
            f_range = f_max - f_min if f_max != f_min else 1.0
            margin = c_height * 0.12
            scale_y = (c_height - 2 * margin) / f_range
            mid_y = int(margin + f_max * scale_y)
            scale_x = c_width / (max_x - min_x)

            # Draw full function curve
            xs_plot = np.linspace(min_x, max_x, c_width)
            ys_plot = func._raw_eval(xs_plot)
            pts = [(i, int(mid_y - ys_plot[i] * scale_y)) for i in range(c_width)]
            canvas.create_line(pts, fill="royalblue", width=2)

            # True minimum star
            m = func._true_minimum
            mpx = int((m["x"] - min_x) * scale_x)
            mpy = int(mid_y - m["y"] * scale_y)
            canvas.create_text(mpx, mpy, text="★", fill="gold", font=("Arial", 22))
            canvas.create_text(
                mpx, mpy - 22, text=f"min = {m['y']:.3f}",
                fill="#c0392b", font=("Arial", 10, "bold"),
            )

            # Player markers
            for i, (name, pos, score) in enumerate(players_data):
                color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
                px = int((pos - min_x) * scale_x)
                py = int(mid_y - func._raw_eval(float(pos)) * scale_y)
                canvas.create_oval(px - 7, py - 7, px + 7, py + 7, fill=color, outline="black", width=2)
                canvas.create_text(px, py - 20, text=name, fill=color, font=("Arial", 10, "bold"))
                canvas.create_text(px, py + 20, text=f"{score:.4f}", fill=color, font=("Arial", 9))

        else:
            y_min, y_max = domain
            scale_x = c_width / (max_x - min_x)
            scale_y = c_height / (y_max - y_min)

            # Build full heatmap
            n = 200
            xs = np.linspace(min_x, max_x, n)
            ys = np.linspace(y_min, y_max, n)
            X, Y = np.meshgrid(xs, ys)
            Z = func._raw_eval((X, Y))

            Z_min, Z_max = Z.min(), Z.max()
            Z_norm = (Z - Z_min) / max(Z_max - Z_min, 1e-10)

            R = (Z_norm * 255).astype(np.uint8)
            G = np.zeros_like(R)
            B = (255 - R).astype(np.uint8)
            img_arr = np.flipud(np.stack([R, G, B], axis=2))
            img = Image.fromarray(img_arr, "RGB").resize((c_width, c_height), Image.NEAREST)

            win._reveal_img = ImageTk.PhotoImage(img)
            canvas.create_image(0, 0, anchor="nw", image=win._reveal_img)

            # True minimum star
            m = func._true_minimum
            mpx = int((m["x"][0] - min_x) * scale_x)
            mpy = int(c_height - (m["x"][1] - y_min) * scale_y)
            canvas.create_text(mpx, mpy, text="★", fill="gold", font=("Arial", 22))
            canvas.create_text(
                mpx, mpy - 22, text=f"min = {m['y']:.3f}",
                fill="white", font=("Arial", 15, "bold"),
            )

            # Player markers
            for i, (name, pos, score) in enumerate(players_data):
                color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
                px = int((pos[0] - min_x) * scale_x)
                py = int(c_height - (pos[1] - y_min) * scale_y)
                canvas.create_oval(px - 7, py - 7, px + 7, py + 7, fill=color, outline="black", width=2)
                canvas.create_text(px, py - 20, text=name, fill="white", font=("Arial", 10, "bold"))
                canvas.create_text(px, py + 20, text=f"{score:.4f}", fill="white", font=("Arial", 9))

    def next_round(self):
        with self.lock:
            if not self.game.waiting_for_next_round:
                self.show_status("Not waiting for next round")
                return
            self.game.advance_round()
            print("Advanced to next round")

    def force_finish(self):
        with self.lock:
            if not self.game.started:
                self.label_leaderboard.config(text="Status: Game is not running")
                return

            if self.game.waiting_for_next_round:
                self.show_status("Round already finished")
                return

            # Force-submit every player who hasn't submitted yet (worst score)
            for p in self.game.player_list:
                if not self.game.submissions.get(p.id, False):
                    self.game.compute_score(p, float("inf"))

            print("Round force finished")
            self.show_status("Round force finished")

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
                n_done = sum(submissions.values())
                n_total = len(submissions)
            else:
                submissions = {}
                n_done = 0
                n_total = 0
            self.label_submissions.config(text=f"Submissions: {submissions}")

            # Round status indicator + button states
            if self.game.started and self.game.waiting_for_next_round:
                self.label_round_status.config(
                    text="✅ Tous les joueurs ont terminé le round !",
                    foreground="green",
                )
                self.button_reveal.config(state="normal")
                self.button_next_round.config(state="normal")
            elif self.game.started:
                self.label_round_status.config(
                    text=f"⏳ En cours... ({n_done}/{n_total} soumissions)",
                    foreground="orange",
                )
                self.button_reveal.config(state="disabled")
                self.button_next_round.config(state="disabled")
            else:
                self.label_round_status.config(text="", foreground="black")
                self.button_reveal.config(state="disabled")
                self.button_next_round.config(state="disabled")

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
