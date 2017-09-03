import plugin_canvas
import random
import numpy as np

name = "Demo 2"

description= "Plots the sum of all columns of pixels"

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

    data = frame.sum(0)

    # create an axis
    ax = canvas.figure.add_subplot(111)

    # discards the old graph
    # ax.hold(False)

    # plot data
    ax.plot(data, '-')
    ax.legend(("red", "green", "blue"))

    # refresh canvas
    canvas.canvas.draw()


def show_window(show: bool = True):
    """
    Show or hide the plugin window
    :param show: True or False
    """
    global canvas
    canvas.show_canvas(show)
