import sys
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication

import plugin_loader

# https://github.com/rkern/line_profiler
# https://jiffyclub.github.io/snakeviz/
# https://julien.danjou.info/blog/2015/guide-to-python-profiling-cprofile-concrete-case-carbonara
# https://zapier.com/engineering/profiling-python-boss/

app = QApplication(sys.argv)

loader = plugin_loader.PluginLoader()
plugin = loader.plugins.getPlugins()[0]
plugin.active = True

for _ in range(10):
    image = QImage(1280, 720, QImage.Format_RGB32)
    plugin.processImage(image)
