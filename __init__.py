"""This module turns the repository into a package so that you can load it
as a Git submodule and import that directly.
"""
from .tqueue import Schedulable, Ticket, TurnQueue, __all__  # noqa: F401
