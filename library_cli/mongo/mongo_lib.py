import click
from pymongo import MongoClient

from .action.action import action
from .adder.adder import add
from .editor.editor import edit
from .remover.remover import remove
from .searcher.searcher import search
from .sorter.sorter import sort
from .stat.stat import stat
from ..logger import Logger


@click.group()
@click.pass_context
def cli(context: click.Context):
    """
    Mongo Library Client Implementation.
    """
    context.obj = {
        'logger': Logger(),
        'client': MongoClient()
    }


@cli.command()
@click.argument('arguments', nargs=-1, required=False)
def echo(arguments: tuple):
    """
    Echo arguments back.
    """
    click.secho(' '.join(arguments), fg='yellow')


cli.add_command(add)
cli.add_command(remove)
cli.add_command(edit)
cli.add_command(search)
cli.add_command(sort)
cli.add_command(action)
cli.add_command(stat)
