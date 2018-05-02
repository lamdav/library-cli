import click

from ...context_extractor import extract_api


@click.group()
@click.pass_context
def action(context: click.Context):
    """
    Library Processing Commands.
    """
    api = extract_api(context)
    api.log_tag('ACTION')


@action.command()
@click.argument('username')
@click.argument('isbn')
@click.pass_context
def take(context: click.Context, username: str, isbn: str):
    """
    Borrow a book with isbn under user with username.
    """
    api = extract_api(context)
    exit(0) if api.check_out_book_for_user(isbn, username) else exit(1)


@action.command()
@click.argument('username')
@click.argument('isbn')
@click.pass_context
def give(context: click.Context, username: str, isbn: str):
    """
    Return a book with isbn a user with username has checked out.
    """
    api = extract_api(context)
    exit(0) if api.return_book_for_user(isbn, username) else exit(1)
