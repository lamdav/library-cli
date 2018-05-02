import click

from ...context_extractor import extract_api
from ...entity_displayer import display_entities


@click.group()
@click.pass_context
def stat(context: click.Context):
    """
    Library Stats Commands.
    """
    api = extract_api(context)
    api.log_tag('STAT')


@stat.command()
@click.argument('isbn')
@click.pass_context
def book(context: click.Context, isbn: str):
    """
    Statistic on the book.
    """
    api = extract_api(context)
    users = api.get_book_stats(isbn)
    if users:
        display_entities(users, api.error, api.success)
    else:
        api.warn('No one has checked out Book isbn={}', isbn)
        exit(0)


@stat.command()
@click.argument('username')
@click.pass_context
def user(context: click.Context, username: str):
    """
    Statistic on the user.
    """
    api = extract_api(context)
    books = api.get_user_stats(username)
    if books:
        display_entities(books, api.error, api.success)
    else:
        api.warn('User username={} has not checked out any book', username)
