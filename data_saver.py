import datetime
import numpy as np
import sys
import xarray as xr
import re
import os
from scipy.misc import imsave

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, qDebug
from PyQt5.QtWidgets import QFileDialog


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
            return new_name
        else:
            return ""

    @pyqtSlot(str)
    def set_prev_name(self, name):
        self._prev_name = name


class DataSaver(QObject):

    message = pyqtSignal(str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name_generator = SaveNameGenerator()
        self._image_to_save = None
        self._last_image = None

    @pyqtSlot()
    def save_image(self):
        self._image_to_save = self._last_image

        filter_netcdf = "netCDF file (*.nc)"
        filter_png = "png file (*.png)"
        filename, filter = QFileDialog.getSaveFileName(caption="Save image", directory=self.name_generator.next_name,
                                                       filter="{};;{}".format(filter_netcdf, filter_png),
                                                       options=QFileDialog.DontUseNativeDialog)
        try:
            if filename == "":
                raise ValueError()
            if filter == filter_netcdf:
                if not filename.endswith(".nc"):
                    filename += ".nc"

                xarr = xarray_from_frame(self._image_to_save)
                if os.path.isfile(filename):
                    os.remove(filename)
                xarr.to_netcdf(path=filename)
            elif filter == filter_png:
                if not filename.endswith(".png"):
                    filename += ".png"
                if os.path.isfile(filename):
                    os.remove(filename)
                imsave(filename, self._image_to_save)
            else:
                raise ValueError()

            self.name_generator.set_prev_name(filename)
            self.message.emit("{} successfully saved.".format(filename))

        except ValueError:
            self.message.emit("Image not saved")

    @pyqtSlot(np.ndarray)
    def set_array(self, array):
        self._last_image = array


def xarray_from_frame(frame):
    xarr = xr.DataArray(frame, dims=["y", "x"], name="intensity")
    xarr.attrs["units"] = "arb. u."
    xarr.attrs["time"] = datetime.datetime.now().isoformat()
    xarr.encoding['zlib'] = True
    # if there is a calibration file, add calibrated coordinates
    try:
        with open("calibration.txt", "r") as file:
            px_per_unit = float(file.readline().strip())
            unit = file.readline().strip()
            ly, lx = frame.shape
            x_span = lx / px_per_unit / 2
            y_span = ly / px_per_unit / 2
            x_coords = np.linspace(-x_span, x_span, lx)
            y_coords = np.linspace(-y_span, y_span, ly)[::-1]
            xarr.coords["x_pos"] = ("x", x_coords)
            xarr.x_pos.attrs["units"] = unit
            xarr.coords["y_pos"] = ("y", y_coords)
            xarr.y_pos.attrs["units"] = unit
            xarr = xarr.swap_dims({"x": "x_pos", "y": "y_pos"})
    except FileNotFoundError:
        print("Calibration file not found", sys.stderr)
    return xarr
