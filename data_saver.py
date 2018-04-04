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
        self.prev_name = ""
        self._pattern = re.compile(r"^(.*?)(\d+)(.\w+)?$")

    @pyqtProperty("QString", notify=nextNameChanged)
    def next_name(self):
        match = self._pattern.match(self.prev_name)

        if match is not None:
            try:
                number = match.group(2)
                new_value = int(number) + 1
                new_number = str(new_value).zfill(len(number))
                new_name = self._pattern.sub(r"\1{}\3", self.prev_name).format(new_number)
            except:
                qDebug("Error generating new file name.")
                new_name = ""
            return new_name
        else:
            return ""


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
        name = self.name_generator.next_name
        if self.name_generator.prev_name.endswith(".png"):
            file_filter = "{};;{}".format(filter_png, filter_netcdf)
        else:
            file_filter = "{};;{}".format(filter_netcdf, filter_png)
        filename, file_filter = QFileDialog.getSaveFileName(caption="Save image", directory=name,
                                                            filter=file_filter,
                                                            options=QFileDialog.DontUseNativeDialog)
        try:
            if filename == "":
                raise ValueError()
            if file_filter == filter_netcdf:
                if not filename.endswith(".nc"):
                    filename += ".nc"

                xarr = xarray_from_frame(self._image_to_save)
                if os.path.isfile(filename):
                    os.remove(filename)
                xarr.to_netcdf(path=filename)
            elif file_filter == filter_png:
                if not filename.endswith(".png"):
                    filename += ".png"
                if os.path.isfile(filename):
                    os.remove(filename)
                imsave(filename, self._image_to_save)
            else:
                raise ValueError()

            self.name_generator.prev_name = filename
            self.message.emit("{} successfully saved.".format(filename))

        except ValueError as err:
            self.message.emit("Image not saved: {}".format(str(err)))

    @pyqtSlot(np.ndarray)
    def set_array(self, array):
        self._last_image = array


def xarray_from_frame(frame):
    # if there is a calibration file, add calibrated coordinates
    try:
        with open("calibration.txt", "r", encoding="utf-8") as file:
            px_per_unit = float(file.readline().strip())
            unit = file.readline().strip()
            ly, lx = frame.shape
            x_span = lx / px_per_unit / 2
            y_span = ly / px_per_unit / 2
            x_coords = np.linspace(-x_span, x_span, lx)
            y_coords = np.linspace(-y_span, y_span, ly)[::-1]
            xarr = xr.DataArray(frame, coords=[("y", y_coords), ("x", x_coords)], name="intensity")
            xarr.x.attrs["units"] = unit
            xarr.y.attrs["units"] = unit
    except FileNotFoundError:
        print("Calibration file not found", sys.stderr)
        xarr = xr.DataArray(frame, dims=["x", "y"], name="intensity")
    xarr.attrs["units"] = "arb. u."
    xarr.attrs["time"] = datetime.datetime.now().isoformat()
    xarr.encoding['zlib'] = True
    return xarr
