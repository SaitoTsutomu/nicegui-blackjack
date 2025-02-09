"""Blackjack Game"""

from importlib.metadata import metadata

from .blackjack import Card, Dealer, Game, Owner, Player, Suit, main

_package_metadata = metadata(str(__package__))
__version__ = _package_metadata["Version"]
__author__ = _package_metadata.get("Author-email", "")

__all__ = ["Card", "Dealer", "Game", "Owner", "Player", "Suit", "__author__", "__version__", "main"]
