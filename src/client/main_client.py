import tkinter as tk
from tkinter import messagebox
from tkinter import font

my_font = ("Segoe UI Symbol", 10)  # Police qui gère bien les flèches
import socket
import threading
import random
import math
from PIL import Image, ImageTk
from ..shared.function_generator_claude import FunctionGenerator, Difficulty

# -------------------------
# Global state
# -------------------------
sock = None
username = None
server_function = None
server_function_generator = None
nb_round = None
joined_game = False
waiting_for_start = False
waiting_for_func = False
current_x = 0.0
steps_left = None
step_size = 1.0
direction = 1


# -------------------------
# Networking helpers
# -------------------------
def send(msg):
    print(f"Sending {msg}")
    sock.sendall((msg + "\n").encode())


buffer = ""  # Keep a buffer outside the function


def receive():
    global buffer
    while "\n" not in buffer:
        data = sock.recv(1024).decode()
        if not data:
            raise ConnectionError("Server closed the connection")
        buffer += data

    # Split one complete message from the buffer
    line, buffer = buffer.split("\n", 1)
    msg = line.strip().strip('"')
    print(f"Got {msg}")
    return msg


# -------------------------
# Connection window
# -------------------------
class ConnectionWindow:
    def __init__(self, root):
        self.root = root
        root.title("Connexion")

        tk.Label(root, text="Nom d'utilisateur").grid(row=0, column=0)
        tk.Label(root, text="Adresse du serveur").grid(row=1, column=0)
        tk.Label(root, text="Port").grid(row=2, column=0)

        self.user_entry = tk.Entry(root)
        self.addr_entry = tk.Entry(root)
        self.port_entry = tk.Entry(root)

        self.user_entry.grid(row=0, column=1)
        self.addr_entry.grid(row=1, column=1)
        self.port_entry.grid(row=2, column=1)

        tk.Button(root, text="Connexion", command=self.connect).grid(
            row=3, column=0, columnspan=2
        )

    def connect(self):
        global sock, username

        username = self.user_entry.get().strip()
        addr = self.addr_entry.get().strip()
        port = self.port_entry.get().strip()

        if not username or not addr or not port:
            messagebox.showerror("Erreur", "Tous les champs doivent être remplis")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((addr, int(port)))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
            return

        send(f"USERNAME {username}")
        reply = receive()

        if reply == "USERNAME ok":
            self.root.destroy()
            open_game_window()
        elif reply == "USERNAME taken":
            messagebox.showerror("Erreur", "Nom d'utilisateur déjà pris")
        else:
            print(repr(reply), type(reply))
            messagebox.showerror("Erreur", f"Réponse serveur inconnue {reply}")


# -------------------------
# Game window
# -------------------------
class GameWindow:

    # Canvas size
    c_width = 800
    c_height = 600

    def __init__(self, root):
        self.root = root
        root.title("Jeu")

        self.turtle_pil = Image.open("src/assets/tortue.png").convert("RGBA")
        self.turtle_pil = self.turtle_pil.resize((40, 30), Image.LANCZOS)
        self.turtle_img = ImageTk.PhotoImage(self.turtle_pil)
        self._rotated_turtle_img = None  # keep reference to avoid GC
        self.water_img = tk.PhotoImage(file="src/assets/water.png")
        self.sand_img = tk.PhotoImage(file="src/assets/beach.png")

        self.canvas = tk.Canvas(
            root, width=self.c_width, height=self.c_height, bg="white"
        )
        self.canvas.pack()

        self.info_label = tk.Label(root, text="Pas restants: 10")
        self.info_label.pack()

        self.info_step = tk.Label(root, text="Taille de pas: 1")
        self.info_step.pack()

        control_frame = tk.Frame(root)
        control_frame.pack()

        self.root.focus_set()
        self.root.after(100, lambda: self.root.focus_force())

        self.dir_var = tk.StringVar(value="0")

        # tk.Button(control_frame, text="↑", command=lambda: self.set_dir("up")).grid(
        #     row=0, column=1
        # )
        # tk.Button(control_frame, text="←", command=lambda: self.set_dir("left")).grid(
        #     row=1, column=0
        # )
        # tk.Button(control_frame, text="↓", command=lambda: self.set_dir("down")).grid(
        #     row=1, column=1
        # )
        # tk.Button(control_frame, text="→", command=lambda: self.set_dir("right")).grid(
        #     row=1, column=2
        # )

        tk.Button(
            control_frame, text="↑", font=my_font, command=lambda: self.move("up")
        ).grid(row=0, column=1)
        tk.Button(
            control_frame, text="←", font=my_font, command=lambda: self.move("left")
        ).grid(row=1, column=0)
        tk.Button(
            control_frame, text="↓", font=my_font, command=lambda: self.move("down")
        ).grid(row=1, column=1)
        tk.Button(
            control_frame, text="→", font=my_font, command=lambda: self.move("right")
        ).grid(row=1, column=2)

        tk.Button(control_frame, text="- Pas", command=self.decrease_step).grid(
            row=2, column=0
        )
        tk.Button(control_frame, text="+ Pas", command=self.increase_step).grid(
            row=2, column=1
        )
        # tk.Button(control_frame, text="Faire pas", command=self.make_step).grid(
        #     row=2, column=2
        # )

        tk.Button(root, text="Rejoindre une partie", command=self.join_game).pack()

        self.reveal_radius = 0.5
        self.explored_ranges = []

        # Current position in 1D or 2D
        self.current_pos = [0.0, 0.0]  # x for 1D, [x, y] for 2D
        self.dim = 1
        self.direction = "right"

    def bind_keys(self):
        # On nettoie d'abord les anciens binds
        self.root.unbind("<Up>")
        self.root.unbind("<Down>")
        self.root.unbind("<Left>")
        self.root.unbind("<Right>")

        if self.dim == 1:
            # En 1D → seulement gauche / droite
            self.root.bind("<Left>", lambda e: self.move("left"))
            self.root.bind("<Right>", lambda e: self.move("right"))
        else:
            # En 2D → toutes les flèches
            self.root.bind("<Up>", lambda e: self.move("up"))
            self.root.bind("<Down>", lambda e: self.move("down"))
            self.root.bind("<Left>", lambda e: self.move("left"))
            self.root.bind("<Right>", lambda e: self.move("right"))

        self.root.after(50, lambda: self.root.focus_force())

    def join_game(self):
        global joined_game, waiting_for_start

        if joined_game or waiting_for_start:
            return  # ignore double click

        send("GAME")
        reply = receive()

        if reply == "GAME ok":
            joined_game = True
            waiting_for_start = True
            self.show_waiting_message()
            threading.Thread(target=self.wait_for_start, daemon=True).start()
        elif reply.startswith("GAME start"):
            # Server already started the game, handle immediately
            joined_game = True
            waiting_for_start = False
            self.handle_game_start(reply)
            threading.Thread(target=self.wait_for_func, daemon=True).start()
        else:
            messagebox.showinfo("Info", "Partie indisponible")

    def show_waiting_message(self):
        self.canvas.delete("all")
        self.canvas.create_text(
            self.c_width // 2,
            self.c_height // 2,
            text="La partie va commencer...",
            font=("Arial", 24, "bold"),
            fill="black",
        )

    def handle_game_start(self, msg):
        global server_function_generator, nb_round, steps_left, step_size

        split_msg = msg.split()
        nb_round = int(split_msg[2])
        self.dim = int(split_msg[3])
        difficulty_str = split_msg[4]
        difficulty = Difficulty[difficulty_str.upper()]
        self.steps_left_max = int(split_msg[5])
        self.reveal_radius = float(split_msg[6])
        step_size = 1.0
        steps_left = self.steps_left_max
        domain_str = " ".join(split_msg[7:]).strip()
        domain = tuple(float(x.strip()) for x in domain_str.strip("()").split(","))

        server_function_generator = FunctionGenerator(
            self.dim, difficulty=difficulty, domain=domain
        )

        if self.dim == 2:
            # Reset position to center of domain
            self.current_pos = [
                (domain[0] + domain[1]) / 2,
                (domain[0] + domain[1]) / 2,
            ]
        else:
            self.current_pos = [0.0]
        self.bind_keys()

    def wait_for_start(self):
        global waiting_for_start

        while True:
            msg = receive()
            print(f"Game start message is {msg}")

            if msg.startswith("GAME start"):
                waiting_for_start = False
                self.handle_game_start(msg)
                threading.Thread(target=self.wait_for_func, daemon=True).start()
                return

    def reset_client_game(self):
        global joined_game, waiting_for_start, waiting_for_func, step_size
        global server_function, server_function_generator
        global nb_round, steps_left, current_x

        joined_game = False
        waiting_for_start = False
        waiting_for_func = False

        server_function = None
        server_function_generator = None
        nb_round = None

        steps_left = self.steps_left_max
        print(f"Resetting client game, steps_left set to {steps_left}")
        current_x = 0.0
        step_size = 1.0
        self.explored_ranges = []

        self.canvas.delete("all")
        self.info_label.config(text="Pas restants: -")
        self.info_step.config(text="Taille de pas: 1")

        print("Client game state reset, waiting for join")

    def wait_for_func(self):
        global server_function, waiting_for_func

        if waiting_for_func:
            return

        waiting_for_func = True

        while True:
            msg = receive()

            if msg.startswith("FUNC"):
                seed = int(msg.split()[1])
                server_function = server_function_generator.generate(seed)

                global steps_left, step_size
                steps_left = self.steps_left_max
                step_size = 1.0
                self.current_pos = [0.0, 0.0]
                self.explored_ranges = []

                self.reveal_at(self.current_pos)
                self.draw_region()
                self.info_label.config(text=f"Pas restants: {steps_left}")
                self.info_step.config(text="Taille de pas: 1.0")

                # Stay in the loop: keep listening during the round so a
                # mid-round GAME over (Force Finish) is caught immediately.
                continue

            if msg.startswith("REVEAL"):
                players_data = self._parse_reveal(msg)
                self.root.after(0, lambda d=players_data: self.draw_reveal(d))
                self.root.after(
                    0, lambda: self.info_label.config(text="Fonction révélée !")
                )
                continue  # keep waiting for FUNC or GAME over

            if msg.startswith("GAME over"):
                waiting_for_func = False
                self.reset_client_game()
                return

    def reveal_at(self, pos):
        if self.dim == 1:
            min_x, max_x = server_function_generator._domain
            x = pos[0]
            a = max(x - self.reveal_radius, min_x)
            b = min(x + self.reveal_radius, max_x)
            self.explored_ranges.append((a, b))
            self.explored_ranges = self.merge_ranges(self.explored_ranges)
        else:
            # For 2D: store revealed rectangle around turtle
            x, y = pos
            x_min, x_max = server_function_generator._domain
            y_min, y_max = server_function_generator._domain
            a = max(x - self.reveal_radius, x_min)
            b = min(x + self.reveal_radius, x_max)
            c = max(y - self.reveal_radius, y_min)
            d = min(y + self.reveal_radius, y_max)
            self.explored_ranges.append((a, b, c, d))

    def merge_ranges(self, ranges):
        if not ranges:
            return []

        ranges.sort()
        merged = [ranges[0]]

        for start, end in ranges[1:]:
            last_start, last_end = merged[-1]
            if start <= last_end:
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))

        return merged

    def draw_region(self):
        self.canvas.delete("all")

        if self.dim == 1:

            # Sand (bottom)
            self.canvas.create_image(
                0,
                self.c_height - self.sand_img.height(),
                anchor="nw",
                image=self.sand_img,
            )

            min_x, max_x = server_function_generator._domain
            domain_width = max_x - min_x
            scale_x = self.c_width / domain_width
            scale_y = 20
            mid_y = self.c_height // 2

            for a, b in self.explored_ranges:
                start_px = int((a - min_x) * scale_x)
                end_px = int((b - min_x) * scale_x)
                prev = None
                for px in range(start_px, end_px + 1):
                    x = min_x + px / scale_x
                    y = server_function.evaluate(x)
                    py = mid_y - y * scale_y
                    if prev is not None:
                        self.canvas.create_line(prev[0], prev[1], px, py)
                    prev = (px, py)

            turtle_x = int((self.current_pos[0] - min_x) * scale_x)
            turtle_y = mid_y - server_function.evaluate(self.current_pos[0]) * scale_y

            # Compute slope for rotation
            eps = 0.01
            x0 = self.current_pos[0]
            slope = (
                server_function.evaluate(x0 + eps) - server_function.evaluate(x0 - eps)
            ) / (2 * eps)
            angle_deg = math.degrees(math.atan(slope * scale_y / scale_x))

            # Flip turtle image if going left
            img = self.turtle_pil
            if self.direction in ("left", "down"):
                img = img.transpose(Image.FLIP_LEFT_RIGHT)

            rotated = img.rotate(angle_deg, resample=Image.BICUBIC, expand=True)
            self._rotated_turtle_img = ImageTk.PhotoImage(rotated)
            self.canvas.create_image(
                turtle_x, turtle_y - 13, image=self._rotated_turtle_img
            )

        else:
            x_min, x_max = server_function_generator._domain
            y_min, y_max = server_function_generator._domain
            domain_width = x_max - x_min
            domain_height = y_max - y_min

            scale_x = self.c_width / domain_width
            scale_y = self.c_height / domain_height

            # Draw color map
            for rect in self.explored_ranges:
                a, b, c, d = rect
                steps = 20
                for i in range(steps):
                    for j in range(steps):
                        x = a + i * (b - a) / steps
                        y = c + j * (d - c) / steps
                        val = server_function.evaluate([x, y])
                        # Map val to color (blue=low, red=high)
                        color = "#%02x00%02x" % (
                            int(min(max(val * 255, 0), 255)),
                            int(255 - int(min(max(val * 255, 0), 255))),
                        )
                        px = int((x - x_min) * scale_x)
                        py = int(self.c_height - (y - y_min) * scale_y)
                        self.canvas.create_rectangle(
                            px,
                            py,
                            px + int(scale_x / steps) + 1,
                            py - int(scale_y / steps) - 1,
                            outline=color,
                            fill=color,
                        )

            # Draw turtle
            tx = int((self.current_pos[0] - x_min) * scale_x)
            ty = int(self.c_height - (self.current_pos[1] - y_min) * scale_y)
            self.canvas.create_oval(tx - 5, ty - 5, tx + 5, ty + 5, fill="red")

    def show_round_end(self, score):
        self.canvas.create_text(
            self.c_width // 2,
            30,
            text="Round terminé !",
            font=("Arial", 26, "bold"),
            fill="black",
        )
        self.canvas.create_text(
            self.c_width // 2,
            65,
            text=f"f(x) = {score:.4f}",
            font=("Arial", 22, "bold"),
            fill="#e74c3c",
        )
        self.canvas.create_text(
            self.c_width // 2,
            100,
            text="En attente du prochain round...",
            font=("Arial", 13),
            fill="gray",
        )

    def _parse_reveal(self, msg):
        """Parse REVEAL message into list of (username, pos, score)."""
        players_data = []
        tokens = msg.split()[1:]  # skip "REVEAL"
        for token in tokens:
            fields = token.split("|")
            if len(fields) < 3:
                continue
            name, pos_str, score_str = fields[0], fields[1], fields[2]
            score = float(score_str)
            if self.dim == 1:
                pos = float(pos_str)
            else:
                x, y = pos_str.split(",")
                pos = [float(x), float(y)]
            players_data.append((name, pos, score))
        return players_data

    def _draw_own_score(self, players_data):
        """Draw only the current player's score in the top-right corner."""
        my_score = next(
            (score for name, pos, score in players_data if name == username), None
        )
        if my_score is None:
            return

        pad = 10
        panel_w = 220
        panel_h = 70
        x0 = self.c_width - pad - panel_w
        y0 = pad

        self.canvas.create_rectangle(
            x0, y0, x0 + panel_w, y0 + panel_h,
            fill="#1a1a2e", outline="#555", width=1,
        )
        self.canvas.create_text(
            x0 + panel_w // 2, y0 + 18,
            text="Votre score", fill="white", font=("Arial", 13),
        )
        self.canvas.create_text(
            x0 + panel_w // 2, y0 + 48,
            text=f"{my_score:.4f}", fill="#e74c3c", font=("Arial", 22, "bold"),
        )

    def draw_reveal(self, players_data):
        """Draw the full function with true minimum and all players' final positions."""
        import numpy as np

        self.canvas.delete("all")

        PLAYER_COLORS = [
            "#e74c3c",
            "#e67e22",
            "#27ae60",
            "#8e44ad",
            "#16a085",
            "#f39c12",
            "#124ef3",
            "#1df312",
        ]

        if self.dim == 1:
            min_x, max_x = server_function_generator._domain
            domain_width = max_x - min_x
            scale_x = self.c_width / domain_width
            scale_y = 20
            mid_y = self.c_height // 2

            # Draw sand background
            self.canvas.create_image(
                0,
                self.c_height - self.sand_img.height(),
                anchor="nw",
                image=self.sand_img,
            )

            # Draw full function curve
            xs = np.linspace(min_x, max_x, self.c_width)
            ys = server_function._raw_eval(xs)
            pts = [(int(px), int(mid_y - ys[px] * scale_y)) for px in range(len(xs))]
            self.canvas.create_line(pts, fill="royalblue", width=2)

            # True minimum star
            m = server_function._true_minimum
            mpx = int((m["x"] - min_x) * scale_x)
            mpy = int(mid_y - m["y"] * scale_y)
            self.canvas.create_text(
                mpx, mpy, text="★", fill="gold", font=("Arial", 22)
            )
            self.canvas.create_text(
                mpx,
                mpy - 22,
                text=f"min = {m['y']:.3f}",
                fill="#c0392b",
                font=("Arial", 10, "bold"),
            )

            # Player markers
            for i, (name, pos, score) in enumerate(players_data):
                color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
                px = int((pos - min_x) * scale_x)
                py = int(mid_y - server_function._raw_eval(float(pos)) * scale_y)
                self.canvas.create_oval(
                    px - 7, py - 7, px + 7, py + 7, fill=color, outline="black", width=2
                )
                self.canvas.create_text(
                    px,
                    py - 20,
                    text=name,
                    fill=color,
                    font=("Arial", 10, "bold"),
                )

            self._draw_own_score(players_data)

        else:
            from PIL import Image, ImageTk

            x_min, x_max = server_function_generator._domain
            y_min, y_max = server_function_generator._domain
            scale_x = self.c_width / (x_max - x_min)
            scale_y = self.c_height / (y_max - y_min)

            # Build full heatmap via numpy
            n = 200
            xs = np.linspace(x_min, x_max, n)
            ys = np.linspace(y_min, y_max, n)
            X, Y = np.meshgrid(xs, ys)
            Z = server_function._raw_eval((X, Y))

            Z_min, Z_max = Z.min(), Z.max()
            Z_norm = (Z - Z_min) / max(Z_max - Z_min, 1e-10)

            R = (Z_norm * 255).astype(np.uint8)
            G = np.zeros_like(R)
            B = (255 - R).astype(np.uint8)
            img_arr = np.flipud(np.stack([R, G, B], axis=2))
            img = Image.fromarray(img_arr, "RGB").resize(
                (self.c_width, self.c_height), Image.NEAREST
            )
            self._reveal_img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor="nw", image=self._reveal_img)

            # True minimum star
            m = server_function._true_minimum
            mpx = int((m["x"][0] - x_min) * scale_x)
            mpy = int(self.c_height - (m["x"][1] - y_min) * scale_y)
            self.canvas.create_text(mpx, mpy, text="★", fill="gold", font=("Arial", 22))
            self.canvas.create_text(
                mpx,
                mpy - 22,
                text=f"min = {m['y']:.3f}",
                fill="white",
                font=("Arial", 15, "bold"),
            )

            # Player markers
            for i, (name, pos, score) in enumerate(players_data):
                color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
                px = int((pos[0] - x_min) * scale_x)
                py = int(self.c_height - (pos[1] - y_min) * scale_y)
                self.canvas.create_oval(
                    px - 7, py - 7, px + 7, py + 7, fill=color, outline="black", width=2
                )
                self.canvas.create_text(
                    px,
                    py - 20,
                    text=name,
                    fill="white",
                    font=("Arial", 10, "bold"),
                )

            self._draw_own_score(players_data)

    def set_dir(self, d):
        self.direction = d  # "up", "down", "left", "right"

    def increase_step(self):
        global step_size
        if step_size > 0.01:
            step_size = round(step_size * 1.3, ndigits=2)
        elif step_size <= 0.01:
            step_size = 0.02
        self.info_step.config(text=f"Taille de pas: {step_size}")

    def decrease_step(self):
        global step_size
        step_size = round(max(step_size * 0.7, 0), ndigits=2)
        self.info_step.config(text=f"Taille de pas: {step_size}")

    def move(self, direction):
        self.direction = direction
        self.make_step()

    def make_step(self):
        global steps_left

        if steps_left <= 0 or server_function_generator is None:
            return

        step = step_size
        if self.dim == 1:
            if self.direction in ("right", "up"):  # right
                if self.current_pos[0] + step >= server_function_generator._domain[1]:
                    self.current_pos[0] = server_function_generator._domain[1] - 0.02
                else:
                    self.current_pos[0] += step
            else:  # left
                if self.current_pos[0] - step <= server_function_generator._domain[0]:
                    self.current_pos[0] = server_function_generator._domain[0] + 0.02
                else:
                    self.current_pos[0] -= step
        else:
            if self.direction == "up":
                self.current_pos[1] += step
            elif self.direction == "down":
                self.current_pos[1] -= step
            elif self.direction == "left":
                self.current_pos[0] -= step
            elif self.direction == "right":
                self.current_pos[0] += step

        # Clamp position
        if self.dim == 1:
            min_x, max_x = server_function_generator._domain
            self.current_pos[0] = max(min(self.current_pos[0], max_x), min_x)
        else:
            x_min, x_max = server_function_generator._domain
            y_min, y_max = server_function_generator._domain
            self.current_pos[0] = max(min(self.current_pos[0], x_max), x_min)
            self.current_pos[1] = max(min(self.current_pos[1], y_max), y_min)

        self.reveal_at(self.current_pos)
        self.draw_region()

        steps_left -= 1
        self.info_label.config(text=f"Pas restants: {steps_left}")

        if steps_left == 0:
            if self.dim == 1:
                pos_arg = str(self.current_pos[0])
                score = server_function.evaluate(self.current_pos[0])
            else:
                pos_arg = f"{self.current_pos[0]},{self.current_pos[1]}"
                score = server_function.evaluate(self.current_pos)
            send(f"SCORE {score} {pos_arg}")
            self.show_round_end(score)
            threading.Thread(target=self.wait_for_func, daemon=True).start()


# -------------------------
# Startup
# -------------------------
def open_game_window():
    root = tk.Tk()
    GameWindow(root)
    root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    ConnectionWindow(root)
    root.mainloop()
