import click

from ...context_extractor import extract_api

BOOK_SORTABLE_FILTERS = ['title', 'author', 'isbn', 'pages']
USER_SORTABLE_FILTERS = ['name', 'username', 'phone']


@click.group()
@click.pass_context
def sort(context: click.Context):
    """
    Library Sort Commands.
    """
    api = extract_api(context)
    api.log_tag('SORT')


@sort.command()
@click.argument('filter', type=click.Choice(BOOK_SORTABLE_FILTERS))
@click.pass_context
def books(context: click.Context, filter: str):
    """
    Sort books by filter.
    """
    api = extract_api(context)
    api.info('Sorting books by {}', filter)


@sort.command()
@click.argument('filter', type=click.Choice(USER_SORTABLE_FILTERS))
@click.pass_context
def users(context: click.Context, filter: str):
    """
    Sort users by filter.

    Extra feature. Helpful to debug.
    """
    api = extract_api(context)
    api.info('Sorting users by {}', filter)
