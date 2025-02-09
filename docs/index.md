# About Blackjack

## Objective

Having a higher sum than the dealer's hand.

## Card Values

* Numeric cards (2-10): The value is as indicated by the number shown.
* Face cards (Jack, Queen, King): Each has a value of 10.
* Ace: Can be set to either 1 or 11.

## Game Flow

* Deal the cards
  * The player and the dealer are each dealt two cards. The player's cards are both face up, while the dealer's is one face up and the other face down.
* Player's Choice
  * Hit: Draw another card.
  * Stand: Play with the current hand.
* Dealer's Turn
  * The dealer turns the face-down cards face up and draws cards until he has 17 or more.
* Winner Decides
  * If the total hand exceeds 21, then loses on a “bust”.
  * When the dealer busts, the remaining player wins.
  * If the hand is high, then wins.
  * If the hands are the same, then tie.

## Install

```sh
pip install nicegui-blackjack
```

## How to play

```sh
blackjack
```
