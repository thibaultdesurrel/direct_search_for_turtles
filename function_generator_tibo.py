import numpy as np
import argparse
import matplotlib.pyplot as plt


def evaluate_polynomial(coefficients, x):
    """Evaluate the polynomial at a given x."""
    return sum(coef * (x**i) for i, coef in enumerate(coefficients))


def evaluate_noisy_polynomial(coefficients, x):
    """Evaluate the polynomial at a given x with added noise."""
    clean_value = evaluate_polynomial(coefficients, x)
    noise = np.cos(10 * x)  # Noise modulated by cosine
    return clean_value + noise


def generate_random_polynomial_1(seed):
    """Generate random polynomial coefficients based on random roots.

    Cool seeds: 5, 6, 7, 10 (?),

    """
    np.random.seed(seed)  # For reproducibility
    degree = 4  # Polynomial degree between 2 and 4
    roots = np.random.uniform(-6, 6, degree)  # Random roots between -5 and 5
    coefficients = np.poly(roots) / 10  # Get coefficients from roots
    return coefficients[::-1]  # Reverse to match our evaluation function's order


def plot_polynomial(coefficients, noisy=False):
    """Plot the polynomial defined by the coefficients."""
    x = np.linspace(-6, 6, 400)
    print("Noisy evaluation:" if noisy else "Clean evaluation:")
    if noisy:
        y = evaluate_noisy_polynomial(coefficients, x)
    else:
        y = evaluate_polynomial(coefficients, x)
    plt.plot(x, y)
    plt.title("Random Polynomial")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.grid()
    plt.show()


parser = argparse.ArgumentParser(description="Generate and plot a random polynomial")
parser.add_argument(
    "--seed",
    type=int,
    default=5,
    help="Seed for random number generation (default: 5)",
)

parser.add_argument(
    "--noisy",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Add noise to the polynomial evaluation (default: False)",
)

if __name__ == "__main__":
    args = parser.parse_args()
    print(f"Generating polynomial with seed {args.seed} and noisy={args.noisy}")
    coefficients = generate_random_polynomial_1(args.seed)
    plot_polynomial(coefficients, noisy=args.noisy)
