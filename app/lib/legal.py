import logging
import pathlib

import cython

from app.config import LEGAL_DIR
from app.lib.rich_text import process_rich_text
from app.models.text_format import TextFormat


@cython.cfunc
def _get_legal_data() -> dict[str, str]:
    result = {}

    for path in pathlib.Path(LEGAL_DIR).glob('*.md'):
        locale = path.stem
        logging.info('Loading legal document for %s', locale)
        html = process_rich_text(path.read_text(), TextFormat.markdown)
        result[locale] = html

    return result


_legal_data = _get_legal_data()


def legal_terms(locale: str) -> str:
    """
    Get legal terms for a locale as HTML.

    >>> legal_terms('GB')
    '<p>Thank you for your interest in contributing...</p>'
    >>> legal_terms('NonExistent')
    KeyError: 'NonExistent'
    """
    return _legal_data[locale]
