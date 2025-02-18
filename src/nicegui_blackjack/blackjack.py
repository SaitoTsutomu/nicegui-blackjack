"""Blackjack Game"""

import asyncio
import random
import secrets
from collections.abc import Iterable
from enum import IntEnum
from logging import DEBUG, basicConfig, getLogger
from typing import Final, Literal, cast

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


class Card(ui.element):
    """**クラス** | カード

    :ivar num: 0〜51の識別番号
    :ivar rank: カードの数字
    :ivar suit: カードのスーツ
    """

    num: int
    rank: Rank
    suit: Suit

    def __init__(self, num: int, *, opened: bool = False) -> None:
        """表と裏のdivタグを作成(デフォルトは裏を表示)"""
        super().__init__()
        self.num = num
        self.suit = Suit(num // 13)
        self.rank = cast("Rank", num % 13 + 1)
        char = chr(CARD_CODE + self.suit * 16 + self.rank + (self.rank > 11))  # noqa: PLR2004
        color = "black" if self.suit in {Suit.Spade, Suit.Club} else "red-10"
        # GUI作成
        with self.classes(f"card{' opened' * opened}"):
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

    def __str__(self) -> str:
        """文字列化"""
        r = " A 2 3 4 5 6 7 8 910 J Q K"[self.rank * 2 - 2 : self.rank * 2]
        return r + f"({'SHDC'[self.suit]})"


class Owner(ui.element):
    """**クラス** | 手札を持ち、カードを引ける人

    :ivar cards: 手札(カードのリスト)
    :ivar container: カード追加時のUIコンテナ
    """

    cards: list[Card]
    container: ui.element

    def __init__(self, nums: Iterable[int], *, opened_num: int, name: str) -> None:
        """GUIと手札の作成"""
        super().__init__()
        self.container = ui.row()
        with self.container:
            with ui.column().classes("mt-6"):
                ui.label(f"{name}'s cards").classes("text-2xl")
                ui.label().bind_text_from(self, "message").classes("text-2xl pl-6")
            self.cards = [Card(num, opened=i < opened_num) for i, num in enumerate(nums)]

    def add_card(self, num: int, *, opened: bool = False) -> None:
        """手札に一枚加える"""
        with self.container:
            self.cards.append(Card(num, opened=opened))

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

    def __str__(self) -> str:
        """文字列化"""
        return " ".join(f"{card}" if card.opened else f"({card})" for card in self.cards)


class Dealer(Owner):
    """**クラス** | ディーラー

    :cvar LOWER: この数以上なら山札から引かない
    """

    LOWER: Final[int] = 17

    async def act(self, game: "Game") -> None:
        """ディーラーの手番の処理"""
        game.set_props(ask_visible=False, message="Dealer's turn")
        logger.debug("Dealer.act: Point %s", self.point())
        while self.point() < self.LOWER:
            if self.cards[1].opened:  # 2枚目がopenedなら3枚目以降を追加
                self.add_card(game.pop())
                await game.sleep(is_bit=True)
            self.cards[-1].open()
            await game.sleep()
            logger.debug("Dealer.act: Opened %s, Point %s", self.cards[-1], self.point())


class Player(Owner):
    """**クラス** | プレイヤー"""

    async def act(self, game: "Game") -> None:
        """プレイヤーの処理"""
        game.set_props(ask_visible=False, message="Player' turn")
        self.add_card(game.pop())
        await game.sleep(is_bit=True)
        self.cards[-1].open()  # 最後のカードを表にする
        await game.sleep()
        if self.point() < POINT21:
            game.set_props(ask_visible=True)
        else:
            await game.stand()  # Stand処理


class Game(ui.element):
    """**クラス** | ゲーム

    :ivar nums: 山札(カードの数字のリスト)
    :ivar dealer: ディーラー
    :ivar player: プレイヤー
    :ivar ask_visible: カードを引くボタンを表示するかどうか
    :ivar message: メッセージ
    :ivar wait: カードをめくる時間(秒)
    """

    nums: list[int]
    dealer: Dealer
    player: Player
    ask_visible: bool
    message: str
    wait: float

    def __init__(self, *, wait: float = 0.6) -> None:
        """CSSの設定"""
        super().__init__()
        self.wait = wait
        ui.add_css(f"""
            .card {{
                width: 68px;
                height: 112px;
                perspective: 1000px;
            }}
            .face {{
                position: absolute;
                width: 100%;
                height: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 8em;
                backface-visibility: hidden;
                transition: transform {self.wait}s;
            }}
            .back {{
                transform: rotateY(180deg);
            }}
            .card.opened .front {{
                transform: rotateY(180deg);
            }}
            .card.opened .back {{
                transform: rotateY(0);
            }}
            .no-select {{
                user-select: none;
            }}
        """)

    def start(self, seed: int | str | None = None, *, nums: list[int] | None = None) -> None:
        """新規ゲーム

        :param seed: 乱数シード, defaults to None
        :param nums: 配布カードのリスト, defaults to None
        """
        if nums is not None:
            self.nums = nums
        else:
            self.nums = [*range(52)]
            if isinstance(seed, str) and seed.isdigit():
                seed = int(seed)
            seed = secrets.randbelow(1000_000_000) if seed is None else seed
            random.seed(seed)
            logger.debug("Game.start: seed %s", seed)
            random.shuffle(self.nums)
        self.set_props(ask_visible=True)
        # GUI作成
        self.clear()
        with self, ui.card().classes("no-select"):
            ui.label("Blackjack Game").classes("text-3xl")
            with ui.column():
                self.dealer = Dealer((self.pop(), self.pop()), opened_num=1, name="Dealer")
                self.player = Player((self.pop(), self.pop()), opened_num=2, name="Player")
                with ui.row():
                    ui.label().bind_text(self, "message").classes("text-2xl font-bold")
                    with ui.row().bind_visibility_from(self, "ask_visible"):
                        ui.button("Hit", on_click=self.hit)
                        ui.button("Stand", on_click=self.stand)
                with ui.row():
                    self._seed = ""
                    ui.button("New Game", on_click=lambda: self.start(self._seed or None)).classes("mt-4")
                    ui.input(label="Seed").bind_value(self, "_seed")

    def set_props(self, *, ask_visible: bool, message: str = "Click your card.") -> None:
        """プレイヤーにカードを引くか尋ねるように設定"""
        self.ask_visible = ask_visible
        self.message = "Draw card?" if ask_visible else message

    def pop(self) -> int:
        """山札(数字)から一枚取る"""
        return self.nums.pop()

    async def hit(self) -> None:
        """Hit処理"""
        await self.player.act(self)

    async def stand(self) -> None:
        """Stand処理"""
        message = "You loss."
        player_point = self.player.point()
        if player_point <= POINT21:
            await self.dealer.act(self)
            dealer_point = self.dealer.point()
            if player_point == dealer_point:
                message = "Draw."
            elif dealer_point > POINT21 or dealer_point < player_point:
                message = "You win."
        self.set_props(ask_visible=False, message=message)

    async def sleep(self, *, is_bit: bool = False) -> None:
        """カードがめくれる間だけ待つ"""
        await asyncio.sleep(self.wait * (1 - 0.7 * is_bit))


def run_game(*, port: int | None = None) -> None:
    """ゲーム実行"""
    basicConfig(level=DEBUG, format="%(message)s")
    Game().start()
    ui.run(title="Blackjack", reload=False, port=port)
