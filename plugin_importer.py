import os
import importlib
import collections

plugin_folder = "plugins"


def find_plugins():
    plugins = collections.OrderedDict()
    print(os.getcwd())
    for file in os.listdir("./" + plugin_folder):
        if file.endswith(".py"):
            name = os.path.splitext(file)[0]
            plugin = importlib.import_module(plugin_folder + "." + name)
            if plugin is None:
                continue
            try:
                plugins[name] = plugin.process_frame
            except AttributeError:
                pass

    return plugins


if __name__ == "__main__":
    my_plugins = find_plugins()
    print(my_plugins)
    for name, plugin in my_plugins.items():
        plugin(None)
