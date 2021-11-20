from enum import Enum

class ColorCode(Enum):
    RED=1
    GREEN=2
    BLUE=3
    WHITE=4
    BLACK=5
    YELLOW=6
    PINK=7
    ORANGE=8

class CardValue(Enum):
    pass

class Monster(CardValue):
    DRACULA = 1
    FRANKENSTEIN = 2
    WEREWOLF = 3
    GHOST = 4
    MUMMY = 5
    JEKYLL = 6

class Victim(CardValue):
    COUNT = 7
    COUNTESS = 8
    HOUSEKEEPER = 9
    BUTLER = 10
    MAIDEN = 11
    GARDENER = 12

class Room(CardValue):
    LOBBY = 13
    LAB = 14
    LIBRARY = 15
    CELLAR = 16
    ROOM = 17
    PANTHEON = 18
    HALL = 19
    GARAGE = 20

class Salem(CardValue):
    SALEM = 21
