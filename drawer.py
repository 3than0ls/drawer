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
# import interactions
import directions
# from downloader import download_from_cse, download_from_reddit
import json
import interactions

IM = interactions.InteractionsManager()


# also: check if the resizing is done first and then

class Drawer:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.canvas_box, self.canvas_x, self.canvas_y = [None] * 3

        self.running = True

        # settings
        with open("settings.json", "r") as settings_file:
            settings = json.load(settings_file)
            self.thickness = settings["thickness"] # thickness should usually always be 1
            self.max_size = settings["max_size"]
            self.color_quality = settings["color_quality"]
            self.save_temp = settings["save_temp"]
            self.keep_open = settings["keep_open"]

    @staticmethod
    def open_paint():
        # perhaps move to interaction file
        # paint must be fullscreened for the program to be correctly calibrated (which is what the /max does)
        subprocess.call(['cmd', '/c', 'start', '/max', 'C:\\Windows\System32\mspaint.exe'])

    def stop_running(self):
        self.running = False
        exit()
    
    def save_canvas(self, name):
        # we remove some pixels from the box because it is not part of the actual canvas that is drawn on, just additional padding to help pyautogui to locate it
        # TO BE DEFINED, image_size (self), and maybe default name to None and instead access a self value
        # pyautogui.screenshot(os.path.join('output/', '{}_copy.png'.format(name)), region=(self.canvas_box[0], self.canvas_box[1], image_size[0]-1, image_size[1]-1))
        pyautogui.screenshot(os.path.join('output/', '{}_copy.png'.format(name)), region=(self.canvas_box[0], self.canvas_box[1], self.canvas_box[2]-1, self.canvas_box[3]-1))

    def modify_image(self, image_basename):
        with Image.open(os.path.join('input', image_basename)) as im:
            # limit the size of these images so they don't take too long to complete
            if im.size[0] > self.max_size[0] or im.size[1] > self.max_size[1]: # maybe base these constant values off of pyautogui.screenWidth and screenHeight?
                im.thumbnail(self.max_size, Image.ANTIALIAS)
            im.save(os.path.join('temp', image_basename))

    def full_directions(self, image_basename):
        # sort of like processing draw directions to be used in actual drawing
        directions = directions_class.Directions(image_basename, color_quality=self.color_quality) # --------------------- directions_class code

        new_colors = directions.generate_color_list()

        with Image.open(os.path.join('temp', image_basename)) as im:
            image_size = im.size

        data = {
            "image_size": image_size,
            "image_basename": image_basename,
            "new_colors": new_colors,
            "draw_directions": directions.draw_directions()
        }

        # with open("data.json", "w+") as f: 
        #     json.dump(data, f, indent=4)

        return data

    def clear_temp(self):
        # clear everything in temp
        basenames = [os.path.basename(input_image) for input_image in os.listdir('temp/')]
        for basename in basenames:
            if self.save_temp and self.running:
                shutil.move(os.path.join('temp', basename), os.path.join('output', basename))
            else:
                os.remove(os.path.join('temp', basename))


    def draw(self, directions, color_locations):
        # combined_dict = draw_directions(image)
        # sort by frequency of color (how often it appears)
        # draw the most frequent colors first, then add on the lesser ones later
        def count_frequency(color_pallete):
            frequency = 0
            for direction in color_pallete:
                frequency += direction[2]
            return frequency

        for color_pallete_number, color_pallete_directions in enumerate(directions['draw_directions']):
            new_locations = IM.add_colors(directions["new_colors"][color_pallete_number])
            IM.update_color_locations(new_locations)

            color_frequencies = ((color, count_frequency(directions)) for color, directions in color_pallete_directions.items())
            sorted_color_frequencies = sorted(color_frequencies, reverse=True, key=lambda x: x[1])

            for i, sorted_color_frequency in enumerate(sorted_color_frequencies):
                color = sorted_color_frequency[0]
                color_directions = color_pallete_directions[color]
                IM.select_color(color)
                if i == 0 and color_pallete_number == 0:
                    # has an issue of not bucketing if the color is already on default pallete
                    # the first index of sorted_color_frequency of the first color_pallete_number is the most common/frequent color, so bucket it
                    IM.bucket_color()
                else:
                    for direction in color_directions:
                        if self.running:
                            if direction[2] == 1:
                                if self.thickness != 1:
                                    pyautogui.click(self.canvas_x + direction[0], self.canvas_y + direction[1])
                                else:
                                    # if thinnest thickness is used, perhaps use this?
                                    pyautogui.moveTo(self.canvas_x + direction[0], self.canvas_y + direction[1])
                                    pyautogui.drag(0, 2)
                            else:
                                pyautogui.moveTo(self.canvas_x + direction[0], self.canvas_y + direction[1])
                                if self.thickness != 1:
                                    pyautogui.drag(0, direction[2])
                                else:
                                    # if thinnest thickness is used, extended the line_length because line lengths are one pixel too short
                                    pyautogui.drag(0, direction[2]+1)
                        else:
                            return
        
    def awake(self, directions):
        # previously known as setup
        th = threading.Thread(target=Drawer.open_paint)
        th.setDaemon(True) # hopefully this works properly, haven't actually tested it
        th.start()
        # wait for paint application to start
        time.sleep(0.5)
        pyautogui.moveTo(self.screen_width - 50, 50)
        self.setup(directions, IM.color_locations)
        pyautogui.moveTo(self.screen_width - 50, 50)
        th.join()

    def setup(self, draw_directions, color_locations):
        # previously known as draw
        # 6, 144 is about the default x, y location for my canvas
        self.canvas_box = (6, 144, draw_directions["image_size"][0], draw_directions["image_size"][1])
        # canvas_box = pyautogui.locateOnScreen('images/canvas.png', region=(0, 0, screen_width, screen_height))
        self.canvas_x, self.canvas_y = self.canvas_box[0], self.canvas_box[1]

        IM.set_size(self.canvas_box[2:4])
        time.sleep(0.1)
        IM.set_thickness()
        time.sleep(0.8)
        
        self.draw(draw_directions, color_locations)

        if self.running:
            image_name = os.path.splitext(draw_directions['image_basename'])[0]
            self.save_canvas(image_name)


    def generate_direction_file(self, image_basename):
        print(f"Generating json file of directions for {image_basename}")
        try: 
            self.modify_image(image_basename)
            directions = self.full_directions(image_basename)
            self.save_directions(directions)
        except KeyboardInterrupt:
            print('Exiting on KeyboardInterrupt')
            self.stop_running()
        finally:
            self.clear_temp()

    def save_directions(self, directions):
        with open(f"output/{os.path.splitext(directions['image_basename'])[0]}_directions.json", "w+") as f: 
            json.dump(directions, f, indent=4)

    def main(self):
        try:
            pyautogui.PAUSE = 0.000001

            keyboard.add_hotkey('ctrl+shift+a', self.stop_running)

            paths = [os.path.basename(input_path) for input_path in os.listdir('input')]

            direction_basenames = []
            image_basenames = []
            for path in paths:
                if path.lower().endswith('.json'):
                    direction_basenames.append(path)
                else:
                    image_basenames.append(path)
            
            all_directions = None

            with multiprocessing.Pool() as pool:
                print('modifying images...')
                pool.map(self.modify_image, image_basenames)
                # time.sleep(1)
                print('calculating drawing directions...')
                all_directions = pool.map(self.full_directions, image_basenames)

            for direction_basename in direction_basenames:
                with open(os.path.join("input/", direction_basename), "r") as f:
                    directions = json.load(f)
                all_directions.append(directions)

            for directions in all_directions:
                # print_results(directions)
                if self.running:
                    self.awake(directions)
                if not self.keep_open:
                    subprocess.call(['taskkill', '/f', '/im', 'mspaint.exe'])


        except KeyboardInterrupt:
            print('Exiting on KeyboardInterrupt')
            self.stop_running()
        except pyautogui.FailSafeException:
            print('Exiting on FailSafeException')
            self.stop_running()
        finally:
            self.clear_temp()


if __name__ == '__main__':
    d = Drawer()
    d.generate_direction_file("test.png")
    # d.main()
