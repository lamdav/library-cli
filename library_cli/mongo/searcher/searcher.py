import click

from ...context_extractor import extract_logger, extract_logger_and_client

BOOK_SEARCHABLE_FIELDS = ['title', 'author', 'isbn', 'name']
USER_SEARCHABLE_FIELDS = ['name', 'username', 'phone']


@click.group()
@click.pass_context
def search(context: click.Context):
    """
    Library Search Commands.
    """
    logger = extract_logger(context)
    logger.tag = 'SEARCH'


@search.command()
@click.argument('field', type=click.Choice(BOOK_SEARCHABLE_FIELDS))
@click.argument('keyword')
def book(context: click.Context, field: str, keyword: str):
    """
    Search for Book.
    """
    logger, mongo = extract_logger_and_client(context)
    logger.info('Searching for book with {}={}', field, keyword)


@search.command()
@click.argument('field', type=click.Choice(USER_SEARCHABLE_FIELDS))
@click.argument('keyword')
def user(context: click.Context, field: str, keyword: str):
    """
    Search for User.
    """
    logger, mongo = extract_logger_and_client(context)
    logger.info('Searching for user with {}={}', field, keyword)
