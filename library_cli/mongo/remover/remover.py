import click

from ...context_extractor import extract_api


@click.group()
@click.pass_context
def remove(context: click.Context):
    """
    Library Remove Commands.
    """
    api = extract_api(context)
    api.log_tag('REMOVE')


@remove.command()
@click.argument('isbn')
@click.pass_context
def book(context: click.Context, isbn: str):
    """
    Remove a book from the library.

    Do not remove a book there is a book checked out.
    """
    api = extract_api(context)
    api.info('Removing book isbn={}', isbn)


@remove.command()
@click.argument('username')
@click.pass_context
def user(context: click.Context, username: str):
    """
    Remove a user from the library.

    Do not remove user if they have a book checked out.
    """
    api = extract_api(context)
    api.info('Removing user username={}', username)
