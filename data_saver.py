import numpy as np
import xarray as xr
import re

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, qDebug
from PyQt5.QtWidgets import QFileDialog


class DataSaver(QObject):

    class SaveNameGenerator(QObject):

        prevNameChanged = pyqtSignal("QString")
        nextNameChanged = pyqtSignal("QString")

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._prev_name = ""
            self._pattern = re.compile(r"^(.*?)(\d+)(.\w+)?$")

        @pyqtProperty("QString", notify=nextNameChanged)
        def next_name(self):
            match = self._pattern.match(self._prev_name)

            if match is not None:
                try:
                    number = match.group(2)
                    new_value = int(number) + 1
                    new_number = str(new_value).zfill(len(number))
                    new_name = self._pattern.sub(r"\1{}\3", self._prev_name).format(new_number)
                except:
                    qDebug("Error generating new file name.")
                    new_name = ""
                qDebug("new name" + new_name)
                return new_name
            else:
                qDebug("returning empty name")
                return ""

        @pyqtSlot(str)
        def set_prev_name(self, name):
            self._prev_name = name

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name_generator = self.SaveNameGenerator()
        self._image_to_save = None
        self._last_image = None

    @pyqtSlot()
    def save_array(self):
        self._image_to_save = self._last_image

        filename, _ = QFileDialog.getSaveFileName(caption="Save image", directory=self.name_generator.next_name,
                                                  filter="netCDF file (*.netcdf)")
        if not filename.endswith(".netcdf"):
            filename += ".netcdf"
        self.name_generator.set_prev_name(filename)

        try:
            xarr = xr.DataArray(self._image_to_save, dims=['x', 'y'])
            xarr.encoding['zlib'] = True
            xarr.to_netcdf(path=filename)
        except ValueError:
            qDebug("Image not saved")


    @pyqtSlot(np.ndarray)
    def set_array(self, array):
        self._last_image = array
