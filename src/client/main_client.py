import tkinter as tk
from tkinter import messagebox
import socket
import threading
import random
import math
from ..shared.function_generator_claude import FunctionGenerator, Difficulty

# -------------------------
# Global state
# -------------------------
sock = None
username = None
server_function = None
server_function_generator = None
nb_round = None
current_x = 0.0
steps_left = 10
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

        tk.Button(root, text="Connexion", command=self.connect).grid(row=3, column=0, columnspan=2)

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

        self.turtle_img = tk.PhotoImage(file="src/assets/tortue.png")

        self.water_img = tk.PhotoImage(file="src/assets/water.png")
        self.sand_img = tk.PhotoImage(file="src/assets/beach.png")

        self.canvas = tk.Canvas(root, width=self.c_width, height=self.c_height, bg="white")
        self.canvas.pack()

        self.info_label = tk.Label(root, text="Pas restants: 10")
        self.info_label.pack()

        self.info_step = tk.Label(root, text="Taille de pas: 1")
        self.info_step.pack()

        control_frame = tk.Frame(root)
        control_frame.pack()

        self.dir_var = tk.IntVar(value=0)

        tk.Radiobutton(control_frame, text="←", variable=self.dir_var, value=-1, indicatoron=False, 
            width=4, command=lambda: self.set_dir(-1)).grid(row=0, column=0)

        tk.Radiobutton(control_frame, text="→", variable=self.dir_var, value=1, indicatoron=False, 
            width=4, command=lambda: self.set_dir(1)).grid(row=0, column=1)

        tk.Button(control_frame, text="- Pas", command=self.decrease_step).grid(row=1, column=0)
        tk.Button(control_frame, text="+ Pas", command=self.increase_step).grid(row=1, column=1)
        tk.Button(control_frame, text="Faire pas", command=self.make_step).grid(row=1, column=2)

        tk.Button(root, text="Rejoindre une partie", command=self.join_game).pack()

        self.reveal_radius = 0.5   # domain units revealed around turtle
        self.explored_ranges = [] # list of (x_min, x_max)

    def join_game(self):
        send("GAME")
        reply = receive()

        if reply == "GAME ok":
            threading.Thread(target=self.wait_for_start, daemon=True).start()
        else:
            messagebox.showinfo("Info", "Partie indisponible")

    def wait_for_start(self):
        global nb_round, server_function_generator
        msg = receive()

        print(f"Game start message is {msg}")

        if msg.startswith("GAME start"):
            # Parsing
            split_msg = msg.split()
            nb_round = int(split_msg[2])        
            dim = int(split_msg[3])      
            difficulty_str = split_msg[4].split(".")[1]   
            difficulty = Difficulty[difficulty_str] 
            domain_str = " ".join(split_msg[5:]).strip()  
            domain = tuple(float(x.strip()) for x in domain_str.strip("()").split(","))
            server_function_generator = FunctionGenerator(dim, difficulty=difficulty, domain=domain)
            threading.Thread(target=self.wait_for_func, daemon=True).start()
        else:
            print("ERROR while waiting for game to start")

    def wait_for_func(self):
        global server_function
        msg = receive()
        if msg.startswith("FUNC"):
            seed = int(msg.split()[1])
            server_function = server_function_generator.generate(seed)
            self.draw_region()
            global steps_left
            steps_left = 10
            self.explored_ranges = []
            self.reveal_at(current_x)
            self.draw_region()
            self.info_label.config(text=f"Pas restants: {steps_left}")

    def reveal_at(self, x):
        min_x, max_x = server_function_generator._domain

        a = max(x - self.reveal_radius, min_x)
        b = min(x + self.reveal_radius, max_x)

        self.explored_ranges.append((a, b))
        self.explored_ranges = self.merge_ranges(self.explored_ranges)

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

        # Water (top)
        # self.canvas.create_image(
        #     0, 0,
        #     anchor="nw",
        #     image=self.water_img
        # )

        # Sand (bottom)
        self.canvas.create_image(
            0,
            self.c_height - self.sand_img.height(),
            anchor="nw",
            image=self.sand_img
        )

        min_x, max_x = server_function_generator._domain
        domain_width = max_x - min_x

        scale_x = self.c_width / domain_width
        scale_y = 20
        mid_y = self.c_height // 2

        # Draw explored segments only
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

        # X axis
        self.canvas.create_line(
            0, mid_y,
            self.c_width, mid_y,
            fill="black",
            dash=(4, 2)
        )

        # Y axis at domain center
        min_x, max_x = server_function_generator._domain
        zero_x = int((-min_x) / (max_x - min_x) * self.c_width)

        self.canvas.create_line(
            zero_x, 0,
            zero_x, self.c_height,
            fill="black",
            dash=(4, 2)
        )

        # Draw turtle
        turtle_x = int((current_x - min_x) * scale_x)
        turtle_y = mid_y - server_function.evaluate(current_x) * scale_y

        self.canvas.create_oval(
            turtle_x - 5, turtle_y - 5,
            turtle_x + 5, turtle_y + 5,
            fill="red"
        )

    def set_dir(self, d):
        global direction
        direction = d

    def increase_step(self):
        global step_size
        step_size = round(step_size + 0.1, ndigits=1)
        self.info_step.config(text=f"Taille de pas: {step_size}")

    def decrease_step(self):
        global step_size
        step_size = round(max(step_size - 0.1, 0), ndigits=1)
        self.info_step.config(text=f"Taille de pas: {step_size}")

    def make_step(self):
        global current_x, steps_left

        if steps_left <= 0:
            return

        new_x = current_x + direction * step_size

        # Clamp to domain
        min_x, max_x = server_function_generator._domain
        current_x = max(min(new_x, max_x), min_x)
        self.reveal_at(current_x)
        self.draw_region()

        steps_left -= 1
        self.info_label.config(text=f"Pas restants: {steps_left}")
        self.draw_region()

        if steps_left == 0:
            score = server_function.evaluate(current_x)
            send(f"SCORE {score}")

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