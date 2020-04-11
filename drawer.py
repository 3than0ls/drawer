import os
import sys
import subprocess
import threading
import time
import pyautogui
import keyboard
import timeit
import multiprocessing
from PIL import Image
from color_picker import select_color, COLORS, expand_colors, color_locations, add_colors
from draw_map import color_map, pixel_map, draw_directions
screen_width, screen_height = pyautogui.size()

pyautogui.PAUSE = 0.000001

running = True


def stop_running():
    global running
    running = False
    exit()


def open_paint():
    # paint must be fullscreened for the program to be correctly calibrated (/max)
    subprocess.call(['cmd', '/c', 'start', '/max',
                     'C:\\Windows\System32\mspaint.exe'])


canvas_box, canvas_x, canvas_y = [None] * 3

# drag_draw evolved into color_map_draw, which evolved into pixel_map_draw, and color_map_draw and pixel_map_draw kinda evolved/fused to make combined_map_draw
# obsolete
def drag_draw():
    """precursor to what comes below"""
    # first, locate the canvas of the paint application window
    canvas_center = pyautogui.locateCenterOnScreen(
        'images/canvas.png', region=(0, 0, screen_width, screen_height))
    if (canvas_center):
        # begin drawing
        pyautogui.moveTo(canvas_center[0], canvas_center[1], 1)
        directions = (
            (200, 200, "red"),
            (-200, 0, "green"),
            (0, -200, "blue"),
            (-200, -200, "red"),
            (200, 0, "green"),
            (0, 200, "blue"),
        )
        for direction in directions:
            if (direction[2]):
                select_color(direction[2])
            pyautogui.drag(direction[0], direction[1], 3)
    else:
        print('mspaint canvas not found')

# obsolete
def color_map_draw(image):
    global canvas_x, canvas_y
    """
    The simpler way, where we iterate through every color and click on every spot that that color is located on
    """
    color_map_dict = color_map(image)
    for color, locations in color_map_dict.items():
        select_color(color)
        for location in locations:
            if running:
                pyautogui.click(canvas_x + location[0], canvas_y + location[1])
            else:
                return

# obsolete
def pixel_map_draw(image):
    global canvas_x, canvas_y
    """
    The more difficult, hair-pulling, oh god why did i stay up until 2am writing this way, where we drag rather than click, and the rest is explained below
    """
    pixel_map_list = pixel_map(image)
    current_row_color = None
    for x in range(len(pixel_map_list)): # column selector
        if len(set(pixel_map_list[x])) <= 1: # if the entire row is one color, take this simpler process
            for y in range(len(pixel_map_list[x])):
                if pixel_map_list[x][y] != current_row_color:
                    current_row_color = pixel_map_list[x][y]
                    select_color(current_row_color)
                if running:
                    if len(set(pixel_map_list[x])) <= 1: # if the entire row is one color
                        pyautogui.moveTo(canvas_x + x, canvas_y)
                        pyautogui.dragTo(canvas_x + x, canvas_y + len(pixel_map_list[x]) + 1)
                        break
                else:
                    return
        else: # otherwise go through this process
            """
            How it works:
            A color_lengths dictionary keeps track of the length of the pixel column that matches a certain color. Let's suppose that there is a column of 200 blue pixels
            When a new color is seen, it is added to the color_lengths dictionary, and the old value is drawn by dragging down the length that was recorded
            Let's suppose after the 200 blue pixels there is a 200 pixel column of orange. The blue column is then drawn by dragging.
            The length is then reset in case blue is run into again after this new orange column.
            After the column ends, (let's suppose it is a 400px column split into 200 blue px and 200 orange px), it draw-drags the orange column and then increases the row
            """
            color_lengths = {}
            total_length = 0
            current_color = None
            for color in pixel_map_list[x]:
                if current_color is None:
                    current_color = color
                    select_color(current_color)
                if color not in color_lengths:  # if the color does not exist, create it. This is different from below because the color may already exist in the dict
                    color_lengths[color] = 1

                if color != current_color:  # if a new color is encountered
                    if running:
                        # move cursor to new updated location, which is where the total length is, and then drag it down the length of the previous color length
                        pyautogui.moveTo(canvas_x + x, canvas_y + total_length)
                        if color_lengths[current_color] == 1: # if the current color length is one, only a click is needed
                            pyautogui.click(canvas_x + x, canvas_y + total_length + 1)
                        else:
                            pyautogui.dragTo(canvas_x + x, canvas_y + total_length + color_lengths[current_color])
                        # update the new total length, reset the previous color length, update the current_color, and select it
                        total_length += color_lengths[current_color]
                        color_lengths[current_color] = 1
                        current_color = color
                        select_color(current_color)
                    else:
                        return
                else:  # if it is the same color, increase the color length by one
                    color_lengths[color] += 1
            else:
                pyautogui.moveTo(canvas_x + x, canvas_y + total_length)
                pyautogui.drag(0, color_lengths[current_color])


def combined_map_draw(directions, color_locations):
    """
    Combines the two main advantages of the drawing methods above.
    It gets directions of where and how long to draw-drag a line (or click) rather than receiving a map
    This simplifies the code SO MUCH compared to the complexity of pixel_map_draw but is also much faster than both
    """
    global canvas_x, canvas_y
    # combined_dict = draw_directions(image)
    # sort by frequency of color (how often it appears)
    # draw the most frequent colors first, then add on the lesser ones later
    def count_frequency(color_directions):
        frequency = 0
        for direction in color_directions:
            frequency += direction[2]
        return frequency

    color_frequencies = ((color, count_frequency(directions)) for color, directions in directions.items())
    sorted_color_frequencies = sorted(color_frequencies, reverse=True, key=lambda x: x[1])
    # if white is the most common, then since the canvas is default white, we can just remove it entirely from the color direction dictionary
    if sorted_color_frequencies[0][0] == 'white':
        sorted_color_frequencies.pop(0)
        directions.pop('white')

    for color, _ in sorted_color_frequencies:
        color_directions = directions[color]
        select_color(color, color_locations)
        for direction in color_directions:
            if running:
                if direction[2] == 1:
                    pyautogui.click(canvas_x + direction[0], canvas_y + direction[1])
                else:
                    pyautogui.moveTo(canvas_x + direction[0], canvas_y + direction[1])
                    # pyautogui.dragTo(canvas_x + direction[0], canvas_y + direction[1] + direction[2]) causes mistakes and lines through the output
                    pyautogui.drag(0, direction[2])

            else:
                return


def draw(image_name, draw_directions, color_locations):
    global canvas_box, canvas_x, canvas_y
    canvas_box = pyautogui.locateOnScreen(
        'images/canvas.png', region=(0, 0, screen_width, screen_height))
    canvas_x, canvas_y = canvas_box[0], canvas_box[1]
    
    combined_map_draw(draw_directions, color_locations)

    if running:
        with Image.open('images/input/{}.png'.format(image_name)) as im:
            save_canvas(image_name, im.size)


def save_canvas(name, image_size):
    # we remove some pixels from the box because it is not part of the actual canvas that is drawn on, just additional padding to help pyautogui to locate it
    pyautogui.screenshot('images/output/{}_copy.png'.format(name), region=(canvas_box[0]+1, canvas_box[1]+1, image_size[0], image_size[1]))


def setup(image_name, directions):
    th = threading.Thread(target=open_paint)
    th.start()
    # wait for paint application window to start
    time.sleep(1)
    new_locations = add_colors(directions["new_colors"])
    color_locations.update(new_locations)
    time.sleep(0.25)
    draw(image_name, directions['draw_directions'], color_locations)
    pyautogui.moveTo(screen_width-50, 50)
    th.join()
    

def full_directions(image_name):
    new_colors = expand_colors(image_name)
    COLORS.update(new_colors)
    
    return {
        "image_name": image_name,
        "new_colors": new_colors,
        "draw_directions": draw_directions(image_name)
    }


def main():
    keyboard.add_hotkey('ctrl+shift+a', stop_running)
    keep_open = input('keep open paint tabs after finishing? (y/n): ')

    input_images = os.listdir('images/input/')
    # images = ['images/input/{}'.format(input_image) for input_image in input_images]
    image_names = [os.path.splitext(input_image)[0] for input_image in input_images]
    
    with multiprocessing.Pool() as pool:
        all_directions = pool.map(full_directions, image_names)

    try:
        for directions in all_directions:
            running = True
            setup(directions['image_name'], directions)
            if not keep_open.lower() == 'y':
                stop_running()

    except KeyboardInterrupt:
        print('Exiting on KeyboardInterrupt')
        stop_running()
        exit()
    except pyautogui.FailSafeException:
        print('Exiting on FailSafeException')
        stop_running()


if __name__ == '__main__':
    main()