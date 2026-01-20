#!/usr/bin/env python3
"""
Test script for turtle_curve_app.py
Tests the polynomial function and basic functionality
"""

import sys
import random

# Set seed for reproducibility
random.seed(42)

# Mock turtle module to test without GUI
class MockTurtle:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.heading_val = 0
    
    def shape(self, s): pass
    def color(self, c): pass
    def penup(self): pass
    def pendown(self): pass
    def goto(self, x, y):
        self.x = x
        self.y = y
    def setheading(self, angle):
        self.heading_val = angle
    def hideturtle(self): pass
    def speed(self, s): pass
    def write(self, *args, **kwargs): pass

class MockScreen:
    def __init__(self):
        pass
    def title(self, t): pass
    def setup(self, **kwargs): pass
    def bgcolor(self, c): pass
    def listen(self): pass
    def onkey(self, func, key): pass
    def mainloop(self): pass

sys.modules['turtle'] = type(sys)('turtle')
sys.modules['turtle'].Turtle = MockTurtle
sys.modules['turtle'].Screen = MockScreen

# Now import our app
from turtle_curve_app import TurtleCurveApp

def test_polynomial_function():
    """Test that polynomial function works"""
    app = TurtleCurveApp()
    
    # Test polynomial evaluation
    y = app.polynomial_function(0)
    print(f"✓ Polynomial at x=0: y={y:.4f}")
    
    y = app.polynomial_function(100)
    print(f"✓ Polynomial at x=100: y={y:.4f}")
    
    # Test that coefficients are generated
    assert len(app.coefficients) > 0, "Coefficients should be generated"
    print(f"✓ Generated {len(app.coefficients)} coefficients for degree {app.degree} polynomial")
    
    return True

def test_turtle_movement():
    """Test turtle movement logic"""
    app = TurtleCurveApp()
    
    # Store initial position
    initial_x = app.x_position
    print(f"✓ Initial position: x={initial_x}")
    
    # Test move right
    app.move_right()
    assert app.x_position == initial_x + app.step_size, "Turtle should move right"
    print(f"✓ After move_right: x={app.x_position}")
    
    # Test move left
    app.move_left()
    assert app.x_position == initial_x, "Turtle should move back to initial position"
    print(f"✓ After move_left: x={app.x_position}")
    
    # Test boundary conditions
    app.x_position = app.min_x
    app.move_left()
    assert app.x_position == app.min_x, "Turtle should not move past min_x"
    print(f"✓ Boundary check (left): x={app.x_position}")
    
    app.x_position = app.max_x
    app.move_right()
    assert app.x_position == app.max_x, "Turtle should not move past max_x"
    print(f"✓ Boundary check (right): x={app.x_position}")
    
    return True

def main():
    print("Testing Turtle Curve Application...")
    print("=" * 50)
    
    try:
        test_polynomial_function()
        print()
        test_turtle_movement()
        print()
        print("=" * 50)
        print("✓ All tests passed!")
        return 0
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
