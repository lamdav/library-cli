import click

from ...context_extractor import extract_api

BOOK_EDITABLE_FIELDS = ['title', 'author', 'pages', 'quantity']
USER_EDITABLE_FIELDS = ['name', 'phone']


@click.group()
@click.pass_context
def edit(context: click.Context):
    """
    Library Edit Commands
    """
    api = extract_api(context)
    api.log_tag('EDIT')


@edit.command()
@click.argument('isbn')
@click.argument('field', type=click.Choice(BOOK_EDITABLE_FIELDS))
@click.argument('value')
@click.pass_context
def book(context: click.Context, isbn: str, field: str, value: str):
    """
    Edit a book from the library.

    Edit any field should also update any relevant data structures needed to quickly search.
    """
    api = extract_api(context)
    api.info('Editing book isbn={} field={} new_value={}', isbn, field, value)


@edit.command()
@click.argument('username')
@click.argument('field', type=click.Choice(USER_EDITABLE_FIELDS))
@click.argument('value')
def user(context: click.Context, username: str, field: str, value: str):
    """
    Edit a user from the library.

    Edit any field should also update any relevant data structures needed to quickly search.
    """
    api = extract_api(context)
    api.info('Editing book isbn={} field={} new_value={}', username, field, value)
