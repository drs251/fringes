import win32com.client as com


def get_control():
    return com.Dispatch("IC.ICImagingControl3")

control = get_control()


def clear_interface():
    if control.DeviceValid:
        control.LiveStop()
        control.DeviceFrameFilters.Clear()
    control.Device = ""


def get_devices():
    devices = control.Devices
    count = devices.Count
    res = []
    for i in range(count):
        res.append(devices.Item(i+1))
    return res


def get_unique_name(device):
    _, serial = device.GetSerialNumber()
    name = device.Name
    return name + " " + serial


def print_devices():
    devs = get_devices()
    print("{} devices found:".format(len(devs)))
    for d in devs:
        print("> {}".format(get_unique_name(d)))


def show_dialog():
    control.ShowDeviceSettingsDialog()
    if not control.DeviceValid:
        raise RuntimeError("invalid device")


def is_auto_exposure():
    return control.ExposureAuto


def set_auto_exposure(auto):
    control.ExposureAuto = auto


def is_auto_gain():
    return control.GainAuto


def set_auto_gain(auto):
    control.GainAuto = auto


def get_exposure():
    return control.Exposure


def get_exposure_range():
    return control.ExposureRange


def set_exposure(exposure):
    exposure = int(exposure)
    rng = get_exposure_range()
    if not rng[0] <= exposure <= rng[1]:
        raise ValueError("Exposure parameter {} is outside of allowed range {}".format(exposure, rng))
    set_auto_exposure(False)
    control.Exposure = exposure


def get_gain():
    return control.Gain


def get_gain_range():
    return control.GainRange


def _ensure_valid(func):
    def wrapper(*args, **kwargs):
        print("testing validity")
        if not control.DeviceValid:
            raise Exception("Device invalid")
        func(*args, **kwargs)
    return wrapper


@_ensure_valid
def set_gain(gain):
    gain = int(gain)
    rng = get_gain_range()
    if not rng[0] <= gain <= rng[1]:
        raise ValueError("Gain parameter {} is outside of allowed range {}".format(gain, rng))
    set_auto_gain(False)
    control.Gain = gain


clear_interface()

devs = get_devices()
print_devices()

control.DeviceUniqueName = get_unique_name(devs[0])
print("device valid: {}".format(control.DeviceValid))

#show_dialog()

print("unique name:" + control.DeviceUniqueName)

set_exposure(1)
set_gain(480)
print("gain: {}".format(get_gain()))
print("exposure: {}".format(get_exposure()))
set_exposure(10)
set_gain(3)
print("gain: {}".format(get_gain()))
print("exposure: {}".format(get_exposure()))
set_auto_gain(True)
set_auto_exposure(True)
print("auto gain:", is_auto_gain())
print("auto exposure:", is_auto_exposure())
