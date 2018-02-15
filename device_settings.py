from abc import ABC, abstractmethod


# an abstract class
class DeviceSettings(ABC):

    # a decorator for easy checking that the device is valid
    # before a function is run
    def _ensure_valid(func):
        def wrapper(self, *args, **kwargs):
            if not self._valid():
                raise RuntimeError("Operation on invalid device!")
            return func(self, *args, **kwargs)

        return wrapper

    def __init__(self):
        self._manualMode = False
        self._active = False

    @abstractmethod
    def _clear_interface(self):
        pass

    @abstractmethod
    def _valid(self):
        pass

    @abstractmethod
    def get_exposure(self):
        pass

    @abstractmethod
    def get_exposure_range(self):
        pass

    @abstractmethod
    def is_auto_exposure(self):
        pass

    @abstractmethod
    def set_auto_exposure(self, auto):
        pass

    @abstractmethod
    def is_auto_gain(self):
        pass

    @abstractmethod
    def set_auto_gain(self, auto):
        pass

    @abstractmethod
    def get_gain(self):
        pass

    @abstractmethod
    def get_gain_range(self):
        pass

    @abstractmethod
    def set_exposure(self, exposure):
        pass

    @abstractmethod
    def set_gain(self, gain):
        pass
