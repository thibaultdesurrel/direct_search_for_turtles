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
    dim : int
        Spatial dimension (1 or 2).
    difficulty : Difficulty
        Controls complexity of the generated landscape.
    domain : tuple[float, float]
        The (min, max) interval on which the function is defined (same for each axis).
    """

    def __init__(self, seed, dim=1, difficulty=Difficulty.MEDIUM, domain=(-6, 6)):
        self.seed = seed
        self.dim = dim
        self._difficulty = difficulty
        self._domain = domain

        rng = np.random.default_rng(seed)
        if dim == 1:
            self._poly_coeffs, self._noise_terms, self._bumps = self._build(rng)
        else:
            self._poly_coeffs_x, self._poly_coeffs_y, self._noise_terms, self._bumps = self._build_2d(rng)
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

    def _build_2d(self, rng):
        cfg = DIFFICULTY_CONFIGS[self._difficulty]
        lo, hi = self._domain

        # Two independent 1D polynomials: p_x(x) + p_y(y) forms the base
        degree_lo, degree_hi = cfg["degree_range"]
        possible_degrees = list(range(degree_lo, degree_hi + 1, 2))

        poly_coeffs_list = []
        for _ in range(2):
            degree = rng.choice(possible_degrees)
            roots = rng.uniform(lo, hi, degree)
            coeffs = np.poly(roots)
            xs = np.linspace(lo, hi, 1000)
            ys = np.polyval(coeffs, xs)
            value_range = ys.max() - ys.min()
            if value_range > 0:
                coeffs = coeffs * (10.0 / value_range)
            coeffs = coeffs / cfg["poly_scale"]
            poly_coeffs_list.append(coeffs)

        poly_coeffs_x, poly_coeffs_y = poly_coeffs_list

        # 2D sinusoidal noise: amp * cos(freq_x * x + phase_x) * cos(freq_y * y + phase_y)
        # Product form creates an egg-carton pattern with well-defined local minima
        n_noise = rng.integers(
            cfg["noise_count_range"][0], cfg["noise_count_range"][1] + 1
        )
        noise_terms = []
        for _ in range(n_noise):
            amp = rng.uniform(*cfg["noise_amplitude_range"])
            freq_x = rng.uniform(
                cfg["noise_frequency_range"][0], cfg["noise_frequency_range"][1]
            )
            freq_y = rng.uniform(
                cfg["noise_frequency_range"][0], cfg["noise_frequency_range"][1]
            )
            phase_x = rng.uniform(0, 2 * np.pi)
            phase_y = rng.uniform(0, 2 * np.pi)
            noise_terms.append((amp, freq_x, freq_y, phase_x, phase_y))

        # 2D Gaussian bumps
        n_bumps = rng.integers(
            cfg["bump_count_range"][0], cfg["bump_count_range"][1] + 1
        )
        bumps = []
        for _ in range(n_bumps):
            amp = rng.uniform(*cfg["bump_amplitude_range"])
            sign = rng.choice([-1, 1])
            center_x = rng.uniform(lo, hi)
            center_y = rng.uniform(lo, hi)
            width = rng.uniform(0.3, 1.5)
            bumps.append((sign * amp, center_x, center_y, width))

        return poly_coeffs_x, poly_coeffs_y, noise_terms, bumps

    def _raw_eval(self, x):
        """Evaluate the function without tracking.

        For dim=1, x is a scalar (or 1-D array).
        For dim=2, x is a tuple/list/array of (x1, x2), or two arrays for vectorised calls.
        """
        if self.dim == 1:
            y = np.polyval(self._poly_coeffs, x)
            for amp, freq, phase in self._noise_terms:
                y = y + amp * np.cos(freq * x + phase)
            for amp, center, width in self._bumps:
                y = y + amp * np.exp(-((x - center) ** 2) / (2 * width**2))
            return y
        else:
            return self._raw_eval_2d(x)

    def _raw_eval_2d(self, pos):
        """Evaluate the 2D function.

        pos can be:
        - A tuple/list/array of two scalars (x, y)
        - A tuple/list of two arrays (xs, ys) for vectorised evaluation
        """
        x, y = pos[0], pos[1]
        z = np.polyval(self._poly_coeffs_x, x) + np.polyval(self._poly_coeffs_y, y)
        for amp, freq_x, freq_y, phase_x, phase_y in self._noise_terms:
            z = z + amp * np.cos(freq_x * x + phase_x) * np.cos(freq_y * y + phase_y)
        for amp, cx, cy, width in self._bumps:
            z = z + amp * np.exp(-(((x - cx) ** 2) + ((y - cy) ** 2)) / (2 * width**2))
        return z

    def _compute_true_minimum(self):
        lo, hi = self._domain

        if self.dim == 1:
            from scipy.optimize import minimize_scalar

            xs = np.linspace(lo, hi, 10_000)
            ys = self._raw_eval(xs)

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
        else:
            from scipy.optimize import minimize

            n_grid = 200
            xs = np.linspace(lo, hi, n_grid)
            ys = np.linspace(lo, hi, n_grid)
            X, Y = np.meshgrid(xs, ys)
            Z = self._raw_eval((X, Y))

            # Find top-20 grid candidates and refine
            flat = Z.ravel()
            top_indices = np.argsort(flat)[:20]
            best_pos = None
            best_val = np.inf
            for idx in top_indices:
                r, c = divmod(idx, n_grid)
                x0 = [X[r, c], Y[r, c]]
                result = minimize(
                    lambda p: float(self._raw_eval((p[0], p[1]))),
                    x0,
                    bounds=[(lo, hi), (lo, hi)],
                    method="L-BFGS-B",
                )
                if result.fun < best_val:
                    best_pos = result.x
                    best_val = result.fun

            return {"x": (float(best_pos[0]), float(best_pos[1])), "y": float(best_val)}

    # -- public API ---------------------------------------------------------

    def evaluate(self, x):
        """Evaluate the function at *x*.

        Parameters
        ----------
        x : float or tuple[float, float]
            For dim=1: a scalar within the domain.
            For dim=2: a tuple (x1, x2), both within the domain.

        Returns
        -------
        float
        """
        lo, hi = self._domain
        if self.dim == 1:
            if x < lo or x > hi:
                raise ValueError(f"x={x} is outside the domain [{lo}, {hi}]")
        else:
            x1, x2 = x
            if x1 < lo or x1 > hi or x2 < lo or x2 > hi:
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

        if self.dim == 1:
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
        else:
            n = 500
            xs = np.linspace(lo, hi, n)
            ys = np.linspace(lo, hi, n)
            X, Y = np.meshgrid(xs, ys)
            Z = self._raw_eval((X, Y))

            fig, axes = plt.subplots(1, 2, figsize=(16, 6))

            # Contour plot
            ax = axes[0]
            cf = ax.contourf(X, Y, Z, levels=40, cmap="viridis")
            ax.contour(X, Y, Z, levels=40, colors="k", linewidths=0.3, alpha=0.4)
            plt.colorbar(cf, ax=ax)
            if show_minimum:
                m = self._true_minimum
                ax.plot(m["x"][0], m["x"][1], "r*", markersize=14, label="True minimum")
                ax.legend()
            ax.set_title(
                f"HiddenFunction  seed={self.seed}  "
                f"difficulty={self._difficulty.value}"
            )
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_aspect("equal")

            # 3D surface
            ax3d = fig.add_subplot(1, 2, 2, projection="3d")
            ax3d.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8,
                              rstride=5, cstride=5, linewidth=0.1)
            if show_minimum:
                m = self._true_minimum
                ax3d.scatter(m["x"][0], m["x"][1], m["y"],
                             color="red", s=100, marker="*", zorder=10)
            ax3d.set_xlabel("x")
            ax3d.set_ylabel("y")
            ax3d.set_zlabel("f(x, y)")

            axes[1].set_visible(False)  # hide the unused 2D axis
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
            seed=seed, dim=self.dim, difficulty=self._difficulty, domain=self._domain
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
    parser.add_argument(
        "--dim",
        type=int,
        default=1,
        choices=[1, 2],
        help="Spatial dimension (default: 1)",
    )

    args = parser.parse_args()
    difficulty = Difficulty(args.difficulty)
    hf = HiddenFunction(seed=args.seed, dim=args.dim, difficulty=difficulty)
    print(f"Generated function  seed={args.seed}  dim={args.dim}  difficulty={args.difficulty}")
    if args.dim == 1:
        print(
            f"True minimum: x={hf.true_minimum['x']:.6f}, "
            f"y={hf.true_minimum['y']:.6f}"
        )
    else:
        m = hf.true_minimum
        print(
            f"True minimum: (x, y)=({m['x'][0]:.6f}, {m['x'][1]:.6f}), "
            f"f={m['y']:.6f}"
        )
    hf.plot(show_minimum=args.show_minimum)
