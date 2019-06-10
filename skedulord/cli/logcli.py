import logging
import subprocess

import click
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(message)s',
)
logger = logging.getLogger(__name__)


@click.command()
@click.argument('command')
def main(command):
    logger.info(f"about to run '{command}'")
    output = subprocess.run(command.split(" "),
                            cwd=str(Path().cwd()))
    logger.info(f"done with `{command}` with status code {output.returncode}")


if __name__ == "__main__":
    main()
