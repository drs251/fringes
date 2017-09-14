from PyQt5.QtCore import QThread, QObject
from PyQt5.QtWidgets import QHBoxLayout, QGroupBox, QSpinBox, QDoubleSpinBox, QWidget, QComboBox, QLabel
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt

import plugin_canvas_pyqtgraph
import plugins.libs.vortex_tools_core as vtc



name = "Fourier Transform 2"
description = "2D Fourier transformation with pyqtgraph"


def plotCircle(handle, origin, radius, color=(0, 0, 255)):
    phi = np.linspace(0, 2 * np.pi, 30)
    x = np.sin(phi) * radius + origin[0]
    y = np.cos(phi) * radius + origin[1]
    return handle.plot(x, y, pen=pg.mkPen(color=color, width=2))


def generatePgColormap(cm_name):
    pltMap = plt.get_cmap(cm_name)
    colors = pltMap.colors
    colors = [c + [1.] for c in colors]
    positions = np.linspace(0, 1, len(colors))
    pgMap = pg.ColorMap(positions, colors)
    return pgMap


class FFTPlugin2(QObject):
    # class PlotThread(QThread):
    #     def __init__(self, parent):
    #         super().__init__(parent)
    #         self.parent = parent
    #         self.frame = None
    #
    #     def run(self):
    #         # make life easier by copying some names:
    #         fftimage = self.parent.fftimage
    #         transformimage = self.parent.transformimage
    #         phaseimage = self.parent.phaseimage
    #         layoutWidget = self.parent.layoutWidget
    #
    #         # get rid of old cirles
    #         for circle in self.parent.circle_plots:
    #             #layoutWidget.removeItem(circle)
    #             pass
    #         self.parent.circle_plots = []
    #
    #         # convert data to grayscale:
    #         data = self.frame.sum(axis=2).astype(np.float64)
    #
    #         # apply window function to get rid of artifacts:
    #         width, height = data.shape
    #         window = np.outer(np.hanning(width), np.hanning(height))
    #         data *= window
    #
    #         # calculate and plot transform
    #         transform, transform_abs = vtc.fourier_transform(data, 300)
    #         # transform_plot = self.parent.ax1.imshow(transform_abs, norm=LogNorm(vmin=0.01,
    #         #                                                                     vmax=transform_abs.max()),
    #         #                                  cmap='inferno')
    #         fftimage.setImage(np.log(transform_abs))
    #
    #         # find blobs
    #         min_sigma = self.parent.parameter_boxes["min_sigma"].value()
    #         max_sigma = self.parent.parameter_boxes["max_sigma"].value()
    #         overlap = self.parent.parameter_boxes["overlap"].value()
    #         threshold = self.parent.parameter_boxes["threshold"].value()
    #         method = self.parent.parameter_boxes["method"].currentText()
    #         blobs = vtc.find_blobs(transform, max_sigma=max_sigma, min_sigma=min_sigma,
    #                                overlap=overlap, threshold=threshold, method=method)
    #         self.parent.blob_label.setText("Blobs found: {}".format(blobs.shape[0]))
    #         found_3_blobs = blobs.shape[0] == 3
    #
    #         # if it's not too many, plot all blobs in blue:
    #         if 0 < blobs.shape[0] < 30:
    #             for i in range(blobs.shape[0]):
    #                 #circle = plt.Circle((blobs[i, 1], blobs[i, 0]), blobs[i, 2], edgecolor='blue', facecolor="None")
    #                 #self.parent.ax1.add_artist(circle)
    #                 circle = plotCircle(self.parent.fftplot, (blobs[i, 0], blobs[i, 1]), blobs[i, 2])
    #                 self.parent.circle_plots.append(circle)
    #
    #         if found_3_blobs:
    #             # determine the main blob and plot in green
    #             main_blob = vtc.pick_blob(blobs)
    #             #circle = plt.Circle((main_blob[1], main_blob[0]), main_blob[2], edgecolor='green', facecolor="None")
    #             #self.parent.ax1.add_artist(circle)
    #             circle = plotCircle(self.parent.fftplot, (main_blob[0], main_blob[1]), main_blob[2], (0, 255, 0))
    #             self.parent.circle_plots.append(circle)
    #
    #             # calculate and plot the inverse transform and phase
    #             shifted_transform = vtc.mask_and_shift(transform, main_blob[0], main_blob[1], main_blob[2])
    #             backtransform, backtransform_abs, backtransform_phase = vtc.inv_fourier_transform(shifted_transform)
    #
    #             transformimage.setImage(backtransform_abs)
    #             phaseimage.setImage(backtransform_phase)
    #
    #         else:
    #             transformimage.setImage()
    #             phaseimage.setImage()


    def __init__(self, parent, send_data_function):
        super().__init__(parent)
        self.parameter_boxes = {}

        #self.plotThread = self.PlotThread(self)

        self.parent = parent
        self.send_data = send_data_function

        self.canvas = plugin_canvas_pyqtgraph.PluginCanvasPyqtgraph(parent, send_data_function)
        self.canvas.set_name(name)
        self.canvas.resize(700, 350)
        self.layoutWidget = self.canvas.layoutWidget

        # make fields to enter parameters:
        self.canvas.param_layout = QHBoxLayout()
        self.canvas.parameter_boxes = {}
        for param in ["min_sigma", "max_sigma", "overlap", "threshold"]:
            if param == "min_sigma" or param == "max_sigma":
                spin_box = QSpinBox()
            else:
                spin_box = QDoubleSpinBox()
            self.parameter_boxes[param] = spin_box
            group_box = QGroupBox(param)
            layout = QHBoxLayout()
            layout.addWidget(spin_box)
            group_box.setLayout(layout)
            self.canvas.param_layout.addWidget(group_box)

        combo_box = QComboBox()
        combo_box.addItem("log")
        combo_box.addItem("dog")
        self.canvas.param_layout.addWidget(combo_box)
        self.parameter_boxes["method"] = combo_box

        # default parameters:
        self.parameter_boxes["min_sigma"].setValue(8)
        self.parameter_boxes["max_sigma"].setValue(17)
        self.parameter_boxes["overlap"].setValue(0)
        self.parameter_boxes["overlap"].setSingleStep(0.05)
        self.parameter_boxes["overlap"].setMaximum(1)
        self.parameter_boxes["threshold"].setValue(0.03)
        self.parameter_boxes["threshold"].setSingleStep(0.005)
        self.parameter_boxes["threshold"].setMaximum(1)
        self.parameter_boxes["threshold"].setDecimals(4)
        self.parameter_boxes["method"].setCurrentText('log')

        param_widget = QWidget()
        param_widget.setLayout(self.canvas.param_layout)
        self.canvas.layout.insertWidget(1, param_widget)

        self.blob_label = QLabel("Blobs found: #")
        self.canvas.layout.insertWidget(2, self.blob_label)

        # some image plots:

        viridis = generatePgColormap('viridis')
        inferno = generatePgColormap('inferno')

        self.fftplot = self.layoutWidget.addPlot(title="FFT")
        self.fftplot.setAspectLocked()
        self.fftplot.showAxis('bottom', False)
        self.fftplot.showAxis('left', False)
        self.fftimage = pg.ImageItem(lut=inferno.getLookupTable())
        self.fftplot.addItem(self.fftimage)

        self.transformplot = self.layoutWidget.addPlot(title="Inverse transform")
        self.transformplot.setAspectLocked()
        self.transformplot.showAxis('bottom', False)
        self.transformplot.showAxis('left', False)
        self.transformimage = pg.ImageItem()
        self.transformplot.addItem(self.transformimage)

        self.phaseplot = self.layoutWidget.addPlot(title="Phase")
        self.phaseplot.setAspectLocked()
        self.phaseplot.showAxis('bottom', False)
        self.phaseplot.showAxis('left', False)
        self.phaseimage = pg.ImageItem(lut=viridis.getLookupTable())
        self.phaseplot.addItem(self.phaseimage)

        self.circle_plots = []

    def process_frame(self, frame: np.ndarray):
        # get rid of old cirles
        for circle in self.circle_plots:
            # layoutWidget.removeItem(circle)
            pass
        self.circle_plots = []

        # convert data to grayscale:
        data = frame.sum(axis=2).astype(np.float64)

        # apply window function to get rid of artifacts:
        width, height = data.shape
        window = np.outer(np.hanning(width), np.hanning(height))
        data *= window

        # calculate and plot transform
        transform, transform_abs = vtc.fourier_transform(data, 300)
        # transform_plot = self.parent.ax1.imshow(transform_abs, norm=LogNorm(vmin=0.01,
        #                                                                     vmax=transform_abs.max()),
        #                                  cmap='inferno')
        self.fftimage.setImage(np.log(transform_abs))

        # find blobs
        min_sigma = self.parameter_boxes["min_sigma"].value()
        max_sigma = self.parameter_boxes["max_sigma"].value()
        overlap = self.parameter_boxes["overlap"].value()
        threshold = self.parameter_boxes["threshold"].value()
        method = self.parameter_boxes["method"].currentText()
        blobs = vtc.find_blobs(transform, max_sigma=max_sigma, min_sigma=min_sigma,
                               overlap=overlap, threshold=threshold, method=method)
        self.blob_label.setText("Blobs found: {}".format(blobs.shape[0]))
        found_3_blobs = blobs.shape[0] == 3

        # if it's not too many, plot all blobs in blue:
        if 0 < blobs.shape[0] < 30:
            for i in range(blobs.shape[0]):
                # circle = plt.Circle((blobs[i, 1], blobs[i, 0]), blobs[i, 2], edgecolor='blue', facecolor="None")
                # self.parent.ax1.add_artist(circle)
                circle = plotCircle(self.fftplot, (blobs[i, 0], blobs[i, 1]), blobs[i, 2])
                self.circle_plots.append(circle)

        if found_3_blobs:
            # determine the main blob and plot in green
            main_blob = vtc.pick_blob(blobs)
            # circle = plt.Circle((main_blob[1], main_blob[0]), main_blob[2], edgecolor='green', facecolor="None")
            # self.parent.ax1.add_artist(circle)
            circle = plotCircle(self.fftplot, (main_blob[0], main_blob[1]), main_blob[2], (0, 255, 0))
            self.circle_plots.append(circle)

            # calculate and plot the inverse transform and phase
            shifted_transform = vtc.mask_and_shift(transform, main_blob[0], main_blob[1], main_blob[2])
            backtransform, backtransform_abs, backtransform_phase = vtc.inv_fourier_transform(shifted_transform)

            self.transformimage.setImage(backtransform_abs)
            self.phaseimage.setImage(backtransform_phase)

        else:
            self.transformimage.setImage()
            self.phaseimage.setImage()


plugin = None


def init(parent=None, send_data_function=None):
    """
    Initialize the plugin. Build the window and create any necessary variables
    :param parent: The main window can be provided here
    :param send_data_function: A function that can start or stop data being sent
    """
    global plugin
    plugin = FFTPlugin2(parent, send_data_function)


def process_frame(frame: np.ndarray):
    """
    Process a numpy array: take the data and convert it into a plot
    :param frame: a numpy array
    """
    plugin.process_frame(frame)



def show_window(show: bool = True):
    """
    Show or hide the plugin window
    :param show: True or False
    """
    plugin.canvas.show_canvas(show)
