from typing import Callable, List


def display_entities(entities: List, on_error: Callable, on_success: Callable):
    if not entities:
        on_error('No matched found')
        exit(1)
    else:
        for index, datum in enumerate(entities):
            on_success('{}: {}', index, datum)
        exit(0)
