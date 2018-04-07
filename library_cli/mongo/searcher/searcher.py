import click

from ...context_extractor import extract_api

BOOK_SEARCHABLE_FIELDS = ['title', 'author', 'isbn', 'name']
USER_SEARCHABLE_FIELDS = ['name', 'username', 'phone']


@click.group()
@click.pass_context
def search(context: click.Context):
    """
    Library Search Commands.
    """
    api = extract_api(context)
    api.log_tag('SEARCH')


@search.command()
@click.argument('field', type=click.Choice(BOOK_SEARCHABLE_FIELDS))
@click.argument('keyword')
def book(context: click.Context, field: str, keyword: str):
    """
    Search for Book.
    """
    api = extract_api(context)
    api.info('Searching for book with {}={}', field, keyword)


@search.command()
@click.argument('field', type=click.Choice(USER_SEARCHABLE_FIELDS))
@click.argument('keyword')
def user(context: click.Context, field: str, keyword: str):
    """
    Search for User.
    """
    api = extract_api(context)
    api.info('Searching for user with {}={}', field, keyword)
