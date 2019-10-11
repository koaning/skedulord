from functools import reduce

import yaml
import click


def read_settings(*settings_paths):
    configs = [{}]
    for path in settings_paths:
        with open(path, "r") as f:
            configs.append(yaml.safe_load(f))
    return reduce(lambda a, b: a.update(b), configs)


def prefer_kwargs(settings, kwargs):
    return {k: settings[k] if not kwargs[k] else kwargs[k] for k in kwargs}


@click.group()
def main():
    pass


@click.command()
@click.option('--site-name', default=None)
def cmd(**kwargs):
    settings = read_settings("mkdocs.yml")
    settings = prefer_kwargs(settings, kwargs)
    print(settings)


main.add_command(cmd)


if __name__ == "__main__":
    main()
