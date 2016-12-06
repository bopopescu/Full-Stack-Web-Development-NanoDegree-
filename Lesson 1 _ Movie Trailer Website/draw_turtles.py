import turtle


def draw_square(some_turtle):
    for i in range(1, 5):
        some_turtle.forward(100)
        some_turtle.right(90)

def draw_triangle(some_turtle):
    for i in range (1,4):
        some_turtle.forward(100)
        some_turtle.right(120)

def draw_circle_square(some_turtle):
    for i in range (1,37):
        draw_square(some_turtle)
        some_turtle.right(10)

def draw_flower_triangle(some_turtle):
    for i in range (1,37):
        draw_triangle(some_turtle)
        some_turtle.right(10)
    some_turtle.right(200)


def draw_art():
    window = turtle.Screen()
    window.bgcolor("red")
    # Window settings
    brad = turtle.Turtle()
    brad.shape("turtle")
    brad.color("yellow")
    brad.speed(2)
    draw_circle_square(brad)
    draw_square(brad)
    # Brad drawing square
    angie = turtle.Turtle()
    angie.shape("arrow")
    angie.color("blue")
    angie.circle(100)
    # Andie drawing circle
    peter = turtle.Turtle()
    peter.shape("square")
    peter.color("green")
    draw_flower_triangle(peter)
    draw_triangle(peter)
    # Peter drawing triangle
    window.exitonclick()
    # Window exit


draw_art(some_turtle)
