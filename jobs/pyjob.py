import time


if __name__ == "__main__":
    for i in range(7):
        time.sleep(0.23)
        print({"iteration": i})
        print({c: i for c in "abcd"})
