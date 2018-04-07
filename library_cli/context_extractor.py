import click

from .logger import Logger


def extract_logger(context: click.Context):
    return context.obj.get('logger', Logger())


def extract_client(context: click.Context):
    return context.obj.get('client')


def extract_logger_and_client(context: click.Context):
    return extract_logger(context), extract_client(context)
