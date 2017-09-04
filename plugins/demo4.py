from PyQt5.QtWidgets import QHBoxLayout

import plugin_canvas
import random
import numpy as np
import plugins.libs.vortex_tools_core as vtc
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt

name = "Demo 4"

description = "Shows the data as grayscale image"

# the area for plotting:
canvas = None

# a function reference to ask the main program to start or stop sending data (i.e. when closing the window)
send_data = None


def init(parent=None, send_data_function=None):
    """
    Initialize the plugin. Build the window and create any necessary variables
    :param parent: The main window can be provided here
    :param send_data_function: A function that can start or stop data being sent
    """
    global canvas
    global send_data
    send_data = send_data_function
    canvas = plugin_canvas.PluginCanvas(parent, send_data)
    canvas.set_name(name)


def process_frame(frame: np.ndarray):
    """
    Process a numpy array: take the data and convert it into a plot
    :param frame: a numpy array
    """
    global canvas
    canvas.figure.clear()

    # create an axis
    ax1 = canvas.figure.add_subplot(111)

    # convert data to grayscale:
    data = frame.sum(axis=2)

    transform_plot = ax1.imshow(data, cmap='inferno')

    canvas.figure.colorbar(transform_plot)

    # refresh canvas
    canvas.canvas.draw()


def show_window(show: bool = True):
    """
    Show or hide the plugin window
    :param show: True or False
    """
    global canvas
    canvas.show_canvas(show)
