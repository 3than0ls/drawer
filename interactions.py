from PIL import Image
import pyautogui
import time
from math import sqrt
import os
import json
from settings_manager import calibrate


class InteractionsManager:
    """handles every interaction except actually drawing using pyautogui to ms paint"""
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

    BUCKET_BUTTON = (254, 57)
    BRUSH_BUTTON = (309, 49)

    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        
        with open('settings.json', 'r') as settings:
            self.locations = json.load(settings)['locations']

        self.color_1_button_location = None
        self.edit_color_prompt_location = None

        self.thickness_button = None

        self.resize_button = None

        self.color_locations = self.find_color_locations()
        

        self.canvas_x = None
        self.canvas_y = None

    def bucket_color(self):
        """
        ms paint provides an option to cover an entire area with a single solid color. Used to color the most frequent color. It buckets the currently selected color
        # print(pyautogui.locateOnScreen('images/bucket.png'))
        # Location of bucket button: Box(left=254, top=57, width=27, height=28) (we add a 10 pixel padding below anyways)
        # print(pyautogui.locateOnScreen('images/brushes.png'))
        # Location of brushes button: Box(left=309, top=49, width=51, height=69) (we and a 11 pixel padding below anyways)
        # locations should be universal, and are defined in constants BUCKET_BUTTON and BRUSH_BUTTON
        """

        pyautogui.click(InteractionsManager.BUCKET_BUTTON[0]+10, InteractionsManager.BUCKET_BUTTON[1]+10)
        pyautogui.click(self.canvas_x+3, self.canvas_y+3)
        pyautogui.click(InteractionsManager.BRUSH_BUTTON[0]+11, InteractionsManager.BRUSH_BUTTON[1]+11, 3)
    
    def add_colors(self, new_colors):
        if self.color_1_button_location is None or self.edit_color_prompt_location is None: # if locations are not defined
            if 'color_1_button' in self.locations: # open settings and see if location is in there
                self.color_1_button_location = self.locations['color_1_button']
            else: # if not locate it and calibrate it in settings
                self.color_1_button_location = pyautogui.locateCenterOnScreen('images/color_1.png')
                calibrate('color_1_button', self.color_1_button_location)

            if 'edit_color_prompt' in self.locations: # open settings and see if location is in there
                self.edit_color_prompt_location = self.locations['edit_color_prompt']
            else: # if not, set value to None and later the value will be found in the correct environmental conditions (below)
                self.edit_color_prompt_location = None
        
        # locations of buttons that are only used within this function, and are based off of locations of already known buttons
        color_2_button_location = (self.color_1_button_location[0] + 40, self.color_1_button_location[1])
        edit_colors_button_location = (self.color_1_button_location[0] + 300, self.color_1_button_location[1])

        # click on color 2 button so we can edit it
        pyautogui.click(color_2_button_location[0], color_2_button_location[1])
        # slow down pyautogui so it doesn't have errors
        pyautogui.PAUSE = 0.005

        new_locations = {}
        current_box = 0
        for color, rgb in new_colors.items():   
            # click edit colors button
            pyautogui.click(edit_colors_button_location[0], edit_colors_button_location[1])
            time.sleep(0.1)

            if self.edit_color_prompt_location is None:
                time.sleep(0.4)
                self.edit_color_prompt_location = pyautogui.locateCenterOnScreen('images/edit_colors.png')
                calibrate('edit_color_prompt', self.edit_color_prompt_location)

            # double click Red input box
            pyautogui.doubleClick(382 + self.edit_color_prompt_location[0], 221 + self.edit_color_prompt_location[1])
            pyautogui.write(str(rgb[0]))
            # doube click Green input box
            pyautogui.doubleClick(382 + self.edit_color_prompt_location[0], 236 + self.edit_color_prompt_location[1])
            pyautogui.write(str(rgb[1]))
            # double click Blue input box
            pyautogui.doubleClick(382 + self.edit_color_prompt_location[0], 255 + self.edit_color_prompt_location[1])
            pyautogui.write(str(rgb[2]))
            # move to okay button
            pyautogui.click(7 + self.edit_color_prompt_location[0], 286 + self.edit_color_prompt_location[1])

            # add locations onto current locations
            # location of first custom color box is (760, 103). From then on, the gap between boxes is 22 pixels, and we only need to go right
            new_locations[color] = (760 + (current_box * 22), 103)
            current_box += 1

        # speed it back up
        pyautogui.PAUSE = 0.000001

        # click the color 1 button
        pyautogui.click(self.color_1_button_location[0], self.color_1_button_location[1])
        
        # move mouse out of the way
        pyautogui.moveTo(self.screen_width-50, 50)

        return new_locations
    
    def set_thickness(self, thickness=1):
        thickness = min(4, max(1, thickness))-1
        if self.thickness_button is None:
            if 'thickness_button' in self.locations: # open settings and see if location is in there
                self.thickness_button = self.locations['thickness_button']
            else: # if not locate it and update settings
                self.thickness_button = pyautogui.locateCenterOnScreen('images/thickness.png')
                calibrate('thickness_button', self.thickness_button)
        pyautogui.click(self.thickness_button[0]+1, self.thickness_button[1]+1)
        time.sleep(0.45)
        # clicks thickness that is 55 pixels below the button, which is constant and universal
        # may change later, because it only sets thickness to one type
        pyautogui.click(self.thickness_button[0], self.thickness_button[1]+55 + 30*thickness)
        # move cursor aside
        pyautogui.moveTo(self.screen_width-50, 50)
        
        
    def set_size(self, size):
        if self.resize_button is None:
            if 'resize_button' in self.locations: # open settings and see if location is in there
                self.resize_button_location = self.locations['resize_button']
            else: # if not locate it and update settings
                self.resize_button_location = pyautogui.locateCenterOnScreen('images/resize.png')
                calibrate('resize_button', self.resize_button_location)

        self.canvas_x, self.canvas_y = size
                
        pyautogui.click(self.resize_button_location)
        # location of pixel resize button
        pyautogui.click(215, 155)
        # location of disable maintain ratio button
        pyautogui.click(75, 265)
        
        # write in width and height values, but add an extra padding as to not interfere with the resize dragging buttons on the edges
        pyautogui.doubleClick(230, 185)
        pyautogui.write(str(size[0] + 5))
        pyautogui.doubleClick(230, 227)
        pyautogui.write(str(size[1] + 5))

        # location of OK button
        pyautogui.click(140, 450)

    def locate_color(self, rgb_value):
        with Image.open('images/toolbar.png') as toolbar:
            width, height = toolbar.size
            pixel = toolbar.load()
            # a brute force search, where we iterate through every pixel until we find the one that matches the color
            for x in range(width):
                for y in range(height):
                    if (pixel[x, y] == rgb_value):
                        return (x+5, y+5)

    def update_color_locations(self, new_locations):
        self.color_locations.update(new_locations)
    
    def find_color_locations(self):
        locations = { # we have to define these locations manually, because they can be found in places besides the default color palette in the paint UI
            "black": (760, 59),
            "white": (760, 81),
            "light-gray": (782, 81)
        }
        for color, rgb_value in InteractionsManager.COLORS.items():
            if color not in locations:
                location = self.locate_color(rgb_value)
                if location:
                    locations[color] = location
        return locations

    
    def select_color(self, color):
        if color in self.color_locations:
            cache_mouse_x, cache_mouse_y = pyautogui.position()
            color_location = self.color_locations[color]
            pyautogui.doubleClick(
                color_location[0], color_location[1], interval=0.1)
            pyautogui.moveTo(cache_mouse_x, cache_mouse_y)