# Rogueweek

Write a Rogue game, under the same type of constraints as those found in PICO-8.

We chose to use Pyxel instead of PICO-8 because it's free. Although there are
less constraints, it's still a lot of fun.

![presentation](screenshots/combined.gif)

# Run

Ubuntu :
```sh
make run
```

Or : 
```sh
pip install -r requirements.txt
python game.py
```

# Features to implement / Wishlist

## General
- [X] turned based gameplay
- [X] text/dialogs/information
- [X] title screen / menu
- [X] particle system
- [ ] sound effects
- [X] handle death :)
- [ ] keep stats and scores
 
## Level features
- [X] randomly generated levels
- [X] sequential actions required to finish a level (key, door, boss)
- [X] more than one level (and stairs :) )
- [ ] traps / fire

## Content
- [X] randomly moving enemies: Bat, Slug
- [X] player following enemies: Skel, Ghost
- [X] distance shooting enemies: Plant
- [ ] insensitive to Melee atacks: Ghost
- [X] final boss: Necromancer (raising skels)
- [X] healing items
- [X] show map

## Player skills:
- [X] melee attack (3) (or 2 if cooldown on distance)
- [X] distance attack (2) (possibly 1 turn of cooldown)
- [X] teleport
- [X] thunder storm (1)
