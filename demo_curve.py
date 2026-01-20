#!/usr/bin/env python3
"""
Demo script that shows the curve path without requiring user interaction.
This is useful for documentation and testing purposes.
"""

import random
import numpy as np
import matplotlib.pyplot as plt


def generate_polynomial_curve():
    """Generate a random polynomial curve similar to the main app"""
    degree = random.randint(2, 20)
    coefficients = [random.uniform(-0.001, 0.001) for _ in range(degree + 1)]

    def polynomial_function(x):
        y = 0
        for i, coef in enumerate(coefficients):
            y += coef * (x**i)
        return y

    return polynomial_function, degree, coefficients


def main():
    # Set seed for reproducibility
    random.seed(42)

    # Generate curve
    poly_func, degree, coeffs = generate_polynomial_curve()

    # Generate points
    x_values = np.linspace(-350, 350, 200)
    y_values = [poly_func(x) for x in x_values]

    # Clip y values to reasonable bounds
    y_values = np.clip(y_values, -250, 250)

    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(x_values, y_values, "b-", linewidth=2, label="Polynomial Curve")

    # Mark start position
    start_x = 0
    start_y = poly_func(start_x)
    start_y = max(min(start_y, 250), -250)
    plt.plot(start_x, start_y, "go", markersize=15, label="Turtle Start Position")

    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.title(f"Random Polynomial Curve (Degree {degree})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(-350, 350)
    plt.ylim(-250, 250)

    # Save the figure
    plt.savefig("turtle_curve_demo.png", dpi=150, bbox_inches="tight")
    print("✓ Demo curve saved to turtle_curve_demo.png")
    print(f"  Polynomial degree: {degree}")
    print(f"  Coefficients: {[f'{c:.6f}' for c in coeffs]}")

    # Also display if running interactively
    # plt.show()


if __name__ == "__main__":
    main()
