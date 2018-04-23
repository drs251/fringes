# Fringes
Image capturing application for interferometry (and more!) written in Python

## Introduction
Fringes was developed to capture and process interferograms specifically for [off-axis digital holography](https://en.wikipedia.org/wiki/Digital_holography), but is extendable via plugins and can be adapted to a variety of tasks (see below). It also can be considered as a smaller, more lightweight alterative to [Micro-Manager](https://micro-manager.org/), which I tried first, but found too difficult to get to work with my Python data analysis code.

Here are some screenshots to illustrate the rough idea:


![main tab](https://github.com/drs251/fringes/blob/master/docs/screenshot1.png)
Main view


![image viewer](https://github.com/drs251/fringes/blob/master/docs/screenshot2.png)
Image viewer with high-pass filter


![fft plugin](https://github.com/drs251/fringes/blob/master/docs/screenshot3.png)
Live 2D Fourier transform and phase extraction


### Hardware compatibility

Fringes should work with pretty much any camera which your operating system can natively recognize, e.g. any camera that can be used as a webcam. However, controlling settings such as exposure time or gain is currently limited to the scientific cameras which I have access to, namely ZWO ASI and The Imaging Source cameras - contributions are highly welcome!

### Functionality
- Main window with zooming, panning and switchable crosshairs for alignment.
- Custom auto-exposure mode that avoids over-saturation.
- High-pass filtering.
- Live 2D Fourier transformation and automatic phase extraction.
- Averaging and sequence recording.
- Data cropping, in order to speed up the plugins.
- Saving images as png or netcdf files - in the latter case, the calibrated x- and y-axis are stored along with the interferogram, if a calibration file is provided

### Extendability

Fringes was written with flexibility in mind. Every tab in the main window is actually a plugin (except main view), and it should be relatively straight-forward to write your own to suit your needs - just use the existing plugins as a template. The advantage of using Python is enabling the user to run the same Python code in a plugin that they will later use for evaluation.


## Installation

Due to the flexible nature of the program, no executables are provided; a Python3 interpreter is required. The Anaconda Python 3.6 distribution is highly recommended, and the following additional packages are needed:
- `pyqtgraph`
- `pywin32` (Windows only, to control The Imaging Source cameras)
- `xarray`

Start the program by typing `python main.py`, or create a shortcut (an icon is provided).

## Acknowledgements

Support of ZWO ASI cameras is accomplished via @stevemarple's excellent [python-zwoasi](https://github.com/stevemarple/python-zwoasi) library.
