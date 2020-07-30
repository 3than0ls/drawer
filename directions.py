from interactions_class import InteractionsManager
from math import sqrt
from PIL import Image
import timeit
import time
import json
import os
from copy import deepcopy
import random

class Directions:
    def __init__(self, image_basename, color_quality=2):
        # figure it out lul
        self.image_basename = image_basename
        self.color_quality = color_quality

        self.new_colors = []

        self.cache = {}
        # a dictionary of all colors that will be used
        self.all_colors = {}

    def refresh_colors(self):
        self.cache.clear()
        self.all_colors.clear()


    def classify_color(self, rgb):
        # create dictionary that contains all colors so we can search through it
        if not self.all_colors:
            self.all_colors.update(InteractionsManager.COLORS)
            for color_pallete in self.new_colors:
                self.all_colors.update(color_pallete)

        if rgb in self.cache:
            return self.cache[rgb] # to optimize

        else:
            # colors likely contain an alpha value we do not care about
            r, g, b, *_ = rgb
            color_diffs = []
            for color_name, rgba in self.all_colors.items():
                color_r, color_g, color_b, _ = rgba
                # use euclidian distance to find the color difference
                color_diff = sqrt(abs(r - color_r)**2 +
                                    abs(g - color_g)**2 + abs(b - color_b)**2)
                color_diffs.append((color_diff, color_name))
            closest_color = min(color_diffs)[1]
            color_pallete_number = 0
            if closest_color in InteractionsManager.COLORS:
                # the closest color is in the default COLORS, so it doesn't matter what color pallete number we assign it to.
                # we'll just add it to the index of thevery last color pallete
                color_pallete_number = len(self.new_colors) - 1
            else:
                for number, color_pallete in enumerate(self.new_colors):
                    if closest_color in color_pallete:
                        color_pallete_number = number
            self.cache[rgb] = (closest_color, color_pallete_number)
            return self.cache[rgb]


    def generate_color_list(self):
        # the lower the self.color_quality is, the less colors the output image will have. However, the higher the amount, the longer it takes to recreate
        # setting a value to high will result in strange behavior, especially if the image doesn't actually have more than about 10*self.color_quality+20 different amount of colors
        self.new_colors = [{} for _ in range(self.color_quality)]
        index = 0
        with Image.open(os.path.join('input', self.image_basename)) as im:
            simplified_image = im.convert('P', palette=Image.ADAPTIVE, colors=20*self.color_quality).convert('RGBA')
            color_list = simplified_image.getcolors()

            # sort the color list by the count of pixels that have that color
            color_list.sort(reverse=True, key = lambda x: x[0])

            # filter out the alpha value to COLORS to use below
            rgb_only_list = list(map(lambda rgba: rgba[:3], InteractionsManager.COLORS.values()))

            current_color = 0
            for color_data in color_list:
                for rgb in rgb_only_list:
                    color_diff = sqrt(
                        abs(color_data[1][0] - rgb[0])**2 + 
                        abs(color_data[1][1] - rgb[1])**2 + 
                        abs(color_data[1][2] - rgb[2])**2
                    )
                    if color_diff <= min((4, 12/(self.color_quality)/2)):
                        # print('{} already exists as {}, with a color difference of {}'.format(color_data[1], rgb, color_diff))
                        break
                else:
                    self.new_colors[index][f'custom_color_{current_color}'] = color_data[1]
                    current_color += 1

                    if current_color - (index) * 10 == 10:
                        index += 1

                    if index >= len(self.new_colors):
                        break

            return self.new_colors

            # print('calculated colors for {}.png'.format(self.image_basename))

    def draw_directions(self):
        """
        generates directions that the drawer "reads" on where to start and how far to drag down
        The return value is a list with each index associated with an index in colors, which is a different color pallete
        Each list value is a dictionary, with a key of the color name equal to a list of directions for that color
        ex: (let's say that red is part of the first colors pallete and blue is part of the second)
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
        # print('calculating directions for {}'.format(self.image_basename))
        self.refresh_colors()
        directions = [{} for color_pallete in range(len(self.new_colors))]
        with Image.open(os.path.join('temp', self.image_basename)) as image:
            width, height = image.size
            pixel = image.load()
            for x in range(width):
                current_line_height = 0
                current_color = None
                current_clr_pallete_number = None
                origin = (x, 0)
                for y in range(height):
                    px_color, clr_pallete_number = self.classify_color(pixel[x, y])
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

