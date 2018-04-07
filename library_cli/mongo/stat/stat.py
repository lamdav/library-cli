import click

from ...context_extractor import extract_logger, extract_logger_and_client


@click.group()
@click.pass_context
def stat(context: click.Context):
    """
    Library Stats Commands.
    """
    logger = extract_logger(context)
    logger.tag = 'STAT'


@stat.command()
@click.argument('isbn')
@click.pass_context
def book(context: click.Context, isbn: str):
    """
    Statistic on the book.
    """
    logger, mongo = extract_logger_and_client(context)
    logger.info('Getting stats on book isbn={}', isbn)


@stat.command()
@click.argument('username')
@click.pass_context
def user(context: click.Context, username: str):
    """
    Statistic on the user.
    """
    logger, mongo = extract_logger_and_client(context)
    logger.info('Getting stats on user username={}', username)
