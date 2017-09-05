from PyQt5.QtWidgets import QHBoxLayout, QGroupBox, QSpinBox, QDoubleSpinBox, QWidget, QComboBox

import plugin_canvas
import random
import numpy as np
import plugins.libs.vortex_tools_core as vtc
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt

name = "Fourier Transform"

description = "2D Fourier transformation"

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

    canvas.toolbar.setVisible(False)
    canvas.resize(700, 350)

    canvas.param_layout = QHBoxLayout()
    canvas.parameter_boxes = {}
    for param in ["min_sigma", "max_sigma", "overlap", "threshold"]:
        if param == "min_sigma" or param == "max_sigma":
            spin_box = QSpinBox()
        else:
            spin_box = QDoubleSpinBox()
        canvas.parameter_boxes[param] = spin_box
        group_box = QGroupBox(param)
        layout = QHBoxLayout()
        layout.addWidget(spin_box)
        group_box.setLayout(layout)
        canvas.param_layout.addWidget(group_box)

    combo_box = QComboBox()
    combo_box.addItem("log")
    combo_box.addItem("dog")
    canvas.param_layout.addWidget(combo_box)
    canvas.parameter_boxes["method"] = combo_box

    # default parameters:
    canvas.parameter_boxes["min_sigma"].setValue(8)
    canvas.parameter_boxes["max_sigma"].setValue(17)
    canvas.parameter_boxes["overlap"].setValue(0)
    canvas.parameter_boxes["overlap"].setSingleStep(0.05)
    canvas.parameter_boxes["overlap"].setMaximum(1)
    canvas.parameter_boxes["threshold"].setValue(0.03)
    canvas.parameter_boxes["threshold"].setSingleStep(0.005)
    canvas.parameter_boxes["threshold"].setMaximum(1)
    canvas.parameter_boxes["threshold"].setDecimals(4)
    canvas.parameter_boxes["method"].setCurrentText('log')

    param_widget = QWidget()
    param_widget.setLayout(canvas.param_layout)
    canvas.layout.insertWidget(2, param_widget)


def process_frame(frame: np.ndarray):
    """
    Process a numpy array: take the data and convert it into a plot
    :param frame: a numpy array
    """
    global canvas
    canvas.figure.clear()

    # create an axis
    ax1 = canvas.figure.add_subplot(131)
    ax1.set_title("FFT")
    ax2 = canvas.figure.add_subplot(132)
    ax2.set_title("Inverse transform")
    ax3 = canvas.figure.add_subplot(133)
    ax3.set_title("Phase")

    # convert data to grayscale:
    data = frame.sum(axis=2)

    # calculate and plot transform
    transform, transform_abs = vtc.fourier_transform(data, 300)
    transform_plot = ax1.imshow(transform_abs, norm=LogNorm(vmin=0.01, vmax=transform_abs.max()), cmap='inferno')

    # find blobs
    min_sigma = canvas.parameter_boxes["min_sigma"].value()
    max_sigma = canvas.parameter_boxes["max_sigma"].value()
    overlap = canvas.parameter_boxes["overlap"].value()
    threshold = canvas.parameter_boxes["threshold"].value()
    method = canvas.parameter_boxes["method"].currentText()
    blobs = vtc.find_blobs(transform, max_sigma=max_sigma, min_sigma=min_sigma,
                           overlap=overlap, threshold=threshold, method=method)
    found_blobs = blobs.shape[0] == 3

    print("blobs found:" + str(blobs.shape[0]))
    if 0 < blobs.shape[0] < 30:
        # plot all blobs in blue
        for i in range(blobs.shape[0]):
            circle = plt.Circle((blobs[i, 0], blobs[i, 1]), blobs[i, 2], edgecolor='blue', facecolor="None")
            ax1.add_artist(circle)

    if found_blobs:
        # determine the main blob and plot in green
        main_blob = vtc.pick_blob(blobs)
        circle = plt.Circle((main_blob[0], main_blob[1]), main_blob[2], edgecolor='green', facecolor="None")
        ax1.add_artist(circle)

        # calculate and plot the inverse transform and phase
        shifted_transform = vtc.mask_and_shift(transform, main_blob[0], main_blob[1], main_blob[2])
        backtransform, backtransform_abs, backtransform_phase =\
            vtc.inv_fourier_transform(shifted_transform, main_blob[0], main_blob[1], main_blob[2])

        backtransform_plot = ax2.imshow(backtransform_abs, cmap='gray')
        phase_plot = ax3.imshow(backtransform_phase, cmap='viridis')

    else:
        backtransform_plot = ax2.imshow(np.array([[0, 0], [0, 0]]), cmap='gray')
        phase_plot = ax3.imshow(np.array([[0, 0], [0, 0]]), cmap='viridis')

    # canvas.figure.colorbar(transform_plot)
    # canvas.figure.colorbar(backtransform_plot)
    # canvas.figure.colorbar(phase_plot)

    # refresh canvas
    canvas.canvas.draw()


def show_window(show: bool = True):
    """
    Show or hide the plugin window
    :param show: True or False
    """
    global canvas
    canvas.show_canvas(show)
