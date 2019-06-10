import click


@click.group()
def main():
    pass


@click.command()
@click.option('--name', prompt='what is your name')
@click.option('--server', prompt='what is your server')
@click.option('--ip', prompt='what is your ip')
def setup(name, server, ip):
    settings = {"name": name, "server": server, "ip": ip}
    click.echo(f"name: {name} - server: {server} - ip: {ip}")


main.add_command(setup)

if __name__ == "__main__":
    main()
