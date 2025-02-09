# flake8: noqa: S101
"""テスト"""

import asyncio
from dataclasses import dataclass

import pytest

from nicegui_blackjack import Game, Owner


@dataclass
class Case:
    """ケース"""

    nums: list[int]  # Playerに2枚、Dealerに2枚、Playerにnum_player_turn枚、以降Dealer
    num_draw: int  # Playerがdrawする数
    player_point: int  # 結果(Player得点)
    dealer_point: int  # 結果(Dealer得点)
    message: str  # 結果(メッセージ)


@pytest.mark.parametrize(
    ("case"),
    [
        Case([11, 0, 12, 0], 0, 21, 21, "Draw."),
        Case([11, 0, 12, 6, 8], 1, 20, 17, "You win."),
        Case([11, 0, 12, 5, 8, 4], 1, 20, 21, "You loss."),
    ],
)
def test_game_build(case: Case):
    """ケースのテスト"""
    Owner.wait = 0
    with Game() as game:
        pass
    game.start(nums=list(reversed(case.nums)))
    for _ in range(case.num_draw):
        game.player_turn()
        asyncio.run(game.player.act(game))
    asyncio.run(game.dealer_turn())
    assert game.player.point() == case.player_point, f"{game.player}"
    assert game.dealer.point() == case.dealer_point, f"{game.dealer}"
    assert game.message == case.message
