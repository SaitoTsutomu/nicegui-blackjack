"""Blackjack Game"""

import asyncio
import random
from collections.abc import Callable, Iterable
from enum import IntEnum
from logging import DEBUG, basicConfig, getLogger
from typing import ClassVar, Final, Literal, cast

from nicegui import ui

CARD_CODE: Final[int] = 127136  # カードの絵柄のユニコード
POINT21: Final[int] = 21

logger = getLogger(__name__)


class Suit(IntEnum):
    """**クラス** | カードのスーツ"""

    Spade = 0
    """スペード"""
    Heart = 1
    """ハート"""
    Diamond = 2
    """ダイヤ"""
    Club = 3
    """クラブ"""


# カードの数字
type Rank = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
# カードのスタイル
type CardClass = Literal["", "opened", "hidden"]


class Card(ui.element):
    """**クラス** | カード

    :ivar num: 0〜51の識別番号
    :ivar rank: カードの数字
    :ivar suit: カードのスーツ
    """

    num: int
    rank: Rank
    suit: Suit

    def __init__(self, num: int, *, class_: CardClass = "", click: Callable | None = None):
        """表と裏のdivタグを作成(デフォルトは裏を表示)"""
        super().__init__()
        self.num = num
        self.suit = Suit(num // 13)
        self.rank = cast("Rank", num % 13 + 1)
        char = chr(CARD_CODE + self.suit * 16 + self.rank + (self.rank > 11))  # noqa: PLR2004
        color = "black" if self.suit in {Suit.Spade, Suit.Club} else "red-10"
        # GUI作成
        with self.classes(f"card {class_}").on("click", click):
            ui.label(chr(CARD_CODE)).classes("face front text-blue-10")
            ui.label(char).classes(f"face back text-{color}")

    def open(self) -> None:
        """カードを表にする"""
        self.classes("opened")

    @property
    def opened(self) -> bool:
        """表かどうか"""
        return "opened" in self.classes

    def point(self) -> int:
        """カードの得点"""
        return min(10, self.rank) if self.opened else 0

    def __str__(self):
        """文字列化"""
        n = self.rank * 2
        m = n - 2
        r = " A 2 3 4 5 6 7 8 910 J Q K"[m:n]
        s = "(" + "SHDC"[self.suit] + ")"
        return r + s


class Owner(ui.element):
    """**クラス** | 手札を持ち、カードを引ける人

    :ivar cards: 手札(カードのリスト)
    :ivar container: カード追加時のUIコンテナ
    :cvar wait: カードをめくる時間
    """

    cards: list[Card]
    container: ui.element
    wait: ClassVar[float] = 0.6

    def __init__(self, nums: Iterable[int], *, opened_num: int, container: ui.element, name: str):
        """GUIと手札の作成"""
        super().__init__()
        self.container = container
        with self.container:
            with ui.column().classes("mt-6"):
                ui.label(f"{name}'s cards").classes("text-2xl")
                ui.label().bind_text_from(self, "message").classes("text-2xl pl-6")
            self.cards = [Card(num, class_="opened" if i < opened_num else "") for i, num in enumerate(nums)]

    def add_card(self, num: int, *, class_: CardClass = "", click: Callable | None = None) -> None:
        """手札に一枚加える"""
        with self.container:
            self.cards.append(Card(num, class_=class_, click=click))

    def point(self) -> int:
        """手札の合計得点"""
        cards = [card for card in self.cards if card.opened]
        point_ = sum(cd.point() for cd in cards)
        for cd in cards:
            if cd.rank == 1 and point_ + 10 <= POINT21:
                point_ += 10
        return point_

    @property
    def message(self) -> str:
        """メッセージ"""
        return f"point: {self.point()}"

    def __str__(self):
        """文字列化"""
        return " ".join(f"{card}" if card.opened else f"({card})" for card in self.cards)


class Dealer(Owner):
    """**クラス** | ディーラー

    :cvar LOWER: この数以上なら山札から引かない
    """

    LOWER: Final[int] = 17

    async def act(self, game: "Game") -> None:
        """ディーラーの手番の処理"""
        game.change_ask(ask_draw=False, message="Dealer's turn")
        logger.debug("Dealer.act: Point %s", self.point())
        while self.point() < self.LOWER:
            if self.cards[1].opened:  # 2枚目がopenedなら3枚目以降を追加
                self.add_card(game.pop())
                await asyncio.sleep(self.wait / 3)
            self.cards[-1].open()
            await asyncio.sleep(self.wait)
            logger.debug("Dealer.act: Opened %s, Point %s", self.cards[-1], self.point())


class Player(Owner):
    """**クラス** | プレイヤー"""

    def draw(self, game: "Game") -> None:
        """山札から裏のままカードを引く"""
        self.add_card(game.pop(), click=lambda: self.act(game))

    async def act(self, game: "Game") -> None:
        """プレイヤーの処理"""
        self.cards[-1].open()  # 最後のカードを表にする
        await asyncio.sleep(self.wait)
        game.change_ask(ask_draw=True)
        if self.point() >= POINT21:
            await game.dealer_turn()  # ディーラーの処理


class Game(ui.element):
    """**クラス** | ゲーム

    :ivar nums: 山札(カードのリスト)
    :ivar dealer: ディーラー
    :ivar player: プレイヤー
    :ivar ask_draw: カードを引くボタンを表示するかどうか
    :ivar message: メッセージ
    """

    nums: list[int]
    dealer: Dealer
    player: Player
    ask_draw: bool
    message: str

    def __init__(self):
        """CSSの設定"""
        super().__init__()
        ui.add_css("""
            .card {
                width: 68px;
                height: 112px;
                perspective: 1000px;
            }
            .face {
                position: absolute;
                width: 100%;
                height: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 8em;
                backface-visibility: hidden;
                transition: transform 0.6s;
            }
            .back {
                transform: rotateY(180deg);
            }
            .card.opened .front {
                transform: rotateY(180deg);
            }
            .card.opened .back {
                transform: rotateY(0);
            }
            .no-select {
                user-select: none;
            }
        """)

    def start(self, seed: int | None = None, *, nums: list[int] | None = None) -> None:
        """新規ゲーム

        :param seed: 乱数シード, defaults to None
        :param nums: 配布カードのリスト, defaults to None
        """
        if nums is not None:
            self.nums = nums
        else:
            self.nums = [*range(52)]
            if seed is not None:
                random.seed(seed)
            random.shuffle(self.nums)
        self.change_ask(ask_draw=True)
        # GUI作成
        self.clear()
        with self, ui.card().classes("no-select"):
            ui.label("Blackjack Game").classes("text-3xl")
            with ui.column():
                self.dealer = Dealer((self.pop(), self.pop()), opened_num=1, container=ui.row(), name="Dealer")
                self.player = Player((self.pop(), self.pop()), opened_num=2, container=ui.row(), name="Player")
                with ui.row():
                    ui.label().bind_text(self, "message").classes("text-2xl font-bold")
                    ui.button("Yes", on_click=self.player_turn).bind_visibility_from(self, "ask_draw")
                    ui.button("No", on_click=self.dealer_turn).bind_visibility_from(self, "ask_draw")
                ui.button("New Game", on_click=self.start)

    def change_ask(self, *, ask_draw: bool, message: str = "Click your card.") -> None:
        """プレイヤーにカードを引くか尋ねるように設定"""
        self.ask_draw = ask_draw
        self.message = "Draw card?" if ask_draw else message

    def pop(self) -> int:
        """山札から一枚取る"""
        return self.nums.pop()

    def player_turn(self) -> None:
        """プレイヤーが山札から裏のままカードを引く"""
        self.player.draw(self)
        self.change_ask(ask_draw=False)

    async def dealer_turn(self) -> None:
        """ディーラーの処理"""
        message = "You loss."
        player_point = self.player.point()
        if player_point <= POINT21:
            await self.dealer.act(self)
            dealer_point = self.dealer.point()
            if player_point == dealer_point:
                message = "Draw."
            elif dealer_point > POINT21 or dealer_point < player_point:
                message = "You win."
        self.change_ask(ask_draw=False, message=message)


def main(*, reload=False, port=8105) -> None:
    """ゲーム実行"""
    basicConfig(level=DEBUG, format="%(message)s")
    Game().start()
    ui.run(title="Blackjack", reload=reload, port=port)
