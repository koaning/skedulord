import time
import logging
import asyncio

from skedulord.job import JobRunner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def timed_wait(sec):
    await asyncio.sleep(sec)
    logging.info(f"slept for {sec}s")
    return sec


def do_many(n):
    async def collector():
        await asyncio.gather(*[timed_wait(0.1) for _ in range(n)])
    stuff = asyncio.run(collector())
    logging.info(f"scores received {stuff}")


def do_stuff(sec=1):
    time.sleep(sec)
    logging.info(f"slept for {sec}s")


if __name__ == "__main__":
    (JobRunner()
     .run(do_stuff, sec=0.1)
     .run(do_many, n=10)
     .run(do_stuff, sec=0.1)
     .run())
