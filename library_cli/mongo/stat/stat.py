import click

from ...context_extractor import extract_api


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
    api.info('Getting stats on book isbn={}', isbn)


@stat.command()
@click.argument('username')
@click.pass_context
def user(context: click.Context, username: str):
    """
    Statistic on the user.
    """
    api = extract_api(context)
    api.info('Getting stats on user username={}', username)
