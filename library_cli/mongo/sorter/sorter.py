import click

from ...context_extractor import extract_api
from ...entity_displayer import display_entities

BOOK_SORTABLE_FIELDS = ['title', 'authors', 'isbn', 'pages']
USER_SORTABLE_FIELDS = ['name', 'username', 'phone']


@click.group()
@click.pass_context
def sort(context: click.Context):
    """
    Library Sort Commands.
    """
    api = extract_api(context)
    api.log_tag('SORT')


@sort.command()
@click.argument('field', type=click.Choice(BOOK_SORTABLE_FIELDS))
@click.pass_context
def books(context: click.Context, field: str):
    """
    Sort books by filter.
    """
    api = extract_api(context)
    books = api.sort_book_by(field)
    display_entities(books, api.error, api.success)


@sort.command()
@click.argument('field', type=click.Choice(USER_SORTABLE_FIELDS))
@click.pass_context
def users(context: click.Context, field: str):
    """
    Sort users by filter.

    Extra feature. Helpful to debug.
    """
    api = extract_api(context)
    users = api.sort_user_by(field)
    display_entities(users, api.error, api.success)
