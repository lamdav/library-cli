import click

from ...context_extractor import extract_logger, extract_logger_and_client


@click.group()
@click.pass_context
def add(context: click.Context):
    """
    Library Add Commands.
    """
    logger = extract_logger(context)
    logger.tag = 'ADD'


@add.command()
@click.argument('title')
@click.argument('author')
@click.argument('isbn')
@click.argument('pages', type=int)
@click.argument('quantity', type=int, default=1)
@click.pass_context
def book(context: click.Context, title: str, author: str, isbn: str, pages: int, quantity: int):
    """
    Add a book to the library.
    """
    logger, mongo = extract_logger_and_client(context)
    logger.info('Adding book title={} author={} isbn={} pages={} quantity={}', title, author, isbn, pages, quantity)


@add.command()
@click.argument('name')
@click.argument('username')
@click.argument('phone', type=int)
@click.pass_context
def user(context: click.Context, name: str, username: str, phone: int):
    """
    Add a user to the library.
    """
    logger, mongo = extract_logger_and_client(context)
    logger.info('Adding user name={} username={} phone={}', name, username, phone)
