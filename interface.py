from tkinter import filedialog
import tkinter as tk
import math
import os
from PIL import Image, ImageTk
from settings_manager import update_settings, get_settings
from statistics import mean
import json

def split(list, n):
    k, m = divmod(len(list), n)
    return (list[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))

def new_split(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]




class App(tk.Frame):
    def __init__(self, width, height, master=None):
        super().__init__(master)
        self.master = master
        
        self.image_grid = tk.Frame(self.master)
        self.settings = tk.Frame(self.master)

        # self.frame = tk.Frame(self.master)
        # self.frame.focus_set()

        self.application_width = width
        self.application_height = height

        self.dir = "C:/Users/Ethanol/drawer/input"

        with open("settings.json", "r") as settings_file:  
            settings = json.load(settings_file)
            self.max_size = settings['max_size'] 


        self.init_app()

    def clear(self, bottom_label='Open an image folder with File > Open to view'):
        # self.frame.bind("<Configure>", App.resize)
        children = []
        children.extend(list(self.image_grid.children.values()))
        children.extend(list(self.settings.children.values()))

        for child in children:
            child.destroy()
        self.dir = ''
        self.bottom_label.config(text=bottom_label)
        

    def init_app(self):
        self.master.geometry("{}x{}".format(self.application_width, self.application_height))
        self.master.title('Drawer')
        self.master.iconbitmap('images/drawer_icon.ico')
        self.master.update()

        self.image_grid.pack(fill=tk.BOTH, expand=True)

        self.theme = {"bg": "#333333"}

        self.image_grid.config(self.theme)
        self.settings.config(self.theme)

        # this refers to the menu that is the horizontal bar at the top
        self.menu = tk.Menu(self.master)
        self.master.config(menu=self.menu)
        
        # file button
        self.file = tk.Menu(self.menu, tearoff=0)
        self.file.add_command(label="Open", command=self.open_dir)
        self.file.add_command(label="Clear", command=self.clear)
        self.file.add_command(label="Settings", command=self.open_settings)
        self.file.add_separator()
        self.file.add_command(label="Exit", command=self.client_exit)
        
        # adds cascading menus self.file and self.edit to the horizontal self.menu
        self.menu.add_cascade(label="File", menu=self.file)
        self.menu.add_command(label="Run", menu=self.run)

        
        self.bottom_label = tk.Label(self.master, text=self.dir)
        self.bottom_label.config({"bg": "#222222", "fg": "#CCCCCC"})
        self.bottom_label.place(x=0, rely=1, anchor="sw", relwidth=1)
        self.show_images(self.dir)


    def open_dir(self):
        new_dir = filedialog.askdirectory()
        if new_dir:
            self.clear()
            self.dir = new_dir
            self.bottom_label.config(text=self.dir)
            self.show_images(self.dir)

    def find_average_width(self, dir):
        image_widths = []
        for basename in self.image_basenames:
            with Image.open(os.path.join(dir, basename)) as img:
                if img.size[0] > self.max_size[0] or img.size[1] > self.max_size[1]:
                    img.thumbnail(self.max_size, Image.ANTIALIAS)
                image_widths.append(img.size[0])
        self.average_width = int(mean(image_widths))
    

    def show_images(self, dir):
        self.clear(bottom_label=dir)
        self.settings.forget()

        self.image_grid.pack(fill=tk.BOTH, expand=True)
        self.image_basenames = [os.path.basename(input_image) for input_image in os.listdir(dir)]
        self.find_average_width(dir)
        columns = math.ceil(self.master.winfo_width()/self.average_width)

        # split the images into columns amount of rows
        images = list(new_split(self.image_basenames, columns))

        for i in range(len(images)):
            self.image_grid.columnconfigure(i, weight=1, minsize=self.max_size[0]/2)
            self.image_grid.rowconfigure(i, weight=1, minsize=self.max_size[1]/2)
            for j in range(len(images[i])):
                frame = tk.Frame(self.image_grid)
                frame.grid(row=i, column=j, padx=3, pady=3)

                with Image.open(os.path.join(dir, images[i][j])) as img:
                    wpercent = (self.average_width/float(img.size[0]))
                    hsize = int((float(img.size[1])*float(wpercent)))
                    img = img.resize((self.average_width, hsize))

                    render = ImageTk.PhotoImage(img)
                    tk_img = tk.Label(frame, image=render)
                    tk_img.config({"bd": 0})
                    tk_img.image = render

                    tk_img.pack()

    def save_dwr_settings(self):
        for setting_name, value in self.dwr.items():
            if setting_name == 'max_size':
                try:
                    max_size = [int(value[i].get()) for i in range(2)]
                    update_settings('max_size', max_size)
                except ValueError:
                    print('Integer was not given')
            else:
                update_settings(setting_name, value.get())
        self.settings.focus()

    def open_settings(self):
        self.clear(bottom_label='Settings')
        self.image_grid.forget()
        self.settings.pack(fill=tk.BOTH, expand=True)
        
        settings = get_settings()
        self.dwr = {}
        self.dwr['thin_mode'] = tk.BooleanVar(value=settings['thin_mode'])
        self.dwr['color_quality'] = tk.IntVar(value=settings['color_quality'])
        self.dwr['max_size'] = [tk.StringVar(value=str(settings['max_size'][i])) for i in range(2)]
        self.dwr['save_temp'] = tk.BooleanVar(value=settings['save_temp'])
        self.dwr['keep_open'] = tk.BooleanVar(value=settings['keep_open'])
        


        canvas = tk.Canvas(self.settings, borderwidth=0, highlightthickness=0)
        canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        scrollbar = tk.Scrollbar(self.settings, command=canvas.yview, )
        scrollbar.pack(side=tk.LEFT, fill='y', expand=0)
        canvas.configure(yscrollcommand=scrollbar.set)


        frame = tk.Frame(canvas)
        frame.config(self.theme)
        
        frame_canvas = canvas.create_window((0, 0), window=frame, anchor='nw')
        
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.itemconfigure(frame_canvas, width=self.master.winfo_width(), height=self.master.winfo_height())
            # canvas.create_window((0, 0), window=frame, anchor='nw', width=self.master.winfo_width(), height=self.master.winfo_height())
        canvas.bind('<Configure>', on_configure)


        def enable_disable_radio(variable, row):
            theme = {
                "indicatoron": False,
                "bd": 0,
                "fg": "#eeeeee",
                "bg": "#a8142a",
                "activeforeground": "#eeeeee",
                "activebackground": "#28a814",
                "selectcolor": "#28a814",
                "relief": tk.SUNKEN,
                "cursor": 'hand2'
            }

            var_true = tk.Radiobutton(frame, text="Enable", variable=variable, value=True)
            var_true.grid(row=row, column=3, sticky=tk.NSEW, pady=20, ipadx=15, ipady=7, padx=2)
            var_true.config(theme)
            var_false = tk.Radiobutton(frame, text="Disable", variable=variable, value=False)
            var_false.grid(row=row, column=4, sticky=tk.NSEW, pady=20, ipadx=15, ipady=7, padx=2)
            var_false.config(theme)
    

        # thin mode
        dwr_thin_label = tk.Label(frame, text="Thin Mode")
        enable_disable_radio(self.dwr['thin_mode'], 1)
        
        
        # input field
        dwr_max_size_label = tk.Label(frame, text="Image Max Size")
        for i in range(2):
            dwr_max_size = tk.Entry(frame, width=5, textvariable=self.dwr['max_size'][i])
            dwr_max_size.config(justify=tk.CENTER)
            dwr_max_size.grid(row=2, column=3+i, sticky=tk.NSEW, pady=20, ipadx=15, ipady=7, padx=2)

        # dropdown
        dwr_clr_quality_label = tk.Label(frame, text="Color Iterations")
        dwr_clr_quality_menu = tk.OptionMenu(frame, self.dwr['color_quality'], *range(1, 10))
        dwr_clr_quality_menu.config({
            "indicatoron": False,
            "bd": 0,
            "fg": "#eeeeee",
            "bg": "#555555",
            "activeforeground": "#ededed",
            "activebackground": "#555555",
            "cursor": 'hand2',
            "relief": tk.SUNKEN,
            "highlightthickness": 0,
        })
        dwr_clr_quality_menu.grid(row=3, columnspan=2, column=3, sticky=tk.NSEW, pady=20, ipadx=15, ipady=7, padx=2)


        # save temp
        dwr_save_temp_label = tk.Label(frame, text="Save Resized")
        enable_disable_radio(self.dwr['save_temp'], 4)

        # keep open
        dwr_keep_open_label = tk.Label(frame, text="Keep Paint Window Open")
        enable_disable_radio(self.dwr['keep_open'], 5)

        # dwr save buton
        save_button_theme = {
            "bd": 0,
            "fg": "#efefef",
            "bg": "#555555",
            "activeforeground": "#dddddd",
            "activebackground": "#666666",
            "cursor": 'hand2',
            "relief": tk.SUNKEN,
            "highlightthickness": 0,
        }
        dwr_save = tk.Button(frame, text="Save", command=self.save_dwr_settings)
        dwr_save.config(save_button_theme)
        dwr_save.grid(row=6, column=2, sticky=tk.NSEW, padx=90, ipady=10)


        # left and right padding
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(5, weight=1)
        # bottom padding
        frame.grid_rowconfigure(7, weight=1)
        # top padding
        frame.grid_rowconfigure(0, minsize=70)
        # spacing between labels and inputs
        frame.grid_columnconfigure(2, minsize=225, weight=1)


        settings_list = [dwr_thin_label, dwr_max_size_label, dwr_clr_quality_label, dwr_save_temp_label, dwr_keep_open_label]

        for row, setting in enumerate(settings_list):
            setting.grid(row=row+1, column=1, padx=50, sticky=tk.W, pady=20)
            setting.config({"fg": "#eeeeee", **self.theme})

    def run(self):
        pass


    def client_exit(self):
        exit()


def main():
    root = tk.Tk()
    width, height = 1000, 700
    app = App(width, height, master=root)
    app.mainloop()

if __name__ == '__main__':
    main()