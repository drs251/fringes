import plugin_canvas
import random

name = "Dummy 1"

description= "A dummy plugin"

canvas = None


def init(parent=None):
    global canvas
    canvas = plugin_canvas.PluginCanvas(parent)
    canvas.set_name(name)
    return
    # process_frame(None)
    # canvas.show_canvas()


def process_frame(frame):
    ''' plot some random stuff '''
    # random data
    data = [random.random() for i in range(10)]

    # create an axis
    ax = canvas.figure.add_subplot(111)

    # discards the old graph
    # ax.hold(False)

    # plot data
    ax.plot(data, '*-')

    # refresh canvas
    canvas.canvas.draw()

    canvas.show_canvas()
