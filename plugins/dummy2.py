name = "Dummy 2"

description= "Another dummy plugin"


def init(parent=None, send_data_function=None):
    print("dummy2: init")

def process_frame(frame):
    print("dummy2: process_frame")

def show_window(show: bool = True):
    pass