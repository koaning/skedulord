import time
from rich.console import Console

console = Console(log_path=False)

if __name__ == "__main__":
    for i in range(7):
        time.sleep(0.23)
        console.log(f"i am at iteration {i}")
        console.log({c: i for c in "abcdefghjkl"})
