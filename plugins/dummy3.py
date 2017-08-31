name = "Dummy 3"

description= "A third dummy plugin"


def init(parent=None, send_data_function=None):
    print("dummy3: init")

def process_frame(frame):
    print("dummy3: process_frame")

def show_window(show: bool = True):
    pass