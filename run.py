import time
import logging
import asyncio

from skedulord import Job

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
        await asyncio.gather(*[timed_wait(1) for i in range(n)])
    stuff = asyncio.run(collector())
    logging.info(f"scores received {stuff}")


def do_stuff(sec=1):
    time.sleep(sec)
    logging.info(f"slept for {sec}s")


(Job()
 .pipe(do_stuff, sec=0.25)
 .pipe(do_stuff, sec=0.50)
 .pipe(do_many, n=10))
