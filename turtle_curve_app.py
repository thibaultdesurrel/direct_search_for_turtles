#!/usr/bin/env python3
"""
Interactive Turtle Curve Application
Move a turtle along a random polynomial curve using arrow keys
"""

import turtle
import random
import numpy as np


class TurtleCurveApp:
    def __init__(self):
        # Setup the screen
        self.screen = turtle.Screen()
        self.screen.title("Turtle on a Polynomial Curve")
        self.screen.setup(width=800, height=600)
        self.screen.bgcolor("white")
        
        # Create the turtle
        self.turtle_obj = turtle.Turtle()
        self.turtle_obj.shape("turtle")
        self.turtle_obj.color("green")
        self.turtle_obj.penup()
        
        # Create a turtle for drawing the curve
        self.curve_drawer = turtle.Turtle()
        self.curve_drawer.hideturtle()
        self.curve_drawer.speed(0)
        self.curve_drawer.color("blue")
        
        # Generate random polynomial coefficients
        self.degree = random.randint(2, 4)  # Polynomial degree between 2 and 4
        self.coefficients = [random.uniform(-0.001, 0.001) for _ in range(self.degree + 1)]
        
        # Position tracking
        self.x_position = 0.0
        self.step_size = 10.0
        self.min_x = -350
        self.max_x = 350
        
        # Draw the curve
        self.draw_curve()
        
        # Position turtle at starting point
        self.update_turtle_position()
        
        # Setup keyboard bindings
        self.screen.listen()
        self.screen.onkey(self.move_left, "Left")
        self.screen.onkey(self.move_right, "Right")
        
        # Display instructions
        self.show_instructions()
    
    def polynomial_function(self, x):
        """Calculate y value for given x using polynomial coefficients"""
        y = 0
        for i, coef in enumerate(self.coefficients):
            y += coef * (x ** i)
        return y
    
    def draw_curve(self):
        """Draw the polynomial curve on the screen"""
        self.curve_drawer.penup()
        
        # Draw the curve
        x_values = range(self.min_x, self.max_x + 1, 5)
        first_point = True
        
        for x in x_values:
            y = self.polynomial_function(x)
            # Keep y within screen bounds
            y = max(min(y, 250), -250)
            
            if first_point:
                self.curve_drawer.goto(x, y)
                self.curve_drawer.pendown()
                first_point = False
            else:
                self.curve_drawer.goto(x, y)
    
    def update_turtle_position(self):
        """Update turtle position based on current x_position"""
        y = self.polynomial_function(self.x_position)
        # Keep y within screen bounds
        y = max(min(y, 250), -250)
        self.turtle_obj.goto(self.x_position, y)
        
        # Update the turtle's heading to follow the curve
        # Calculate slope at current position
        delta_x = 1.0
        y1 = self.polynomial_function(self.x_position)
        y2 = self.polynomial_function(self.x_position + delta_x)
        slope = (y2 - y1) / delta_x
        
        # Convert slope to angle
        angle = np.degrees(np.arctan(slope))
        self.turtle_obj.setheading(angle)
    
    def move_left(self):
        """Move turtle to the left along the curve"""
        if self.x_position > self.min_x:
            self.x_position -= self.step_size
            self.update_turtle_position()
    
    def move_right(self):
        """Move turtle to the right along the curve"""
        if self.x_position < self.max_x:
            self.x_position += self.step_size
            self.update_turtle_position()
    
    def show_instructions(self):
        """Display instructions on screen"""
        instructions = turtle.Turtle()
        instructions.hideturtle()
        instructions.penup()
        instructions.goto(0, 270)
        instructions.write(
            "Use LEFT and RIGHT arrow keys to move the turtle",
            align="center",
            font=("Arial", 12, "normal")
        )
    
    def run(self):
        """Start the application main loop"""
        self.screen.mainloop()


def main():
    """Main entry point for the application"""
    app = TurtleCurveApp()
    app.run()


if __name__ == "__main__":
    main()
