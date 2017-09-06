import sys, time

from PyQt5.QtCore import QTimer, QObject
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication

import numpy as np
from scipy.misc.pilutil import toimage
from PIL. ImageQt import ImageQt

import plugin_loader


# https://github.com/rkern/line_profiler
# https://jiffyclub.github.io/snakeviz/
# https://julien.danjou.info/blog/2015/guide-to-python-profiling-cprofile-concrete-case-carbonara
# https://zapier.com/engineering/profiling-python-boss/


app = QApplication(sys.argv)

loader = plugin_loader.PluginLoader()
plugin = loader.plugins.getPlugins()[5]
plugin.active = True

image_width = 1280
image_height = 720
np_image = np.random.rand(image_height, image_width, 3)
q_image = ImageQt(toimage(np_image))

class Runner(QObject):

    def __init__(self):
        super().__init__(None)
        self._running = False

    def run(self):
        if not self._running:
            self._running = True
            np_image = np.random.rand(image_height, image_width, 3)
            q_image = ImageQt(toimage(np_image))
            start = time.time()
            plugin.processImage(q_image)
            end = time.time()
            print("time for one process: " + str(end-start))
        self._running = False

timer = QTimer()
runner = Runner()
timer.timeout.connect(runner.run)
timer.start(100)
app.exec_()

# initial version of fourier2d takes 0.9-1.0 s for 1280x720
