import numpy as np
from PyQt5.QtCore import QObject, QThread

import plugin_canvas

name = "Sum of columns"
description = "A simple demo plugin which sums the columns of pixels"


class MyPlugin(QObject):
    class PlotThread(QThread):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.frame = None

        def run(self):
            # this does the actual plotting without
            # freezing the window

            data = self.frame.sum(0)

            self.parent.ax.cla()

            # plot data
            self.parent.ax.plot(data, '-')
            self.parent.ax.legend(("red", "green", "blue"))

            # refresh canvas
            self.parent.canvas.canvas.draw()

    def __init__(self, parent, send_data_function):
        super().__init__(parent)
        self.plotThread = self.PlotThread(self)
        self.parent = parent
        self.send_data = send_data_function
        self.canvas = plugin_canvas.PluginCanvas(parent, send_data_function)
        self.canvas.set_name(name)

        self.ax = self.canvas.figure.add_subplot(111)

    def process_frame(self, frame):
        if not self.plotThread.isRunning():
            self.plotThread.frame = frame
            self.plotThread.start()


plugin = None


def init(parent=None, send_data_function=None):
    global plugin
    plugin = MyPlugin(parent, send_data_function)


def process_frame(frame: np.ndarray):
    plugin.process_frame(frame)


def show_window(show: bool = True):
    plugin.canvas.show_canvas(show)
