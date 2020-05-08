import os
import subprocess
import threading
import shutil
import time
import pyautogui
import keyboard
import timeit
import multiprocessing
from PIL import Image
from interactions import select_color, COLORS, expand_colors, color_locations, add_colors, set_size, set_thickness, bucket_color
from directions import color_map, pixel_map, draw_directions
from downloader import download_from_cse, download_from_reddit
import json

screen_width, screen_height = pyautogui.size()
canvas_box, canvas_x, canvas_y = [None] * 3
running = True

# error when converting jpg to png, likely because of the time it takes to convert draw_directions has already started and missed

# assign settings
with open("settings.json", "r") as settings_file:
    settings = json.load(settings_file)
    thin_mode = settings["thin_mode"]
    max_size = settings["max_size"]
    color_quality = settings["color_quality"]
    save_temp = settings["save_temp"]
    keep_open = settings["keep_open"]


def stop_running():
    """doesnt work as intended half the time"""
    global running
    running = False
    exit()


def open_paint():
    # paint must be fullscreened for the program to be correctly calibrated (/max)
    subprocess.call(['cmd', '/c', 'start', '/max',
                     'C:\\Windows\System32\mspaint.exe'])


# drag_draw evolved into color_map_draw, which evolved into pixel_map_draw, and color_map_draw and pixel_map_draw kinda evolved/fused to make combined_map_draw
# the below are just there for "historical" purposes
# obsolete
def drag_draw():
    """precursor to what comes below"""
    # first, locate the canvas of the paint application window
    canvas_center = pyautogui.locateCenterOnScreen(
        'images/canvas.png', region=(0, 0, screen_width, screen_height))
    if canvas_center:
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



def save_canvas(name, image_size):
    # we remove some pixels from the box because it is not part of the actual canvas that is drawn on, just additional padding to help pyautogui to locate it
    pyautogui.screenshot(os.path.join('output/', '{}_copy.png'.format(name)), region=(canvas_box[0], canvas_box[1], image_size[0]-1, image_size[1]-1))


def full_directions(image_basename):
    global color_quality
    new_colors = expand_colors(image_basename, num=color_quality)
    
    return {
        "image_basename": image_basename,
        "new_colors": new_colors,
        "draw_directions": draw_directions(image_basename, new_colors)
    }


def modify_image(image_basename):
    global max_size
    with Image.open(os.path.join('input', image_basename)) as im:
        # limit the size of these images so they don't take too long to complete
        if im.size[0] > max_size[0] or im.size[1] > max_size[1]: # maybe base these constant values off of pyautogui.screenWidth and screenHeight?
            im.thumbnail(max_size, Image.ANTIALIAS)
        # image_name = os.path.splitext(image_basename)[0]
        im.save(os.path.join('temp', '{}'.format(image_basename)))

def combined_map_draw(directions, color_locations):
    global canvas_x, canvas_y
    # combined_dict = draw_directions(image)
    # sort by frequency of color (how often it appears)
    # draw the most frequent colors first, then add on the lesser ones later
    def count_frequency(color_pallete):
        frequency = 0
        for direction in color_pallete:
            frequency += direction[2]
        return frequency

    for color_pallete_number, color_pallete_directions in enumerate(directions['draw_directions']):
        new_locations = add_colors(directions["new_colors"][color_pallete_number])
        color_locations.update(new_locations)

        color_frequencies = ((color, count_frequency(directions)) for color, directions in color_pallete_directions.items())
        sorted_color_frequencies = sorted(color_frequencies, reverse=True, key=lambda x: x[1])
        


        for i, sorted_color_frequency in enumerate(sorted_color_frequencies):
            color = sorted_color_frequency[0]
            color_directions = color_pallete_directions[color]
            select_color(color, color_locations)
            if i == 0 and color_pallete_number == 0:
                # the first index of sorted_color_frequency of the first color_pallete_number is the most common/frequent color, so bucket it
                bucket_color(canvas_x, canvas_y)
            else:
                for direction in color_directions:
                    if running:
                        if direction[2] == 1:
                            if not thin_mode:
                                pyautogui.click(canvas_x + direction[0], canvas_y + direction[1])
                            else:
                                # if thinnest thickness is used, perhaps use this?
                                pyautogui.moveTo(canvas_x + direction[0], canvas_y + direction[1])
                                pyautogui.drag(0, 2)
                        else:
                            pyautogui.moveTo(canvas_x + direction[0], canvas_y + direction[1])
                            if not thin_mode:
                                pyautogui.drag(0, direction[2])
                            else:
                                # if thinnest thickness is used, extended the line_length because line lengths are one pixel too short
                                pyautogui.drag(0, direction[2]+1)
                    else:
                        return



def draw(draw_directions, color_locations):
    global canvas_box, canvas_x, canvas_y
    with Image.open(os.path.join('temp', draw_directions['image_basename'])) as im:
        # 6, 144 is about the default x, y location for my canvas
        canvas_box = (6, 144, im.size[0], im.size[1])
    # canvas_box = pyautogui.locateOnScreen('images/canvas.png', region=(0, 0, screen_width, screen_height))
    canvas_x, canvas_y = canvas_box[0], canvas_box[1]

    set_size(canvas_box[2:4])
    time.sleep(0.1)
    set_thickness()
    time.sleep(0.8)
    
    combined_map_draw(draw_directions, color_locations)

    if running:
        image_name = os.path.splitext(draw_directions['image_basename'])[0]
        save_canvas(image_name, im.size)



def setup(directions):
    th = threading.Thread(target=open_paint)
    th.setDaemon(True) # hopefully this works properly, haven't actually tested it
    th.start()
    # wait for paint application to start
    time.sleep(0.5)
    pyautogui.moveTo(screen_width-50, 50)
    draw(directions, color_locations)
    pyautogui.moveTo(screen_width-50, 50)
    th.join()



def main():
    try:
        pyautogui.PAUSE = 0.000001

        keyboard.add_hotkey('ctrl+shift+a', stop_running)

        image_basenames = [os.path.basename(input_image) for input_image in os.listdir('input')]
        

        with multiprocessing.Pool() as pool:
            print('modifying images...')
            pool.map(modify_image, image_basenames)
            time.sleep(1)
            print('calculating drawing directions...')
            all_directions = pool.map(full_directions, image_basenames)

        # print('Starting in 5 seconds...')
        # time.sleep(5)

        for directions in all_directions:
            # print_results(directions)
            if running:
                setup(directions)
            if not keep_open:
                subprocess.call(['taskkill', '/f', '/im', 'mspaint.exe'])


    except KeyboardInterrupt:
        print('Exiting on KeyboardInterrupt')
        stop_running()
    except pyautogui.FailSafeException:
        print('Exiting on FailSafeException')
        stop_running()
    finally:
        # clear everything in temp
        basenames = [os.path.basename(input_image) for input_image in os.listdir('temp/')]
        for basename in basenames:
            if save_temp and running:
                shutil.move(os.path.join('temp', basename), os.path.join('output', basename))
            else:
                os.remove(os.path.join('temp', basename))




if __name__ == '__main__':
    main()