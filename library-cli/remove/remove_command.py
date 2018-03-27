import click

class Config(object):
    def __init__(self):
        pass
config = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Print all logs')
@config
def remove(config, verbose):
    _setup_config(config, verbose)
