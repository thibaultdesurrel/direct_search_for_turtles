# direct_search_for_turtles
Repo pour le code pour notre projet pour les 3èmes "Mettez les tortues à l'abri grâce à la recherche directe"

## Interactive Turtle Curve Application

This application allows you to move a turtle along a random polynomial curve using arrow keys.

### Requirements

- Python 3.x
- numpy
- scipy

### Installation

```bash
pip install -r requirements.txt
```

### Usage

Run the application:

```bash
python turtle_curve_app.py
```

Use the **LEFT** and **RIGHT** arrow keys to move the turtle along the curve.

### Features

- Random polynomial curve (degree 2-4) generated each time the app runs
- Smooth turtle movement along the curve
- Turtle orientation follows the curve's tangent

## Function Generator

`function_generator.py` generates the objective functions that players try to minimize during the game. Each function is a reproducible, seed-based landscape built from three components:

1. **Even-degree polynomial** — constructed from random roots within the domain, ensuring the function rises at the boundaries so the minimum is always in the interior.
2. **Sinusoidal noise** — multiple cosine terms with varying frequency, amplitude, and phase that add oscillations to the surface.
3. **Gaussian bumps** — localized hills and pits that create additional local minima to confuse naive search strategies.

### Difficulty levels

The generator supports three difficulty levels (`easy`, `medium`, `hard`) that control the number and intensity of these components. Higher difficulty flattens the base polynomial (via a scale divisor), making noise and bumps relatively more dominant and producing a more deceptive landscape with many local minima.

### Classes

- **`HiddenFunction(seed, difficulty, domain)`** — the core black-box function. Exposes `evaluate(x)` for single-point queries (with domain validation and tracking), `reset()` to clear player state, `plot()` for game-master visualization, and properties like `eval_count`, `best_x`, `best_value`, `true_minimum`, and `history`.
- **`FunctionGenerator(dim, difficulty, base_seed, domain)`** — server-compatible wrapper. Calling `generate()` returns a new `HiddenFunction` with a derived seed, matching the interface used by the game server.

### CLI usage

```bash
# Plot an easy function with the true minimum marked
python function_generator.py --seed 5 --difficulty easy --show-minimum

# Plot a hard function
python function_generator.py --seed 5 --difficulty hard
```

### Python usage

```python
from function_generator import HiddenFunction, Difficulty

hf = HiddenFunction(seed=42, difficulty=Difficulty.HARD)
hf.evaluate(0.0)    # returns a float
hf.eval_count        # 1
hf.true_minimum      # {'x': ..., 'y': ...}
hf.reset()           # clear tracking for a new player
```
