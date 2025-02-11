# flake8: noqa: S101
"""テスト"""

import asyncio
from dataclasses import dataclass

import pytest

from nicegui_blackjack import Game


@pytest.fixture
def game() -> Game:
    """ゲーム"""
    return Game(wait=0)


@dataclass
class Case:
    """ケース(1回の勝負)"""

    nums: list[int]  # Dealerに2枚、Playerに2枚、Playerにnum_hit枚、以降Dealer
    num_hit: int  # Playerがdrawする数
    player_point: int  # 結果(Player得点)
    dealer_point: int  # 結果(Dealer得点)
    message: str  # 結果(メッセージ)


@pytest.mark.parametrize(
    ("case"),
    [
        Case([12, 0, 11, 0], 0, 21, 21, "Draw."),
        Case([12, 6, 11, 0, 8], 1, 20, 17, "You win."),
        Case([12, 5, 11, 0, 8, 4], 1, 20, 21, "You loss."),
    ],
)
def test_game_case(game: Game, case: Case) -> None:
    """ゲームのテスト"""
    game.start(nums=list(reversed(case.nums)))
    for _ in range(case.num_hit):
        asyncio.run(game.hit())
    asyncio.run(game.stand())
    assert game.player.point() == case.player_point, f"{game.player}"
    assert game.dealer.point() == case.dealer_point, f"{game.dealer}"
    assert game.message == case.message
