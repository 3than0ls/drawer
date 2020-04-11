from PIL import Image
import pyautogui
import time
screen_width, screen_height = pyautogui.size()

# ms paint default colors that are given
COLORS = {
    "black":            (0, 0, 0, 255),
    "gray":             (127, 127, 127, 255),
    "dark-red":         (136, 0 , 21, 255),
    "red":              (237, 28, 36, 255),
    "orange":           (255, 127, 39, 255),
    "neon-yellow":      (255, 242, 0, 255),
    "green":            (34, 177, 76, 255),
    "light-blue":       (0, 162, 232, 255),  # more like light-blue
    "indigo":           (63, 72, 204, 255),
    "purple":           (163, 73, 164, 255),  # more like lavender
    "white":            (255, 255, 255, 255),
    "light-gray":       (195, 195, 195, 255),
    "tan":              (185, 122, 87, 255),
    "pink":             (255, 174, 201, 255),
    "yellow":           (255, 201, 14, 255),
    "sand":             (239, 228, 176, 255),
    "bright-green":     (181, 230, 29, 255),
    "light-blue":       (153, 217, 234, 255),
    "gray-blue":        (112, 146, 190, 255),
    "light-purple":     (200, 191, 231, 255),
}

# create some custom colors (because it can never hurt to have more colors for a higher quality image)
CUSTOM_COLORS = {
    "dark-green":       (25, 82, 46, 255),
    "light-brown":      (150, 123, 87, 255),
    "dark-brown":       (82, 50, 25, 255),
    "dark-gray":        (50, 50, 50, 255),
    "red-orange":       (255, 83, 73, 255),
    "skin":             (236, 188, 180, 255),
    "turqoise":         (64, 224, 208, 255),
    "hot-pink":         (255, 0, 195, 255),
    "blue":             (5, 5, 255, 255),
    "maroon":           (87, 0, 0, 255),
}


def expand_colors(image_name):
    global COLORS, CUSTOM_COLORS, color_locations
    # two modes: non-advanced, which just adds more pre-defined colors to the color palette, and advanced, which takes the top 10 dominant colors of the image
    # new_colors = CUSTOM_COLORS
    new_colors = {}

    with Image.open('images/input/{}.png'.format(image_name)) as im:
        simplified_image = im.convert('P', palette=Image.ADAPTIVE, colors=10).convert('RGBA')
        color_list = simplified_image.getcolors()

        current_color = 0
        for color_data in color_list:
            new_colors['custom_color_{}'.format(current_color)] = color_data[1]
            current_color += 1

    return new_colors


def add_colors(new_colors):
    color_1_button_location = pyautogui.locateCenterOnScreen('images/color_1.png')
    color_2_button_location = (color_1_button_location[0] + 40, color_1_button_location[1])
    edit_colors_button_location = (color_1_button_location[0] + 300, color_1_button_location[1])

    pyautogui.click(color_2_button_location[0], color_2_button_location[1])

    new_locations = {}

    current_box = 0
    for color, rgb in new_colors.items():
        # click edit colors button
        pyautogui.click(edit_colors_button_location[0], edit_colors_button_location[1])
        time.sleep(0.1)
        # double click Red input box
        pyautogui.doubleClick(1475, 770)
        pyautogui.write(str(rgb[0]))
        # doube click Green input box
        pyautogui.doubleClick(1475, 795)
        pyautogui.write(str(rgb[1]))
        # double click Blue input box
        pyautogui.doubleClick(1475, 820)
        pyautogui.write(str(rgb[2]))
        # move to okay button
        pyautogui.click(1100, 845)

        # add locations onto current locations
        # location of first custom color box is (760, 103). From then on, the gap between boxes is 22 pixels, and we only need to go right
        new_locations[color] = (760 + (current_box * 22), 103)
        current_box += 1

    # click the color 1 button
    pyautogui.click(color_1_button_location[0], color_1_button_location[1])
    
    pyautogui.moveTo(screen_width-50, 50)

    return new_locations


def set_thickness():
    # something seems to be wrong with the thinnest thickness
    thickness_button = pyautogui.locateCenterOnScreen('images/thickness.png', region=(0, 0, screen_width, screen_height))
    pyautogui.click(thickness_button[0], thickness_button[1])
    time.sleep(0.45)
    pyautogui.click(thickness_button[0], thickness_button[1]+55)
    pyautogui.moveTo(screen_width-50, 50)


def locate_color(rgb_value):
    with Image.open('images/toolbar.png') as toolbar:
        width, height = toolbar.size
        pixel = toolbar.load()
        # a brute force search, where we look through every pixel until we find the one that matches the color
        for x in range(width):
            for y in range(height):
                if (pixel[x, y] == rgb_value):
                    return (x+5, y+5)

def color_selection_locations(refresh=False, _cache={}):
    global COLORS
    # memoize color location so we don't have to relocate
    if not _cache or refresh:
        locations = { # we have to define these locations manually, because they can be found in places besides the default color palette in the paint UI
            "black": (760, 59),
            "white": (760, 81),
            "light-gray": (782, 81)
        }
        for color, rgb_value in COLORS.items():
            if color not in locations:
                location = locate_color(rgb_value)
                if location:
                    locations[color] = location
        _cache = locations
        return locations
    else:
        return _cache



color_locations = color_selection_locations()


def select_color(color, color_locations):
    if color in color_locations:
        cache_mouse_x, cache_mouse_y = pyautogui.position()
        color_location = color_locations[color]
        pyautogui.doubleClick(
            color_location[0], color_location[1], interval=0.1)
        pyautogui.moveTo(cache_mouse_x, cache_mouse_y)



def _test():
    global color_locations
    locations = color_selection_locations()
    print(locations)


if __name__ == '__main__':
    try:
        _test()
    except KeyboardInterrupt:
        print('Exiting')
        exit()
