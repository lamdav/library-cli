import click

from ...context_extractor import extract_logger, extract_logger_and_client


@click.group()
@click.pass_context
def action(context: click.Context):
    """
    Library Processing Commands.
    """
    logger = extract_logger(context)
    logger.tag = 'ACTION'


@action.command()
@click.argument('username')
@click.argument('isbn')
@click.pass_context
def take(context: click.Context, username: str, isbn: str):
    """
    Borrow a book with isbn under user with username.
    """
    logger, mongo = extract_logger_and_client(context)
    logger.info('Taking book isbn={} for user username={}', isbn, username)


@action.command()
@click.argument('username')
@click.argument('isbn')
@click.pass_context
def give(context: click.Context, username: str, isbn: str):
    """
    Return a book with isbn a user with username has checked out.
    """
    logger, mongo = extract_logger_and_client(context)
    logger.info('Giving book isbn={} for user username={}', isbn, username)
