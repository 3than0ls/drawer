from interactions import COLORS
from math import sqrt
from PIL import Image
import timeit
import time
import os
import random


def classify_color(rgb, new_colors, refresh=False, _cache={}, _all_colors={}):
    global COLORS
    if refresh:
        _cache.clear()
        _all_colors.clear()
        return


    # create and cache a dictionary that contains all colors so we can search through i
    if not _all_colors:
        _all_colors.update(COLORS)
        for color_pallete in new_colors:
            _all_colors.update(color_pallete)

    if rgb in _cache:
        return _cache[rgb] # to optimize
    else:
        # colors likely contain an alpha value we do not care about
        r, g, b, *_ = rgb
        color_diffs = []
        for color_name, rgba in _all_colors.items():
            color_r, color_g, color_b, _ = rgba
            # use euclidian distance to find the color difference
            color_diff = sqrt(abs(r - color_r)**2 +
                                abs(g - color_g)**2 + abs(b - color_b)**2)
            color_diffs.append((color_diff, color_name))
        closest_color = min(color_diffs)[1]
        color_pallete_number = 0
        if closest_color in COLORS:
            # the closest color is in the default COLORS, so it doesn't matter what color pallete number we assign it to.
            # we'll just add it to the index of thevery last color pallete
            color_pallete_number = len(new_colors) - 1
        else:
            for number, color_pallete in enumerate(new_colors):
                if closest_color in color_pallete:
                    color_pallete_number = number
        _cache[rgb] = (closest_color, color_pallete_number)
        return (closest_color, color_pallete_number)

# obsolete
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

# obsolete
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


def draw_directions(image_basename, new_colors):
    """
    A sort of combination of the above two methods to truly get the fastest results. 
    It essentially provides the drawer with instructions on where to start and how far to drag down
    The return value is a list with each index associated with an index in new_colors, which is a different color pallete
    Each list value is a dictionary, with a key of the color name equal to a list of directions for that color
    ex: (let's say that red is part of the first new_colors pallete and blue is part of the second)
    [
        {
            'red': [(0, 0, 50)] # select red from color pallete one, start at 0, 0, and then draw 50 down
        },
        # iterate to next dictionary, and so update color pallete
        {
            'blue': [(1, 0, 50)] # select blue from color pallete two, start at 1, 0, and then draw 50 down
        },
    ]
    """
    # print('calculating directions for {}'.format(image_basename))
    classify_color(None, None, refresh=True)
    directions = [{} for color_pallete in range(len(new_colors))]
    with Image.open(os.path.join('temp', image_basename)) as image:
        width, height = image.size
        pixel = image.load()
        for x in range(width):
            current_line_height = 0
            current_color = None
            current_clr_pallete_number = None
            origin = (x, 0)
            for y in range(height):
                px_color, clr_pallete_number = classify_color(pixel[x, y], new_colors)
                if current_color is None:
                    current_color = px_color
                    current_clr_pallete_number = clr_pallete_number

                if px_color not in directions[clr_pallete_number]:
                    directions[clr_pallete_number][px_color] = []

                if px_color != current_color:
                    directions[current_clr_pallete_number][current_color].append((origin[0], origin[1], current_line_height))
                    origin = (x, y)
                    current_line_height = 1
                    current_clr_pallete_number = clr_pallete_number 
                    current_color = px_color
                else:
                    current_line_height += 1
            directions[current_clr_pallete_number][current_color].append((origin[0], origin[1], current_line_height))
        return directions

