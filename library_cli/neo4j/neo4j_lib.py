import click
from neo4j.v1 import GraphDatabase, basic_auth

from .neo4j_api import Neo4jAPI
from ..command.action.action import action
from ..command.adder.adder import add
from ..command.deleter.deleter import delete
from ..command.editor.editor import edit
from ..command.remover.remover import remove
from ..command.searcher.searcher import search
from ..command.sorter.sorter import sort
from ..command.stat.stat import stat
from ..context_extractor import extract_api
from ..logger import Logger


@click.group()
@click.pass_context
def cli(context: click.Context):
    """
    Neo4j Library Client Implementation.
    """
    logger = Logger()
    uri = 'bolt://localhost:7687'
    client = GraphDatabase().driver(uri, auth=basic_auth('neo4j', 'csse433'))

    api = Neo4jAPI(client, logger)
    context.obj = {
        'api': api
    }


@cli.command()
@click.argument('username')
@click.argument('isbn')
@click.argument('score', type=click.IntRange(min=1, max=5))
@click.pass_context
def rate(context: click.Context, username: str, isbn: str, score=int):
    """
    Rate a book with the given isbn with the score as the user with username.
    """
    api = extract_api(context)
    api.log_tag('RATE')
    exit(0) if api.rate_book(username, isbn, score) else exit(1)


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
cli.add_command(delete)
