"""Function generator for the direct-search-for-turtles optimization game.

Generates reproducible, seed-based objective functions with configurable
difficulty. Each function is a polynomial with sinusoidal noise and Gaussian
bumps, creating landscapes with varying numbers of local minima.
"""

from enum import Enum

import numpy as np


# ---------------------------------------------------------------------------
# Difficulty configuration
# ---------------------------------------------------------------------------


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


DIFFICULTY_CONFIGS = {
    Difficulty.EASY: {
        "degree_range": (2, 4),
        "poly_scale": 1.0,
        "noise_count_range": (1, 1),
        "noise_amplitude_range": (0.1, 0.5),
        "noise_frequency_range": (1, 4),
        "bump_count_range": (0, 1),
        "bump_amplitude_range": (0.5, 2.0),
    },
    Difficulty.MEDIUM: {
        "degree_range": (4, 6),
        "poly_scale": 3.0,
        "noise_count_range": (1, 3),
        "noise_amplitude_range": (0.3, 1.5),
        "noise_frequency_range": (3, 10),
        "bump_count_range": (1, 3),
        "bump_amplitude_range": (1.0, 4.0),
    },
    Difficulty.HARD: {
        "degree_range": (4, 6),
        "poly_scale": 6.0,
        "noise_count_range": (2, 5),
        "noise_amplitude_range": (0.5, 2.5),
        "noise_frequency_range": (5, 15),
        "bump_count_range": (3, 7),
        "bump_amplitude_range": (2.0, 6.0),
    },
}


# ---------------------------------------------------------------------------
# HiddenFunction
# ---------------------------------------------------------------------------


class HiddenFunction:
    """A black-box objective function for the optimization game.

    Parameters
    ----------
    seed : int
        Deterministic seed for reproducible function generation.
    difficulty : Difficulty
        Controls complexity of the generated landscape.
    domain : tuple[float, float]
        The (min, max) interval on which the function is defined.
    """

    def __init__(self, seed, difficulty=Difficulty.MEDIUM, domain=(-6, 6)):
        self.seed = seed
        self._difficulty = difficulty
        self._domain = domain

        rng = np.random.default_rng(seed)
        self._poly_coeffs, self._noise_terms, self._bumps = self._build(rng)
        self._true_minimum = self._compute_true_minimum()

        self.reset()

    # -- construction -------------------------------------------------------

    def _build(self, rng):
        cfg = DIFFICULTY_CONFIGS[self._difficulty]
        lo, hi = self._domain

        # Even-degree polynomial from random roots
        degree_lo, degree_hi = cfg["degree_range"]
        # Pick an even degree in [degree_lo, degree_hi]
        possible_degrees = list(range(degree_lo, degree_hi + 1, 2))
        degree = rng.choice(possible_degrees)
        roots = rng.uniform(lo, hi, degree)
        poly_coeffs = np.poly(roots)  # leading-coeff = 1, highest degree first

        # Normalize so the range over the domain is ~10, then scale down
        xs = np.linspace(lo, hi, 1000)
        ys = np.polyval(poly_coeffs, xs)
        value_range = ys.max() - ys.min()
        if value_range > 0:
            poly_coeffs = poly_coeffs * (10.0 / value_range)
        poly_coeffs = poly_coeffs / cfg["poly_scale"]

        # Sinusoidal noise terms
        n_noise = rng.integers(
            cfg["noise_count_range"][0], cfg["noise_count_range"][1] + 1
        )
        noise_terms = []
        for _ in range(n_noise):
            amp = rng.uniform(*cfg["noise_amplitude_range"])
            freq = rng.uniform(
                cfg["noise_frequency_range"][0], cfg["noise_frequency_range"][1]
            )
            phase = rng.uniform(0, 2 * np.pi)
            noise_terms.append((amp, freq, phase))

        # Gaussian bumps (negative = pit / extra local min, positive = hill)
        n_bumps = rng.integers(
            cfg["bump_count_range"][0], cfg["bump_count_range"][1] + 1
        )
        bumps = []
        for _ in range(n_bumps):
            amp = rng.uniform(*cfg["bump_amplitude_range"])
            sign = rng.choice([-1, 1])
            center = rng.uniform(lo, hi)
            width = rng.uniform(0.3, 1.5)
            bumps.append((sign * amp, center, width))

        return poly_coeffs, noise_terms, bumps

    def _raw_eval(self, x):
        """Evaluate the function without tracking."""
        y = np.polyval(self._poly_coeffs, x)
        for amp, freq, phase in self._noise_terms:
            y = y + amp * np.cos(freq * x + phase)
        for amp, center, width in self._bumps:
            y = y + amp * np.exp(-((x - center) ** 2) / (2 * width**2))
        return y

    def _compute_true_minimum(self):
        from scipy.optimize import minimize_scalar

        lo, hi = self._domain
        xs = np.linspace(lo, hi, 10_000)
        ys = self._raw_eval(xs)

        # Refine from the top-20 candidates
        best_x, best_y = xs[np.argmin(ys)], ys.min()
        top_indices = np.argsort(ys)[:20]
        for idx in top_indices:
            result = minimize_scalar(
                self._raw_eval,
                bounds=(max(lo, xs[idx] - 0.1), min(hi, xs[idx] + 0.1)),
                method="bounded",
            )
            if result.fun < best_y:
                best_x, best_y = result.x, result.fun

        return {"x": float(best_x), "y": float(best_y)}

    # -- public API ---------------------------------------------------------

    def evaluate(self, x):
        """Evaluate the function at *x*.

        Parameters
        ----------
        x : float
            Must be within the domain.

        Returns
        -------
        float
        """
        lo, hi = self._domain
        if x < lo or x > hi:
            raise ValueError(f"x={x} is outside the domain [{lo}, {hi}]")
        y = float(self._raw_eval(x))
        self._eval_count += 1
        self._history.append((x, y))
        if self._best_value is None or y < self._best_value:
            self._best_x = x
            self._best_value = y
        return y

    def reset(self):
        """Clear tracking state (for a new player)."""
        self._eval_count = 0
        self._best_x = None
        self._best_value = None
        self._history = []

    def plot(self, show_minimum=False):
        """Visualize the function (game-master view)."""
        import matplotlib.pyplot as plt

        lo, hi = self._domain
        xs = np.linspace(lo, hi, 1000)
        ys = self._raw_eval(xs)

        plt.figure(figsize=(10, 5))
        plt.plot(xs, ys, linewidth=1.5)
        if show_minimum:
            m = self._true_minimum
            plt.plot(m["x"], m["y"], "r*", markersize=14, label="True minimum")
            plt.legend()
        plt.title(
            f"HiddenFunction  seed={self.seed}  "
            f"difficulty={self._difficulty.value}"
        )
        plt.xlabel("x")
        plt.ylabel("f(x)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    # -- properties ---------------------------------------------------------

    @property
    def eval_count(self):
        return self._eval_count

    @property
    def best_x(self):
        return self._best_x

    @property
    def best_value(self):
        return self._best_value

    @property
    def true_minimum(self):
        return self._true_minimum

    @property
    def domain(self):
        return self._domain

    @property
    def history(self):
        return list(self._history)


# ---------------------------------------------------------------------------
# FunctionGenerator  (server-compatible wrapper)
# ---------------------------------------------------------------------------


class FunctionGenerator:
    """Generates :class:`HiddenFunction` instances for the game server.

    Parameters
    ----------
    dim : int
        Spatial dimension (currently only ``1`` is supported).
    difficulty : Difficulty
        Difficulty preset for generated functions.
    base_seed : int | None
        If given, used to seed the internal RNG for reproducible sequences.
    domain : tuple[float, float]
        Domain passed through to each :class:`HiddenFunction`.
    """

    def __init__(
        self, dim, difficulty=Difficulty.MEDIUM, base_seed=None, domain=(-6, 6)
    ):
        self.dim = dim
        self._difficulty = difficulty
        self._domain = domain
        self._rng = np.random.default_rng(base_seed)

    def generate(self, seed=None):
        """Return a new :class:`HiddenFunction` with a derived seed."""
        if seed is None:
            seed = int(self._rng.integers(0, 2**31))
        return HiddenFunction(
            seed=seed, difficulty=self._difficulty, domain=self._domain
        )


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate and plot a random objective function"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=5,
        help="Seed for function generation (default: 5)",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="medium",
        choices=["easy", "medium", "hard"],
        help="Difficulty level (default: medium)",
    )
    parser.add_argument(
        "--show-minimum",
        action="store_true",
        help="Mark the true minimum on the plot",
    )

    args = parser.parse_args()
    difficulty = Difficulty(args.difficulty)
    hf = HiddenFunction(seed=args.seed, difficulty=difficulty)
    print(f"Generated function  seed={args.seed}  difficulty={args.difficulty}")
    print(
        f"True minimum: x={hf.true_minimum['x']:.6f}, " f"y={hf.true_minimum['y']:.6f}"
    )
    hf.plot(show_minimum=args.show_minimum)
