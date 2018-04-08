import click


class Logger(object):
    def __init__(self):
        self.tag = None

    def success(self, format_string: str, *args):
        """
        Helper method to stylistically print success level logs.
        """
        self.__display(format_string.format(*args), 'green')

    def info(self, format_string: str, *args):
        """
        Helper method to stylistically print info level logs.
        """
        self.__display(format_string.format(*args), 'blue')

    def warn(self, format_string: str, *args):
        """
        Helper method to stylistically print warning level logs.
        """
        self.__display(format_string.format(*args), 'yellow')

    def error(self, format_string: str, *args):
        """
        Helper method to stylistically print error level logs.
        """
        self.__display(format_string.format(*args), 'red')

    def __display(self, message: str, color: str):
        """
        Display message with color
        """
        tagged_message = '[{}] {}'.format(self.tag, message) if self.tag else message
        click.secho(tagged_message, fg=color)
