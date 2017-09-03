name = "Demo 3"

description= "An empty demo plugin"


def init(parent=None, send_data_function=None):
    print("dummy3: init")

def process_frame(frame):
    print("dummy3: process_frame")

def show_window(show: bool = True):
    pass