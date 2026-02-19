# direct_search_for_turtles

**Mettez les tortues à l'abri grâce à la recherche directe** — a competitive multiplayer optimization game for 3rd-year students. Players explore a hidden mathematical landscape by moving a turtle, trying to find the minimum value of an unknown function in as few steps as possible.

---

## How the game works

1. A **Game Master** configures and starts a session from the server interface.
2. All connected players receive a function seed and begin exploring a hidden landscape by moving their turtle with the arrow keys.
3. Each move costs one step. The function value is only revealed within a configurable radius around the turtle.
4. When all steps are used, each player's score (the lowest function value found) is sent to the server.
5. The server ranks players, reveals the full landscape and all final positions, and advances to the next round.
6. The player with the most ranking points across all rounds wins.

The game supports both **1D** (curve) and **2D** (heatmap) function landscapes.

---

## Requirements

- Python 3.x
- numpy >= 1.19.0
- scipy
- Pillow
- matplotlib

```bash
pip install -r requirements.txt
```

---

## Running the game

### 1. Start the server (Game Master)

```bash
python src/server/main_server.py <port> [max_connections]
```

Example:
```bash
python src/server/main_server.py 5000 20
```

This opens the **Game Master GUI**, where you can:
- Set the number of rounds, function dimension (1D or 2D), difficulty, steps per round, and reveal radius
- See connected players in real time
- Start the game, advance rounds, or force-finish a round early

### 2. Connect as a player (Client)

```bash
python src/client/main_client.py
```

Enter your username, the server address, and port. Once connected, click **Join Game** to enter the next round.

**Controls in-game:**
- `←` / `→` — move the turtle (1D mode)
- `←` / `→` / `↑` / `↓` — move the turtle (2D mode)
- `+` / `- Pas` buttons — increase or decrease step size

---

## Project structure

```
direct_search_for_turtles/
├── requirements.txt
├── turtle_curve_app.py          # Standalone interactive demo (no server needed)
│
└── src/
    ├── client/
    │   └── main_client.py       # Player GUI (Tkinter)
    │
    ├── server/
    │   ├── main_server.py       # Server entry point
    │   ├── game.py              # Game state and round management
    │   ├── game_master.py       # Game Master GUI
    │   ├── client_handler.py    # Per-connection message handling
    │   ├── leaderboard.py       # Scoring and ranking logic
    │   └── leaderboard_display.py
    │
    ├── shared/
    │   └── function_generator_claude.py  # Hidden function generator (used by both sides)
    │
    ├── assets/                  # Turtle sprite and background textures
    └── protocole.md             # Client–server message protocol specification
```

---

## Function generator

Functions are reproducible, seed-based landscapes built from three components:

1. **Even-degree polynomial** — constructed from random roots inside the domain, ensuring the function rises at the boundaries so the global minimum is always in the interior.
2. **Sinusoidal noise** — cosine terms with varying frequency, amplitude, and phase that add oscillations to the surface.
3. **Gaussian bumps** — localized hills and pits that create deceptive local minima.

### Difficulty levels

| Level  | Effect |
|--------|--------|
| Easy   | Smooth landscape, few local minima |
| Medium | Moderate oscillations, some local minima |
| Hard   | Highly deceptive landscape with many local minima |

### Python API

```python
from shared.function_generator_claude import HiddenFunction, Difficulty

hf = HiddenFunction(seed=42, difficulty=Difficulty.HARD)
hf.evaluate(0.0)   # returns the function value at x=0.0
hf.eval_count      # number of evaluations so far
hf.true_minimum    # {'x': ..., 'y': ...}
hf.reset()         # clear tracking state for a new player
```

### CLI visualization

```bash
# Plot an easy function with the true minimum marked
python function_generator_claude.py --seed 5 --difficulty easy --show-minimum

# Plot a hard function
python function_generator_claude.py --seed 5 --difficulty hard
```

---

## Standalone demo

To try the turtle movement without a server:

```bash
python turtle_curve_app.py
```

Use `←` / `→` to move the turtle along a random polynomial curve.

---

## Communication protocol

A summary of the client–server message format (see [`src/protocole.md`](src/protocole.md) for full details):

| Direction | Message | Description |
|-----------|---------|-------------|
| C → S | `USERNAME <name>` | Register a username |
| S → C | `USERNAME ok / taken` | Username acceptance |
| C → S | `GAME` | Request to join next round |
| S → C | `GAME start <rounds> <dim> <difficulty> <steps> <radius> <domain>` | Round parameters |
| S → C | `FUNC <seed>` | Function seed for this round |
| C → S | `SCORE <value> [position]` | Player's final score |
| S → C | `SCORE <rank> <points>` | Server confirms ranking |
| S → C | `REVEAL <player\|pos\|score> ...` | End-of-round reveal |
| S → C | `GAME over` | Game ended |
