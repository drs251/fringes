import os

def find_plugins():
    res = []
    for file in os.listdir("./plugins"):
        if file.endswith(".py"):
            plugin = __import__("plugins." + os.path.splitext(file)[0])
            print("imported", plugin)

if __name__ == "__main__":
    find_plugins()
