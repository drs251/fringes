import numpy as np


name = "Demo 5"
description = "An empty demo plugin using an object"


class MyPlugin:
    def __init__(self):
        print("demo5: init")
        self.parent = None
        self.send_data_function = None

    def process_frame(self, frame):
        print("demo5: process_frame")

    def show_window(self, show: bool = True):
        pass


plugin = MyPlugin()


def init(parent=None, send_data_function=None):
    global plugin
    plugin.send_data_function = send_data_function
    plugin.parent = parent


def process_frame(frame: np.ndarray):
    plugin.process_frame(frame)


def show_window(show: bool = True):
    plugin.show_window(show)
