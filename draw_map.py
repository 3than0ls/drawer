from color_picker import COLORS
from math import sqrt
from PIL import Image

def classify_color(rgb):
    global COLORS
    # colors likely contain an alpha value we do not care about
    r, g, b, _ = rgb
    color_diffs = []
    for color_name, rgba in COLORS.items():
        color_r, color_g, color_b, _ = rgba
        # use euclidian distance to find the color difference
        color_diff = sqrt(abs(r - color_r)**2 +
                               abs(g - color_g)**2 + abs(b - color_b)**2)
        color_diffs.append((color_diff, color_name))
    closest_color = min(color_diffs)
    return closest_color[1]


def color_map(image):
    """
    This returns a dictionary with each defined color as a key to a list of every pixel that has that color
    Advantages: It allows less clicking in between selecting color during the drawing process, theoretically reducing time required
    ex:
    {
        'red': [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
        'blue': [(0, 2), (1, 2), (2, 2)]
    }
    """
    pixel_colors = {}
    with Image.open(image) as image:
        width, height = image.size
        pixel = image.load()
        for x in range(width):
            for y in range(height):
                closest_color = classify_color(pixel[x, y])
                if closest_color not in pixel_colors:
                    pixel_colors[closest_color] = [(x, y)]
                else:
                    pixel_colors[closest_color].append((x, y))
    return pixel_colors

def pixel_map(image):
    """
    This returns a 2d list with each every pixel assigned to a defined color
    Advantages: It allows dragging during the drawing process, theoretically reducing time required
    ex:
    [
        ['red', 'red', 'blue'],
        ['red', 'red', 'blue'],
        ['red', 'blue', 'blue'],
    ]
    """
    pixel_colors = []
    with Image.open(image) as image:
        width, height = image.size
        pixel = image.load()
        for x in range(width):
            if len(pixel_colors) < x+1:
                pixel_colors.append([])
                for y in range(height):
                    closest_color = classify_color(pixel[x, y])
                    pixel_colors[x].append(closest_color)
    return pixel_colors


def draw_directions(image):
    """
    A sort of combination of the above two methods to truly get the fastest results. 
    It essentially provides the drawer with instructions on where to start and how far to drag down
    This returns a dictionary with each defined color as a key to a list of y-coordinate line height values that should be draw vertically down
    The list contains tuples specifying the start points and the correlating indexed line height length
    ex: (x, y, line_height_length)
    unlike pixel_map, there does not have to be a value for every row.

    Advantages: Combines the two advantages of less color switching and drag-drawing
    ex:
    {
        'red': [
            (0, 0, 3), (1, 0, 2), 
        ],
        'blue': [
            (1, 2, 1), (2, 0, 3),
        ],
    }
    This should tell the drawer to select color red, start at (0, 0), and drag down 3 pixels. Then start at (1, 0) (the next given row/column), and drag down 2 pixels.
    Then move onto blue. Start at (1, 2), move down 1px, next row, start at (2, 0) (the next given row/column), and drag down 3px
    """
    directions = {}
    with Image.open(image) as image:
        width, height = image.size
        pixel = image.load()
        for x in range(width):
            current_line_height = 0
            current_color = None
            origin = (x, 0)
            for y in range(height):
                px_color = classify_color(pixel[x, y])
                if current_color is None:
                    current_color = px_color

                if px_color not in directions:
                    directions[px_color] = []

                if px_color != current_color:
                    directions[current_color].append((origin[0], origin[1], current_line_height))
                    origin = (x, y)
                    current_line_height = 1
                    current_color = px_color
                else:
                    current_line_height += 1
            directions[current_color].append((origin[0], origin[1], current_line_height))
        return directions
                    