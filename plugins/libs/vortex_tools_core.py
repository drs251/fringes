import numpy as np
import scipy.fftpack as fftpack
from skimage.feature import blob_dog, blob_log


def fourier_transform(image, transform_size=200):
    """
    Calculates the Fourier transform of a 2D numpy array and returns another numpy array containing the
    absolute value with logarithmic scaling.

    :param image: 2D numpy array to be Fourier transformed
    :param transform_size: Size to which the transform is cut. Defaults to 200, cutting can be avoided by setting
    transform_size=0.
    :return: tuple of complex transform and power spectrum of transform (2d numpy arrays)
    """
    transform = fftpack.fft2(image)
    transform = fftpack.fftshift(transform)

    if transform_size != 0:
        transform_size = int(transform_size / 2)
        cx = int((transform.shape[0] + 1) / 2)
        cy = int((transform.shape[1] + 1) / 2)
        transform = transform[cx - transform_size: cx + transform_size,
                              cy - transform_size: cy + transform_size]

    transform_abs = np.abs(transform) ** 2
    return transform, transform_abs


def inv_fourier_transform(image):
    """
    Calculates the inverse Fourier transform of a 2D numpy array and returns numpy arrays with the transform, the
    absolute value and the phase of the transform

    :param image: numpy array containing the data to be transformed
    :return: A tuple of three 2D numpy arrays containing the complex transform, the absolute value of the transform and
    the phase of the transform in units of pi
    """
    transform = fftpack.ifftshift(image)
    transform = fftpack.ifft2(transform)
    transform_abs = np.abs(transform)
    transform_phase = np.angle(transform) / np.pi

    return transform, transform_abs, transform_phase


def plot_rgb_phases(absolute, phase):
    """
    Calculates a visualization of an inverse Fourier transform, where the absolute value is plotted as brightness
    and the phase is plotted as color.

    :param absolute: 2D numpy array containing the absolute value
    :param phase: 2D numpy array containing phase information in units of pi (should range from -1 to +1!)
    :return: numpy array containing red, green and blue values
    """
    red = 0.5 * (np.sin(phase * np.pi) + 1) * absolute / absolute.max()
    green = 0.5 * (np.sin(phase * np.pi + 2 / 3 * np.pi) + 1) * absolute / absolute.max()
    blue = 0.5 * (np.sin(phase * np.pi + 4 / 3 * np.pi) + 1) * absolute / absolute.max()
    return np.dstack([red, green, blue])


def roll_to_center(raw_transform, xc, yc):
    """
    Shifts ("rolls") a two-dimensional numpy array so that the given coordinate will be in the center. Pixels
    shifted over the edge re-appear on the other side

    :param raw_transform: A numpy array to be shifted
    :param xc: current x position in pixels
    :param yc: current y position in pixels
    :return: Shifted numpy array
    """
    (xs, ys) = raw_transform.shape
    dx = int(xs / 2 - xc)
    dy = int(ys / 2 - yc)
    rolled = np.roll(raw_transform, shift=dx, axis=0)
    rolled = np.roll(rolled, shift=dy, axis=1)
    return rolled


# perhaps make and option to use smooth (intepolated) shifting and use it for extracting the phase
def shift_to_center(raw_transform, xc, yc):
    """
    Destructively shifts a two-dimensional numpy array so that the given coordinate will be in the center. Pixels
    shifted over the edge are gone forever.

    :param raw_transform: A numpy array to be shifted
    :param xc: current x position in pixels
    :param yc: current y position in pixels
    :return: Shifted numpy array
    """
    (xs, ys) = raw_transform.shape
    dx = int(xs / 2 - xc)
    dy = int(ys / 2 - yc)
    rolled = np.roll(raw_transform, shift=dx, axis=0)
    rolled[0:dx, :] = 0
    rolled = np.roll(rolled, shift=dy, axis=1)
    rolled[:, 0:dy] = 0

    return rolled


def shift(raw_transform, dx, dy):
    """
    Destructively shifts a two-dimensional numpy array so that the given coordinate will be in the center. Pixels
    shifted over the edge are gone forever.

    :param raw_transform: A numpy array to be shifted
    :param dx: x shift
    :param dy: y shift
    :return: Shifted numpy array
    """
    rolled = np.roll(raw_transform, shift=dx, axis=0)
    if dx >= 0:
        rolled[0:dx, :] = 0
    else:
        rolled[dx:-1, :] = 0
    rolled = np.roll(rolled, shift=dy, axis=1)
    if dy >= 0:
        rolled[:, 0:dy] = 0
    else:
        rolled[:, dy:-1] = 0

    return rolled


def pick_blob(blobs, pick_opposite=False):
    """
    Picks one of the outer blob of three blobs in a Fourier transform.

    :param blobs: Array of blob coordinates, as returned by find_blobs
    :param pick_opposite: If set to True, the other outer blob will be returned. (Default: False)
    :return: Coordinates [x, y, r] of the correct blob
    """
    blob_coords = blobs[:, 0:2]
    blob_coords_rolled = np.roll(blob_coords, 1, 0)
    sums = np.sum(np.abs(blob_coords - blob_coords_rolled), 0)
    if sums[0] > sums[1]:  # if the blobs are lined up more vertically:
        if pick_opposite:
            index = blob_coords[:, 0].argmax(axis=0)
        else:
            index = blob_coords[:, 0].argmin(axis=0)
    else:  # they're aligned more horizontally:
        if pick_opposite:
            index = blob_coords[:, 1].argmax(axis=0)
        else:
            index = blob_coords[:, 1].argmin(axis=0)
    return blobs[index]


def find_blobs(transform, min_sigma=8, max_sigma=17, overlap=0.,
               threshold=0.03, method='log'):
    """
    Finds blobs in a Fourier transform and returns their coordinates

    :param transform: Complex numpy array containing a Fourier transform or real array assumed to contain the log of a FFT
    :param max_sigma: Largest blob size (Default: 15)
    :param min_sigma: Smallest blob size (Default: 10)
    :param overlap: Maximum allowed overlap fraction between two blobs (Default: 0.2)
    :param threshold: Minimum threshold, defined as fraction between the lowest and highest absolute value of the points
    in the transform
    :param method: Peak finding method: 'log' for Laplacian of Gaussians, 'dog' for Difference of Gaussians
    (Default: 'log')
    :return: Array of [x, y, r] for each blob
    """
    if np.iscomplexobj(transform):
        transform_log = np.nan_to_num(np.log(np.abs(transform)))
    else:
        transform_log = transform

    threshold = transform_log.ptp() * threshold + transform_log.min()

    if method == 'log':
        method = blob_log
    elif method == 'dog':
        method = blob_dog
    else:
        raise Exception("Bad method '{}'. Use 'log' or 'dog'.")

    blobs = method(transform_log, max_sigma=max_sigma, min_sigma=min_sigma,
                   threshold=threshold, overlap=overlap)
    blobs[:, 2] = blobs[:, 2] * np.sqrt(2)

    return blobs


def find_3_blobs(transform, min_sigma=8, max_sigma=17, overlap=0.,
                 threshold=0.5, method='log'):
    """
    Attempts to find the three strongest blobs in a Fourier transform and returns their coordinates

    :param transform: Complex numpy array containing a Fourier transform or real array assumed to contain the log of a FFT
    :param max_sigma: Largest blob size (Default: 15)
    :param min_sigma: Smallest blob size (Default: 10)
    :param overlap: Maximum allowed overlap fraction between two blobs (Default: 0.2)
    :param threshold: Starting point for the automatically adjusted threshold, defined as fraction between the lowest
    and highest absolute value of the points in the transform
    :param method: Peak finding method: 'log' for Laplacian of Gaussians, 'dog' for Difference of Gaussians
    (Default: 'log')
    :return: Array of [x, y, r] for each blob
    """
    if np.iscomplexobj(transform):
        transform_log = np.nan_to_num(np.log(np.abs(transform)))
    else:
        transform_log = transform

    # try to find 3 or more blobs by decreasing the threshold until it's 0.001
    blobs = np.zeros((0, 3))
    divisor = np.power(10., 1/3)
    while blobs.shape[0] < 3 and threshold > 0.001:
        blobs = find_blobs(transform, min_sigma, max_sigma, overlap, threshold, method)
        threshold /= divisor
    if blobs.shape[0] <= 3:
        return blobs

    # calculate the integral and return the three most intense blobs
    blob_dict = {}
    for blob in np.vsplit(blobs, blobs.shape[0]):
        blob = blob.reshape(3)
        integral = np.sum(apply_mask(transform, blob[0], blob[1], blob[2]))
        blob_dict[integral] = blob
    ret_blobs = []
    for key in sorted(blob_dict.keys())[0:3]:
        ret_blobs.append(blob_dict[key])
    return np.array(ret_blobs)


def apply_mask(transform, x, y, radius):
    """
    Applies a circular mask to a numpy array

    :param transform: Numpy array
    :param x: center in x
    :param y: center in y
    :param radius: blob radius (is multiplied by a factor of 1.2)
    :return: Masked array
    """
    trans_data = transform.copy()
    lx, ly = trans_data.shape
    xx, yy = np.ogrid[0:lx, 0:ly]
    mask = (xx - x) ** 2 + (yy - y) ** 2 > (radius * 1.2) ** 2
    trans_data[mask] = 0

    return trans_data


def mask_and_shift(transform, x, y, radius):
    """
    Combination of apply_mask and roll_to_center

    :param transform: Numpy array
    :param x: center in x
    :param y: center in y
    :param radius: blob radius
    :return: Masked and shifted numpy array
    """
    transform = apply_mask(transform, x, y, radius)
    transform = roll_to_center(transform, x, y)

    return transform


def extract_phase(interferogram, min_sigma=8, max_sigma=17, overlap=0,
                  threshold=0.03, method='log', transform_size=200):
    """
    Extracts the phase of an interferogram by calculating the Fourier transform, shifting the outer blob to the center
    of the frequency space and performing an inverse Fourier transform. The blob is found automatically. Returns a
    report showing the Fourier transform with the found blobs, as well as a HoloMap containing the inverse
    transform.

    :param interferogram: numpy array containing an interferogram
    :param min_sigma: For find_blobs
    :param max_sigma: For find_blobs
    :param overlap: For find_blobs
    :param threshold: For find_blob
    :param method: Peak finding method: 'log' for Laplacian of Gaussians, 'dog' for Difference of Gaussians
    (Default: 'log')
    :param transform_size: Size in pixels that the Fourier transform should be clipped to
    :return: Tuple of the inverse Fourier transform and the main blob coordinates as (x, y, radius)
    """

    transform, transform_abs = fourier_transform(interferogram, transform_size=transform_size)

    # find and plot blobs
    blobs = find_blobs(transform, max_sigma=max_sigma, min_sigma=min_sigma,
                       overlap=overlap, threshold=threshold, method=method)

    if not blobs.shape[0] == 3:
        raise Exception("Error: found {} blobs instead of 3!".format(blobs.shape[0]))

    main_blob = pick_blob(blobs)

    shifted_transform = mask_and_shift(transform, main_blob[0], main_blob[1], main_blob[2])

    return inv_fourier_transform(shifted_transform), main_blob


def gauss(x, a, sigma, mux=0):
    """
    A gaussian

    :param x: x coordinates
    :param a: amplitude
    :param sigma: width
    :param mux: center (Default: 0)
    :return: Numpy array
    """
    return a * np.exp(-(x - mux) ** 2 / (2. * sigma ** 2))


def gauss2d(x, y, a, sigma, mx=0, my=0):
    """
    A 2d gaussian

    :param x: x coordinates
    :param y: y coordinates
    :param a: amplitude
    :param sigma: width
    :param mx: center in x (Default: 0)
    :param my: center in y (Default: 0)
    :return: Numpy array
    """
    return a * np.exp(-((x - mx) ** 2 + (y - my) ** 2) / (2. * sigma ** 2))
