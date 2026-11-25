from importlib.metadata import PackageNotFoundError, version

from .formatter import ConllFormatter
from .parser import ConllParser
from .utils import init_parser


try:
    __version__ = version("spacy-conll")
except PackageNotFoundError:
    __version__ = "unknown"


__all__ = ["ConllFormatter", "ConllParser", "__version__", "init_parser"]
