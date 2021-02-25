import typer
import time


def printing(**kwargs):
    for i in range(5):
        time.sleep(0.23)
        print(f"i am at iteration {i}")


if __name__ == "__main__":
    typer.run(printing)
