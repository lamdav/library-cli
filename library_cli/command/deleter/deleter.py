import click

from ...context_extractor import extract_api

DELETABLE_BOOK_FIELDS = ['title', 'authors', 'pages']
DELETABLE_USER_FIELDS = ['name', 'phone']


@click.group()
@click.pass_context
def delete(context: click.Context):
    """
    Library Field Delete Commands.
    """
    api = extract_api(context)
    api.log_tag('DELETE')


@delete.command()
@click.argument('isbn')
@click.argument('field', type=click.Choice(DELETABLE_BOOK_FIELDS))
@click.pass_context
def book(context: click.Context, isbn: str, field: str):
    """
    Delete a field in a Book.
    """
    api = extract_api(context)
    exit(0) if api.delete_book_field(isbn, field) else exit(1)


@delete.command()
@click.argument('username')
@click.argument('field', type=click.Choice(DELETABLE_USER_FIELDS))
@click.pass_context
def user(context: click.Context, username: str, field: str):
    """
    Delete a field in a User.
    """
    api = extract_api(context)
    exit(0) if api.delete_user_field(username, field) else exit(1)
