# -*- coding: utf-8 -*-
"""write-your-own-adventure-computer-game-usborne.ipynb

From the Usborne Book

Initialisation
Lines 1600 onwards from original ZX81 code
"""

import re
import sys # for exit
import logging
from pprint import pprint, pformat # for dumping game_context (for debugging purposes)
from pickle import dump, load # for saving and loading the game
#import pickle
from difflib import ndiff # for diffing game context
import copy # for game debug diffs (as we need a before and after context copy)
import os # for checking if a file exists
import difflib # for diffing files
from random import choice, randint

# From the Usborne Book
# Use the ZX81 code, with an 8x8 game grid, not the Spectrum code as the Spectrum version is a smaller 6x6 game


# Almost all functions take a single game_context object, which contains all game variables
# print_game_context_changes is a debug function that prints the diff of the previous and current game_context, so takes two objects, old and dew context

# Display visible items in {room}
def display_visible_items(game_context):
  current_room = game_context['room'] # set this for code readability

  visible_items = [name for name, obj in game_context['objects'].items() if obj['location'] == current_room and obj['visible'] is True]
  visible_items = ', A '.join(visible_items) # make a comma separated list of visible items

  if visible_items: # if items are visible in this room
    print(f'YOU CAN SEE A {visible_items} HERE.')
#  else:
#    print("YOU SEE NOTHNG HERE.")

  print(f'====================')

# split a string into two parts, the first word, and everything else
# handles an emptry string
def split_string(input_string):
  parts = input_string.split(' ', 1)
  if len(parts) == 2:
      verb, word = parts
  else:
      verb = parts[0]
      word = ''
  return verb, word

# Analyse user input
# TODO: This may not exactly mimic the message logic
def analyse_input(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability


  # In the original OB = 0 is an invalid object
  # and VB=0 was similarly an invalid verb, but because GOSUB doesn't support zero values,
  # the code set VB=V+1 (the number of verbs is V) in the case of an invalid verb
  # The gosub then just jumps to a dummy subroutine on an invalid verb


  # Arrays in the old days started at 1, so 0 was a way of checking for invalid index, we'll use -1
  #verb_index = -1 # Originally VO, and 0 was used as the default
  #object_index = -1 # Originally OB, and 0 was used as the default

  #print(f"query:{game_context['query']}")

  # query to uppercase
  game_context['query']=game_context['query'].upper()

  # remove multiple spaces
  game_context['query']=re.sub(' +', ' ', game_context['query'])

  # remove anything that isn't a space or a character or a question mark
  game_context['query']=re.sub(r'[^A-Z\? ]', '', game_context['query'])

  # query (input from use) based on spaces. We only want the first two words
  [game_context['verb'], game_context['word']]=split_string(game_context['query'])

  # We have to reassign these readability variables here, as we maniuplated them previously
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

#  print(f"verb:{verb} word:{word}") # I think they called this V and W and not V and O because the letter O would be an insane variable name

  # The original used gosubs to jump to a subroutine based on the verb, similar to a switch statement
  # to handle the special case of verb zero, it set it to the max vert, as gosub didn't play
  # nicely with a 0 value. We don't need to do this.

  # In the original a verb (VB) or word (object - OB) was invalid. In the
  # GOSUB subroutine, VB = 0 would result in running a dummy subroutine that just returns

  # If there is no word
  if current_word == "":
    game_context['message'] = "I NEED TWO WORDS"
    # apparently this will be changed later in the program to allow valid single word input

  # LINE 360
  # If there is a word, but it's invalid
  if current_word not in game_context['objects']:
    game_context['message'] = "THAT'S SILLY"

  # LINE 390
# if the verb is invalid, but object is valid ("fly door" for example)
  elif current_verb not in game_context['verbs'] and current_word in game_context['objects']:
    game_context['message'] = f"YOU CAN'T '{game_context['query']}'"

  # LINE 400
  # if the verb is invalid, and neither is the object
  elif current_verb not in game_context['verbs'] and current_word not in game_context['objects']:
    game_context['message'] = "YOU DON'T MAKE SENSE"

  # LINE 410
  # verb is valid, object is valid, but we're not carrying it
  elif current_verb in game_context['verbs'] and current_word in game_context['objects'] and game_context['objects'][current_word]['carrying'] == False:
    game_context['message'] = f"YOU DON'T HAVE {current_word}"

  #else:
    # You shouldn't get here
  #  message = "SOMETHING UNUSAL HAS HAPPENED."

  #return verb_index, object_index, verb, word, message

def init(game_context):
  # Initilaisation

  # constants (capitalised as per Pythong convetion)
  # this is just for error checking the lists and dicts, in case we miss an item or put in extra commas
  VERB_COUNT = 25 + 5 # Originally V, I've added 5 more (DUMP, LOAD, SAVE, DEBUG, QUIT)
  OBJECT_COUNT = 37 # Originally W
  GETTABLE_OBJECT_COUNT = 18 # Originally G
  ROOM_COUNT = 64 # Didn't originally exist, but lets define it

  # reset user input
  game_context['word'] = ""
  game_context['verb'] = ""
  game_context['query'] = ""

  game_context['debug'] = False # By default debugging is off

  # Line 1600 and onwards in original
  # trying to keep this version as true to the original as possible, so this is going to be simple and unoptimised with global variables
  # routes was R$ in the original
  # 8 routes per line as per book

  # there are 64 locations, 0 - 63.
  #TODO: I've added some flags for special features, such as the DOOR open or closed
  game_context['locations'] = [
      {"description": "DARK CORNER", "routes": "SE"},
      {"description": "OVERGROWN GARDEN", "routes": "WE"},
      {"description": "BY LARGE WOODPILE", "routes": "WE"},
      {"description": "YARD BY RUBBISH", "routes": "SWE"},
      {"description": "WEEDPATCH", "routes": "WE"},
      {"description": "FOREST", "routes": "WE"},
      {"description": "THICK FOREST", "routes": "SWE"},
      {"description": "BLASTED TREE", "routes": "WS"},
      {"description": "CORNER OF HOUSE", "routes": "NS"},
      {"description": "ENTRANCE TO KITCHEN", "routes": "SE"},
      {"description": "KITCHEN & GRIMY COOKER", "routes": "WE"},
      {"description": "SCULLERY DOOR", "routes": "NW"},
      {"description": "ROOM WITH INCHES OF DUST", "routes": "SE"},
      {"description": "REAR TURRET ROOM", "routes": "W"},
      {"description": "CLEARING BY HOUSE", "routes": "NE"},
      {"description": "PATH", "routes": "NSW"},
      {"description": "SIDE OF HOUSE", "routes": "NS"},
      {"description": "BACK OF HALLWAY", "routes": "NS"},
      {"description": "DARK ALCOVE", "routes": "SE"},
      {"description": "SMALL DARK ROOM", "routes": "WE"},
      {"description": "BOTTOM OF SPIRAL STAIRCASE", "routes": "NWUD"},
      {"description": "WIDE PASSAGE", "routes": "SE"},
      {"description": "SLIPPERY STEPS", "routes": "WSUD"},
      {"description": "CLIFFTOP", "routes": "NS"},
      {"description": "NEAR CRUMBLING WALL", "routes": "N"},
      {"description": "GLOOMY PASSAGE", "routes": "NS"},
      {"description": "POOL OF LIGHT", "routes": "NSE"},
      {"description": "IMPRESSIVE VAULTED HALLWAY", "routes": "WE"},
      {"description": "HALL BY THICK WOODEN DOOR", "routes": "WE"},
      {"description": "TROPHY ROOM", "routes": "NSW"},
      {"description": "CELLAR WITH BARRED WINDOW", "routes": "NS"},
      {"description": "CLIFF PATH", "routes": "NS"},
      {"description": "CUPBOARD WITH HANGING COAT", "routes": "S"},
      {"description": "FRONT HALL", "routes": "NSE"},
      {"description": "SITTING ROOM", "routes": "NSW"},
      {"description": "SECRET ROOM", "routes": "S"},
      {"description": "STEEP MARBLE STAIRS", "routes": "NSUD"},
      {"description": "DINING ROOM", "routes": "N"},
      {"description": "DEEP CELLAR WITH COFFIN", "routes": "N"},
      {"description": "CLIFF PATH", "routes": "NS"},
      {"description": "CLOSET", "routes": "NE"},
      {"description": "FRONT LOBBY", "routes": "NW"},
      {"description": "LIBRARY OF EVIL BOOKS", "routes": "NE"},
      {"description": "STUDY WITH DESK & HOLE IN WALL", "routes": "W"},
      {"description": "WEIRD COBWEBBY ROOM", "routes": "NSE"},
      {"description": "VERY COLD CHAMBER", "routes": "WE"},
      {"description": "SPOOKY ROOM", "routes": "W"},
      {"description": "CLIFF PATH BY MARSH", "routes": "NS"},
      {"description": "RUBBLE-STREWN VERANDAH", "routes": "SE"},
      {"description": "FRONT PORCH", "routes": "NSW"},
      {"description": "FRONT TOWER", "routes": "E"},
      {"description": "SLOPING CORRIDOR", "routes": "WE"},
      {"description": "UPPER GALLERY", "routes": "NW"},
      {"description": "MARSH BY WALL", "routes": "S"},
      {"description": "MARSH", "routes": "SW"},
      {"description": "SOGGY PATH", "routes": "NW"},
      {"description": "BY TWISTED RAILING", "routes": "NE"},
      {"description": "PATH THROUGH IRON GATE", "routes": "NWE"},
      {"description": "BY RAILINGS", "routes": "WE"},
      {"description": "BENEATH FRONT TOWER", "routes": "WE"},
      {"description": "DEBRIS FROM CRUMBLING FACADE", "routes": "WE"},
      {"description": "LARGE FALLEN BRICKWORK", "routes": "NWE"},
      {"description": "ROTTING STONE ARCH", "routes": "NWE"},
      {"description": "CRUMBLING CLIFFTOP", "routes": "W"}
  ]

  game_context['routes'] = [ "SE", "WE", "WE", "SWE", "WE", "WE", "SWE", "WS",
            "NS", "SE", "WE", "NW", "SE", "W", "NE", "NSW",
            "NS", "NS", "SE", "WE", "NWUD", "SE", "WSUD", "NS",
            "N", "NS", "NSE", "WE", "WE", "NSW", "NS", "NS",
            "S" ,"NSE", "NSW", "S", "NSUD", "N","N","NS",
            "NE", "NW", "NE", "W", "NSE", "WE", "W", "NS",
            "SE", "NSW", "E", "WE", "NW","S","SW", "NW",
            "NE", "NWE", "WE", "WE", "WE", "NWE", "NWE", "W" ]

  # if len(game_context['routes']) != ROOM_COUNT:
  #   raise Exception(f"There are only {len(routes)} routes, which should be equal to ROOM_COUNT: {ROOM_COUNT}")


  # Array D is the descriptions
  # descriptions was D$ in the original
  # Trying to keep same code formatting as the book, so not 8 location descriptions per line
  # TODO: Delete, no longer used
  '''
  descriptions = [ "DARK CORNER", "OVERGROWN GARDEN", "BY LARGE WOODPILE", "YARD BY RUBBISH",
                  "WEEDPATCH", "FOREST", "THICK FOREST", "BLASTED TREE",
                  "CORNER OF HOUSE", "ENTRANCE TO KITCHEN", "KITCHEN & GRIMY COOKER", "SCULLERY DOOR",
                  "ROOM WITH INCHES OF DUST", "REAR TURRET ROOM", "CLEARING BY HOUSE", "PATH",
                  "SIDE OF HOUSE", "BACK OF HALLWAY", "DARK ALCOVE", "SMALL DARK ROOM" ,
                  "BOTTOM OF SPIRAL STAIRCASE", "WIDE PASSAGE", "SLIPPERY STEPS", "CLIFFTOP",
                  "NEAR CRUMBLING WALL", "GLOOMY PASSAGE", "POOL OF LIGHT", "IMPRESSIVE VAULTED HALLWAY",
                  "HALL BY THICK WOODEN DOOR", "TROPHY ROOM", "CELLAR WITH BARRED WINDOW", "CLIFF PATH",
                  "CUPBOARD WITH HANGING COAT", "FRONT HALL", "SITTING ROOM", "SECRET ROOM",
                  "STEEP MARBLE STAIRS", "DINING ROOM", "DEEP CELLAR WITH COFFIN", "CLIFF PATH",
                  "CLOSET", "FRONT LOBBY", "LIBRARY OF EVIL BOOKS", "STUDY WITH DESK & HOLE IN WALL",
                  "WEIRD COBWEBBY ROOM", "VERY COLD CHAMBER", "SPOOKY ROOM", "CLIFF PATH BY MARSH",
                  "RUBBLE-STREWN VERANDAH", "FRONT PORCH", "FRONT TOWER", "SLOPING CORRIDOR",
                  "UPPER GALLERY", "MARSH BY WALL", "MARSH", "SOGGY PATH",
                  "BY TWISTED RAILING", "PATH THROUGH IRON GATE", "BY RAILINGS", "BENEATH FRONT TOWER",
                  "DEBRIS FROM CRUMBLING FACADE", "LARGE FALLEN BRICKWORK", "ROTTING STONE ARCH", "CRUMBLING CLIFFTOP" ]

  if len(descriptions) != ROOM_COUNT:
    raise Exception(f"There are only {len(game_context['routes'])} descriptions, which should be equal to ROOM_COUNT: {ROOM_COUNT}")
  '''
  # O (the letter) is to show if an object is visible
  # objects was O$ in the original (what a terrible variable name!)
  #old_objects = [ "PAINTING", "RING", "MAGIC SPELLS", "GOBLET", "SCROLL", "COINS", "STATUE", "CANDLESTICK", "MATCHES", "VACUUM", "BATTERIES", "SHOVEL", "AXE", "ROPE", "BOAT", "AEROSOL", "CANDLE", "KEY", "NORTH", "SOUTH", "WEST", "EAST", "UP", "DOWN", "DOOR", "BATS", "GHOSTS", "DRAWER", "DESK", "COAT", "RUBBISH", "COFFIN", "BOOKS", "XZANFAR", "WALL", "SPELLS" ]



  # Array C is for information about which objects the player is carrying


  # Array L shows the location each object is in
  # location_of_objects was L in the original
  # TODO: Delete, no longer used
  #location_of_objects = [ 46,38,35,50,13,18,28,42,10,25,26,4,2,7,47,60,43,32]

  # Array F is for flags, 0 is inactive/normal; 1 is active/not normal. The initial state is preset.
  # set flags as per book
  # TODO: Delete, no longer used
  #flag_object_visible = [0] * OBJECT_COUNT # OBJECT_COUNT zero value flags, one per object
  # TODO: I suspect these items are off by one, as door is 24, not 23
  #flag_object_visible[18] = 1
  #flag_object_visible[17] = 1
  #flag_object_visible[2] = 1
  #flag_object_visible[26] = 1
  #flag_object_visible[28] = 1
  #flag_object_visible[23] = 1 # front door open, but this is object 23!

  # this version keeps the state of each object

  # In the original code the variable G was used to only allow the user to pick up the first 18 objects
  # We will allow more flexiblity
  # In the original the F flag array was used to store if an object was visible (0) or invisible (1)
  # All objects were set to visible (0) when the program started and then these objects objects were therefore invisible (set to 1): 18,17,2,26,28,23
  game_context['objects'] = {
    "DUMMY": {"location": None, "visible": False, 'carrying': False, "can_be_picked_up": False},  # Index 0 - adding this to keep indexes consistent with original code
    "PAINTING": {"location": 46, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 1
    "RING": {"location": 38, "visible": False, 'carrying': False, "can_be_picked_up": True},  # Index 2 - invisible at startup
    "MAGIC SPELLS": {"location": 35, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 3
    "GOBLET": {"location": 50, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 4
    "SCROLL": {"location": 13, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 5
    "COINS": {"location": 18, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 6
    "STATUE": {"location": 28, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 7
    "CANDLESTICK": {"location": 42, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 8
    "MATCHES": {"location": 10, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 9
    "VACUUM": {"location": 25, "visible": True, 'carrying': False, "can_be_picked_up": True, "turned_on": False},  # Index 10
    "BATTERIES": {"location": 26, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 11
    "SHOVEL": {"location": 4, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 12
    "AXE": {"location": 2, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 13
    "ROPE": {"location": 7, "visible": True, 'carrying': False, "can_be_picked_up": True, "up_tree": False},  # Index 14 - In the original the rope flag was used to determine if a player is up the tree
    "BOAT": {"location": 47, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 15
    "AEROSOL": {"location": 60, "visible": True, 'carrying': False, "can_be_picked_up": True},  # Index 16
    "CANDLE": {"location": 43, "visible": False, "lit": False, "low_light": 60, 'carrying': False, "can_be_picked_up": True},  # Index 17 - invisible at startup
    "KEY": {"location": 32, "visible": False, 'carrying': False, "can_be_picked_up": True},  # Index 18 - invisible at startup
    "NORTH": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 19
    "SOUTH": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 20
    "WEST": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 21
    "EAST": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 22
    "UP": {"location": None, "visible": False, 'carrying': False, "can_be_picked_up": False},  # Index 23 - invisible at startup
    "DOWN": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 24
    "DOOR": {"location": None, "visible": True, 'carrying': False, "is_open": True, "can_be_picked_up": False},  # Index 25. Front door is open by default
    "BATS": {"location": None, "visible": False, 'carrying': False, "can_be_picked_up": False},  # Index 26 - invisible at startup
    "GHOSTS": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 27
    "DRAWER": {"location": None, "visible": False, 'carrying': False, "can_be_picked_up": False},  # Index 28 - invisible at startup
    "DESK": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 29
    "COAT": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 30
    "RUBBISH": {"location":None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 31
    "COFFIN": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 32
    "BOOKS": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 33
    "XZANFAR": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 34
    "WALL": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False},  # Index 35
    "SPELLS": {"location": None, "visible": True, 'carrying': False, "can_be_picked_up": False}  # Index 36
  }
  if len(game_context['objects']) != OBJECT_COUNT:
    raise Exception(f"There are only {len(game_context['objects'])} descriptions, which should be equal to OBJECT_COUNT: {OBJECT_COUNT}")

  # verbs was V$ in the original
  # TODO: Get rid of this
  #verbs = [ "HELP", "CARRYING?", "GO", "N", "S", "W", "E", "U", "D", "GET", "TAKE", "OPEN", "EXAMINE", "READ", "SAY", "DIG", "SWING", "CLIMB", "LIGHT", "UNLIGHT", "SPRAY", "USE", "UNLOCK", "LEAVE", "SCORE" ]

  # Dictionary of verbs with corresponding handlers
  # The handlers make handling verbs much easier, as there is no need for
  # a giant match-case statement
  game_context['verbs'] = {
    "HELP": {"handler": handle_help},
    "CARRYING?": {"handler": handle_carrying},
    "GO": {"handler": handle_go},
    "N": {"handler": handle_go}, # TODO: Should we just have a single handle_go for all these and modify handle_go to allow single direction words?
    "S": {"handler": handle_go},
    "W": {"handler": handle_go},
    "E": {"handler": handle_go},
    "U": {"handler": handle_go},
    "D": {"handler": handle_go},
    "GET": {"handler": handle_get_and_take},
    "TAKE": {"handler": handle_get_and_take},
    "OPEN": {"handler": handle_open}, # Index 12
    "EXAMINE": {"handler": handle_examine}, # Index 13
    "READ": {"handler": handle_read}, # Index 14
    "SAY": {"handler": handle_say}, # Index 15
    "DIG": {"handler": handle_dig}, # Index 16
    "SWING": {"handler": handle_swing}, # Index 17
    "CLIMB": {"handler": handle_climb}, # Index 18
    "LIGHT": {"handler": handle_light},
    "UNLIGHT": {"handler": handle_unlight},
    "SPRAY": {"handler": handle_spray},
    "USE": {"handler": handle_use},
    "UNLOCK": {"handler": handle_unlock},
    "LEAVE": {"handler": handle_leave},
    "SCORE": {"handler": handle_score},
    "DEBUG": {"handler": handle_debug},
    "DUMP": {"handler": handle_dump},
    "SAVE": {"handler": handle_save_game},
    "LOAD": {"handler": handle_load_game},
    "QUIT": {"handler": handle_quit}
  }
  if len(game_context['verbs']) != VERB_COUNT:
    raise Exception(f"There are only {len(game_context['verbs'])} descriptions, which should be equal to VERB_COUNT: {VERB_COUNT}")

  # LL is a counter for how long many turns the candle will stay lit.
  # LL perhaps means "low light"?
  #LL = 60

  # room (originally RM) is location of player (in 1 d array space)
  game_context['room'] = 57 # we start in the FRONT PORCH

  # message (originally M) is for messages from the previous turn
  game_context['message'] = "OK"

  # The input the user types are split into two words, V (verb) and W (word I assume)
  # when analysing verbs the computer finds V in the Verb list, then sets VB to the verbs index. It's crazy how it seems that in basic the string V$ and the array V$() are treated as separate variables
  #   Similarly W is checked against objects and WB records the index
  # the program runs some error checking on VB and WB to ensure it's possible

  # There are override conditions, such as bats attach
  # This program uses single letter variables. This is a habit I recall, and was for memory saving purposes in 8 bit micro-computers


  #ll = 60 #TODO: What is this LL?

  # Lines 2240 - 2380 reset the variables to their original state between game plays, however
  # there is no need to do this on our Python version, as we will just initialise the variables every time we play

  # Run once apparently, keeping same variable names
  #Originally this was line 2440

  ## TO DO fix all this, I was looking at the spectrum code, I should have looked at page 36 (pdf page 37)
  # R was a 36x4 string. Presumably an array of 4 strings, 36 characters long.
  # D was a 36x30 string. Presumably an array of 30 strings,  36 characters long.
  # V was a 25x9 string. Presumably an array of 9 strings, 25 characters long. Line 2420 was weird in the code, is V and V$ different?
  # O was a 36x13 string. Presumably an array of 13 strings, 36 characters long.
  # C was an array W long (36 long)
  # F was an array W long (36 long)
  # L was an array G long (18 long)

  #return routes, locations, descriptions, verbs, objects, verbs_dict, room, message

def display_welcome_message():
  print(f'''
  HAUNTED HOUSE ADVENTURE
  ***********************')
  Originally written for "MICROSOFT" BASIC
  and required 16K of RAM

  This version written in Python
  for educational purposes
  ''')

# Update candle.
# If candle is lit, reduce the counter
# If the candle is less than 1, then it's no longer visible.
def update_candle(game_context):
  current_room = game_context['room'] # set this for code readability

  if game_context['objects']['CANDLE']['lit']:
    game_context['objects']['CANDLE']['light_limit'] -= 1

  if game_context['objects']['CANDLE']['light_limit'] < 1:
    game_context['objects']['CANDLE']['visible'] = False

# If we're in the lobby and the door is still open, slam the door shut
def check_if_front_door_slams(game_context):
  current_room = game_context['room'] # set this for code readability

  if current_room == 41 and game_context['objects']['DOOR']['is_open'] is True:

    # update routes from FRONT PORCH so we can't go NORTH through the front door again.
    game_context['locations'][49]['routes'] = "SW"

    # We don't update Lobby directions, as they didn't include South to begin with, exits were always only NW for Lobby.
    game_context['message'] = "THE DOOR SLAMS SHUT!"

    game_context['objects']['DOOR']['is_open'] = False

# Line 420
# If bats are present, player is in Rear Turret Room, random number is not 3 and player hasn't used verb 21 (SPRAY) in his instructions, then M$ is set to "BATS ATTACKING" and player cannot go any further in the game.
def check_bats_status(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if current_room == 13 and game_context['objects']['BATS']['visible'] and choice([True, False, False]) and current_verb != "SPRAY":
    return True

# Line 430
# Original Description:
# If player is in Cobwebby Room, random number value is 1 and vacuum cleaner is switched off, then flag is set for paralysing ghosts to appear, i.e. F(27) is set to 1.
def ghosts_randomly_appear_in_cobwebby_room(game_context):
  current_room = game_context['room'] # set this for code readability

  if current_room == 44 and choice([True, False]) and game_context['objects']['VACUUM']['turned_on'] is False:
    game_context['objects']['GHOSTS']['visible'] = True


# Line 440 & 450
# if the candle is low or extinguished them update the message
# if not, the message to the user remains unchanged
def get_candle_status_message(game_context):
  current_room = game_context['room'] # set this for code readability

  if game_context['objects']['CANDLE']['low_light'] == 10:
    game_context['message'] = "YOUR CANDLE IS WANING!"
  elif game_context['objects']['CANDLE']['low_light'] == 1:
    game_context['message'] = "YOUR CANDLE IS OUT!"

# Handle verb function
# Originally these were subroutines

# Function to find and execute the handler for a given verb
def handle_verb(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  # keep handling verb
  verb_dict_result = game_context['verbs'].get(current_verb)

  # if the verb exists in the dictionary, then run the verb handler
  if verb_dict_result and "handler" in verb_dict_result:

    # get the handler function result
    handler_result = verb_dict_result['handler'](game_context)

    # if the hanlder function didn't return anything, then we keep the room and message
    if handler_result is None:
      return

    # if the hanlder did return something, then we update the room and message
    else:
        game_context['room'] = handler_result[0]
        game_context['message'] = handler_result[1]

  else:
    # If it is an invalid word, normally we just do nothing, but if debug is on, say something
    if game_context['debug'] is True:
      print(f"ERROR: No handler for {current_verb}")

# print_game_context_changes is a debug function that prints the diff of the previous and current game_context, so takes two objects, old and dew context
def print_game_context_changes(old_game_context, game_context):

  old_game_context_string = pformat(old_game_context)#.upper().replace(' ','')
  # remove extra whitespace in old_game_context_string

  #old_game_context_string = ' '.join(old_game_context_string) # remove extra white space
  game_context_string = pformat(game_context)#.upper().replace(' ','')

  #game_context_string = ' '.join(game_context_string) # remove extra white space
  game_context_diff = ndiff(old_game_context_string.splitlines(), game_context_string.splitlines())
  #game_context_diff = difflib.unified_diff(old_game_context_string.splitlines(), game_context_string.splitlines())#, lineterm='')


  #line_counter = 0

  # printing the entire ndiff is huge:
  #print('\n'.join(game_context_diff))

  print("==GAME CONTEXT DIFF DEBUG==")

  # so instead print just the lines that have changed:
  for index, line in enumerate(game_context_diff):
    if line.startswith('+') or line.startswith('-'):
      # don't print debug lines with message, query, verb or word updates
      # this could be useful debugging issues with the handler functions, but when debugging the game it's just annoying.
      #if not("message" in line or "query" in line or "verb" in line or "word" in line):
    # if  KEY in line, print next three lines
      print(line)
#    if 'KEY' in line:
#      print(f"{index:03}:{line}")
#      line_counter = 3
#    elif line_counter > 0:
#      print(f"{index:03}:{line}")
#      line_counter -= 1

  print("==========================")

  # the old game state is now a copy of the current game state
  # deepcopy() rather than copy() is used as game_state contains nested structures
  #old_game_context = copy.deepcopy(game_context)
  # above doesnt work
  old_game_context.clear()  # Clear the existing game_context dictionary
  old_game_context.update(game_context)  # Update with loaded data (merge, which is bad if the save file is from an old version of the game!)

# Define handler functions for each verb
def handle_help(game_context):
  print("HELP")
  print(f"WORDS I KNOW:")
  print(",".join(game_context['verbs'].keys()))


def handle_carrying(game_context):
  current_room = game_context['room'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling CARRYING?")

  print("YOU ARE CARRYING:")

  carried_objects = [object_name for object_name, object_info in game_context['objects'].items() if object_info['carrying'] is True]
  carried_objects_list = ", ".join(carried_objects)
  print(carried_objects_list)

  game_context['message'] = ""

  #for key, value in game_context['objects'].items():
  #  if value['carrying'] is True:
  #    print(key)
  #print(game_context['objects
  #for carried_object in game_context['objects']:
    #print("{type(carried_object['carrying'])}")
   # print(type(carried_object['carrying']))
#  carried_objects = [carried_object for carried_object in game_context['objects'] if carried_object['carried'] is True]
#  print(",",join(carried_objects))

# If the user types "GO <DIRECTION>" then call the appropriate handler
def handle_go(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling GO")

  # if the person types N,S,E,W,U, or D, then we set the word to be the verb so it will match the match statement
  if current_verb == "GO":
    current_verb = current_word

  # LINE 780 - 840 stop processing that prevents you moving
  # There is some complexity to decoding what all the variables mean, but this
  # is important code

  # 780 IF F(14)=1 THEN M$="CRASH! YOU FELL OUT OF THE TREE!":F(14)=0:RETURN
  if game_context['objects']['ROPE']['up_tree'] is True:
    game_context['message'] = "CRASH! YOU FELL OUT OF THE TREE!"
    game_context['objects']['ROPE']['up_tree'] = False
    return

  # 790 IF F(27)=1 AND RH=52 THEN H$="GHOSTS WILL NOT LET YOU MOVE": RETURN
  if current_room == 52 and game_context['objects']['GHOSTS']['visible'] is True:
    game_context['message'] = "GHOSTS WILL NOT LET YOU MOVE"
    return

  # 800 IF RM=45 AND C(1)=1 AND F(34)=0 THEN M$="A MAGICAL BARRIER TO THE WEST":RETURN
  # If we're in room 45 (COLD CHAMBER) and have the PAINTING (C1=1) and
  # the painting is in room 46, so if we pick it up then we get stuck with the barrier
  if game_context['room'] == 45 and game_context['objects']['PAINTING']['carrying'] is True and game_context['objects']['XZANFAR']['visible'] is True:
    game_context['message'] = "A MAGICAL BARRIER TO THE WEST"
    return

  # 810 IF (RM=26 AND F(Q)=0) AND (D=1 OR D=4) THEN M$="YOU NEED A LIGHT": RETURN
  # ROOM IS "POOL OF LIGHT", exits are NSE. If we are here and the candle isn't lit then we can only go east, which means we're stuck in the cellar series of rooms
  if current_room == 26 and game_context['objects']['CANDLE']['lit'] is False and (current_word == "NORTH" or current_word =="SOUTH"):
    game_context['message'] = "YOU NEED A LIGHT"
    return

  # 820 IF RM=54 AND C(15)) <1 THEN MS="YOU'RE STUCK!*:RETURN
  #If you are at the MARSH and BOAT isn't being carried (take boat I suppose), then you're stuck
  if current_room == 54 and game_context['objects']['BOAT']['carrying'] is False:
    game_context['message'] = "YOU'RE STUCK!"
    return


  # 830 IF C(5)=1 AND NOT (RN=53 OR RM=54 OR RM=55 OR RM=47)
  if game_context['objects']['BOAT']['carrying'] == True and not (current_room == 53 or current_room == 54 or current_room == 55 or current_room == 47):
    game_context['message'] = "YOU CAN'T CARRY A BOAT"
    return
  # 840 IF (RM > 26 AND RM < 3O) AND F(0)=0 THEN M$="TOO DARK TO MOVE":RETURN
  # If you're in room 27 (VAULTED HALL) room 28 (HALL), room 29 (TROPHY ROOM) and the candle isn't lit then you can't move
  if current_room > 26 and current_room < 30 and game_context['objects']['CANDLE']['lit'] is False:
    game_context['message'] = "TOO DARK TO MOVE"
    return


  # first handle up down, then handle nsew
  # map isn't really 3D, so UP and DOWN is converted to N,S,W or E
  match current_verb:
    case "UP" | "U":
      match current_room:
        case 20: # In room 20 (SPIRAL STAIRCASE), UP is NORTH
          current_verb = "NORTH"
          game_context['message'] = "OK"
        case 22: # In room 22 (SLIPPERY STEPS), UP is WEST
          current_verb = "WEST"
          game_context['message'] = "OK"
        case 36: # In room 36 (STEEP MARBLE STAIRS), UP is SOUTH
          current_verb = "SOUTH"
          game_context['message'] = "OK"
        case _:
          game_context['message'] = "CAN'T GO THAT WAY"
    case "DOWN" | "D":
      if game_context['debug'] is True:
        print("DEBUG: Going DOWN")

      # map isn't really 3D, so UP and DOWN is converted to N,S,W or E
      match current_room:
        case 20: # In room 20 (SPIRAL STAIRCASE), DOWN is WEST
          current_verb = "WEST"
          game_context['message'] = "OK"
        case 22: # In room 22 (SLIPPERY STEPS), DOWN is SOUTH
          current_verb = "SOUTH"
          game_context['message'] = "OK"
        case 36: # In room 36 (STEEP MARBLE STAIRS), DOWN is NORTH
          current_verb = "NORTH"
          game_context['message'] = "OK"
        case _:
          game_context['message'] = "CAN'T GO THAT WAY"


  match current_verb:
    case "NORTH" | "N":
      if game_context['debug'] is True:
        print("DEBUG: Going DOWN")

      if game_context['locations'][current_room]['routes'].find("N") != -1:
        # North moves us 8 positions up the grid
        game_context['room'] -= 8
        game_context['message'] = "OK"
      else:
        game_context['message'] = "CAN'T GO THAT WAY"

    case "SOUTH" | "S":
      if game_context['locations'][current_room]['routes'].find("S") != -1:
        # South moves us 8 positions down the gird
        game_context['room'] += 8
        game_context['message'] = "OK"
      else:
        game_context['message'] = "CAN'T GO THAT WAY"

    case "WEST" | "W":
      if game_context['locations'][current_room]['routes'].find("W") != -1:
        game_context['room'] -= 1
        game_context['message'] = "OK"
      else:
        game_context['message'] = "CAN'T GO THAT WAY"

    case "EAST" | "E":
      if game_context['locations'][current_room]['routes'].find("E") != -1:
        game_context['room'] += 1
        game_context['message'] = "OK"
      else:
        game_context['message'] = "CAN'T GO THAT WAY"

    case _:
      game_context['message'] = "GO WHERE?" # Line 950

  check_if_front_door_slams(game_context)

# LINES 980 - 1020
# Handle getting and taking of objects (synonyms of each other)
def handle_get_and_take(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling GET and TAKE")
  # invalid objects can come through.
  if current_word not in game_context['objects']:
    pass # do nothing
  # LINE 980 check if the object is able to be picked up
  elif game_context['objects'][current_word]['can_be_picked_up'] is False:
    game_context['message'] = f"I CAN'T TAKE {current_word}"

  # LINE 985 check if the object isn't in this room
  elif game_context['objects'][current_word]['location'] != current_room:
    game_context['message'] = "IT ISN'T HERE"

  # LINE 990 check if the object is visible
  elif game_context['objects'][current_word]['visible'] is False:
    game_context['message'] = f"WHAT {current_word}?"

  # LINE 1000 check if we already have the object
  elif game_context['objects'][current_word]['carrying'] is True:
    game_context['message'] = f"YOU ALREADY HAVE IT"

  # LINE 1010 pick up the object
  elif game_context['objects'][current_word]['location'] == current_room and game_context['objects'][current_word]['visible'] is True:
    game_context['objects'][current_word]['carrying'] = True
    game_context['objects'][current_word]['location'] = None # the original set the room to 65 when an object was carried, but we'll use None
    game_context['message'] = f"YOU HAVE THE {current_word}"

# LINE 1030 - 1060
def handle_open(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling OPEN")

  # If we're in ??? and have been asked to OPEN the DRAWER or DESK then open it and reveal the candle
  if current_room == 43 and (current_word == "DRAWER" or current_word == "DESK"):
    game_context['objects']['CANDLE']['visible'] = True
    game_context['message'] = "DRAWER OPEN"

  # You can never open the front door apparently
  elif current_room == 28 and current_word == "DOOR":
    game_context['message'] = "IT's LOCKED"

  # open the coffin reveals the ring
  elif current_room == 38 and current_word == "COFFIN":
    game_context['message'] = "THAT's CREEPY"
    game_context['objects']['RING']['visible'] = True

# LINES 1070 - 1130
def handle_examine(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling EXAMINE")

  # If we EXAMINE COAT then tell the user there is something there and make key visible
  # Note that there is no checking for which room we're in! I suspect memory constraints in the original mean that this wasn't done
  if current_word == "COAT":
    game_context['message'] = "SOMETHING HERE!"
    game_context['objects']['KEY']['visible'] = True

  #If we EXAMINE the RUBBISH, tell the user that's disgusting!
  elif current_word == "RUBBISH":
    game_context['message'] = "THAT'S DISGUSTING!"

  # EXAMINE the DESK or DRAWER and there is... a DRAWER
  elif (current_word == "DRAWER" or current_word == "DESK"):
    game_context['message'] = "THERE IS A DRAWER"

  # EXAMINE BOOK or SCROLL is the same as READ BOOK or READ SCROLL
  elif current_word == "BOOKS" or current_word == "SCROLL":
    handle_read(game_context)

  # If we're in ROOM 43??? and EXAMINE WALL then
  elif current_room == 43 and current_word == "WALL":
    game_context['message'] = "THERE IS SOMETHING BEYOND..."

  # If we EXAMINE COFFIN, that is the same as OPEN COFFIN
  elif current_room == 32 and current_word == "COFFIN":
    handle_open(game_context)

# LINE 1140 - 1170 - VERB 14: "READ"
def handle_read(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling READ")

  # If we READ BOOKS
  if current_room == 42 and current_word == "BOOKS":
    game_context['message'] = "THEY ARE DEMONIC WORKS"

  if (current_word == "MAGIC SPELLS" or current_word == "SPELLS") and game_context['objects']['MAGIC SPELLS']['carrying'] is True and game_context['objects']['XZANFAR']['visible'] is True:
    game_context['message'] = "USE THIS WORD WITH CARE 'XZANFAR'"

  # 1160 IF C(5)=1 AND OH=5 THEN M&="THE SCRIPT IS IN AN ALIEN TONGUE” | formofRND here.
  # TODO: implement this line
  if current_word == "BOOK" and game_context['objects']['BOOK']['carrying'] is True:
    game_context['message'] = "THE SCRIPT IS IN AN ALIEN TONGUE"

# LINE 1180 - 1210 - VERB 15: "SAY"
def handle_say(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling SAY")

  game_context['message'] = f"OK '{current_word}'"

  if game_context['objects']['MAGIC SPELLS']['carrying'] is True and current_word == "XZANFAR":
    game_context['message'] = "*MAGIC OCCURS*"

    # If the user says "XZANFAR" and isn't in room 45, then sent them to random room (between room 0 and 63)
    if current_room != 45:
      game_context['room'] = randint(0,63) # send the user to a random room (between room 0 and 63)

    # If the user says "XZANFAR" and IS in room 45, then sent them to random room (between room 0 and 63)
    else:
      game_context['objects']['XZANFAR']['visible'] = False

# LINE 1220 - 1240 - VERB 16: "DIG"
def handle_dig(game_context):
  current_room = game_context['room'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling DIG")

  # If we're carrying a SHOVEL and DIG then we made a hole
  if game_context['objects']['SHOVEL']['carrying'] is True:
    game_context['message'] = "YOUR MADE A HOLE"

    # if we have a SHOVEL and are in room 30 (CELLAR) then we made a hole in the wall, so add an exit to the EAST and change the description from "CELLAR" to "HOLE IN WALL"
  if current_room == 30:
    game_context['message'] = "DUG THE BARS OUT"
    game_context['locations'][current_room]['description'] = "HOLE IN WALL"
    game_context['locations'][current_room]['routes'] = "NSE"
    # This means that from outside we can't get back down to the cellar again, as we didn't update the routes for room 31 (CLIFF PATH) to add a next exit to the WEST

# LINE 1250 - 1290 - VERB 17: "SWING"
def handle_swing(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability 

  if game_context['debug'] is True:
    print("Handling SWING")

  # if we haven't got the rope but are at BLASTED TREE (room 7) then
  if game_context['objects']['ROPE']['carrying'] is False and current_room == 17:
    game_context['message'] = "THIS IS NO TIME TO PLAY GAMES"

  # If you say "SWING ROPE and you have the ROPE
  if current_word == "ROPE" and game_context['objects']['ROPE']['carrying'] is True:
    game_context['message'] = "YOU SWUNG IT"

  # If you say "SWING AXE" and you have the AXE
  if current_word == "AXE" and game_context['objects']['AXE']['carrying'] is True:
    game_context['message'] = "WHOOSH!"

    # The original avoided nested if statements - were they not supported by all 8-bit computers?
    # If we're in room 43 (STUDY) and switch the AXE (which we've established we have)
    if current_room == 43:
      game_context['locations'][current_room]['routes'] = "WN" #Add another exit to STUDY to the NORTH
      game_context['locations'][current_room]['description'] = "STUDY WITH SECRET ROOM"
      game_context['message'] = "YOU BROKE THE WALL"

# LINE 1300 - 1330 - VERB 18: "CLIMB"
def handle_climb(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling CLIMB")

  # IF "CLIMB ROPE" but we're carrying it, no matter where we are
  if current_word == "ROPE" and game_context['objects']['ROPE']['carrying'] is True:
    game_context['message'] = "IT ISN'T ATTACHED TO ANYTHING"

  # If we are at the BLASTED, and aren't carrying the rope, then CLIMB ROPE
  # So the user must DROP rope at the BLASTED TREE in order to climb the rope
  # In the original the rope flag (F14) was used to record the status as to whether we were up the tree
  if current_word == "ROPE" and game_context['objects']['ROPE']['carrying'] is False and current_room == 7:
    if game_context['objects']['ROPE']['up_tree'] == False:
      game_context['message'] = "YOU SEE FORREST AND CLIFF SOUTH"
      game_context['objects']['ROPE']['up_tree'] = True
    elif game_context['objects']['ROPE']['up_tree'] == True:
      game_context['message'] = "GOING DOWN!"
      game_context['objects']['ROPE']['up_tree'] = False


# LINE 1340 - 1370 - VERB 19: "LIGHT"
def handle_light(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling LIGHT")

  if current_word == "CANDLE" and game_context['objects']['CANDLE']['carrying'] is True:

    # Setting up the logic to match to original
    if game_context['objects']['CANDLESTICK']['carrying'] is False:
      game_context['message'] = "YOU WILL BURN YOUR HANDS"

    # In the original F(0) was used for the candle status, we use objects['CANDLE']['lit']
    if game_context['objects']['MATCHES']['carrying'] is False:
      game_context['message'] = "NOTHING TO LIGHT IT WITH"
    elif game_context['objects']['MATCHES']['carrying'] is True:
      game_context['message'] = "IT CASTS A FLICKERING LIGHT"
      game_context['objects']['CANDLE']['lit'] = True

# LINE 1380 - 1390 - VERB 20: "EXTINGUISH"
# Only used for extinguishing the candle
def handle_unlight(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling EXTINGUISH")

  # Extinguish the candle
  if game_context['objects']['CANDLE']['lit'] is True:
    game_context['objects']['CANDLE']['lit'] = False
    game_context['message'] = "EXTINGUISHED"

# LINE - VERB 21: "SPRAY"
def handle_spray(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling SPRAY")

  if current_word == "BATS" and game_context['objects']['AEROSOL']['carrying'] is True:

    if game_context['objects']['BATS']['visible'] is True:
      messsage = "PFFT! GOT THEM"
    else:
      game_context['message'] = "HISSSS"

# LINE - VERB 22: "USE"
def handle_use(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling USE")

  # If we have the vacuum and the batteries, then turn it on
  if current_word == "VACUUM" and game_context['objects']['VACUUM']['carrying'] is True and game_context['objects']['BATTERIES']['carrying'] is True:
    game_context['message'] = "SWITCHED ON"
    game_context['objects']['VACUUM']['turned_on'] = True # originally the F24 "DOWN" flag was used for the vacuum state

    # If the vacuum is on and the ghosts are visible, then suck them up and the ghosts become no longer visible
    if game_context['objects']['GHOSTS']['visible'] is True:
      game_context['message'] = "WHIZZ - VACUUMED THE GHOSTS UP!"
      game_context['objects']['GHOSTS']['visible'] = False

# LINE 1460 - 1480. VERB 23: "UNLOCK"
def handle_unlock(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling UNLOCK")


  # LINE 1460
  # If we're in the study
  # There is a bug in the printed version availalbe online as A PDF (I'm not sure if there was ever a reprint)
  # If we are in the STUDY (room 43) and UNLOCK DESK or UUNLOCKSE DRAWER then we jump to the OPEN handler
  # In the code for this it was checking if we wrote UNLOCK + GHOST (object 27) or UNLOCK + DESK (object 28)
  # What they meant was UNLOCK + DESK (object 28) or UNLOCK + DRAWER (object 29)
  # This is definitely a bug, as in the original, the OPEN subroutine checks for objects 28 and 29 (not 27 and 28)
  # This also shows why we don't check for verbs in the handler, that is, so we can be flexible, UNLOCK drawer, or OPEN drawer should have the same result for example, although in our implementation, we can modify the verb anyway
  if current_room == 43 and (current_word == "DESK" or current_word == "DRAWER"):
    # Note that I haven't modified the verb to be OPEN isntead of UNLOCK
    handle_open(game_context)

  # OPEN DOOR in Hall
  # If we're in the HALL (ROOM 28) and asked "UNLOCK DOOR and door is VISIBLE (F25) and we are carrying the KEY (C18) then routes in the current room (lobby) update to "SEW" and description changes to "HUGE OPEN DOOR". message is "THE KEY TURNS!"
  if current_room == 28 and current_word == "DOOR" and game_context['objects']['DOOR']['visible'] is True and game_context['objects']['KEY']['carrying'] is True:
    game_context['locations'][current_room]['routes'] = "SEW"
    game_context['locations'][28]['description'] = "HUGE OPEN DOOR"
    game_context['message'] = "THE KEY TURNS!"
    # now the player can access the rooms SPIRAL STAIRCASE (20), DUSTY ROOM(12), and REAT TURRET ROOM (13)

# LINE - VERB 24: "LEAVE"
def handle_leave(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling LEAVE")

  if current_word in game_context['objects']: # make sure the word exists
    # drop "word" in current location, if we're carrying it
    if game_context['objects'][current_word]['carrying'] is True:
      game_context['objects'][current_word]['location'] = current_room
      game_context['objects'][current_word]['carrying'] = False
      game_context['message'] = "DONE"
  else:
    pass # do nothing


# LINE - VERB 25: "SCORE"
# Just add up how many items we have
def handle_score(game_context):
  current_room = game_context['room'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling SCORE")
  score = 0

  # loop through
  for current_word in game_context['objects']:
    if game_context['objects'][current_word]['carrying'] is True:
      score += 1

  # 17 means we have everything
  if score == 17:
    # So if the score is 17, and we don't have the boat (as we can't carry the boat to the exit), then tell the player to return to the GATE to complete the game
    if game_context['objects']['BOAT']['carrying'] is False:
      print("YOU HAVE EVERYTHING")
      print("RETURN TO GATE FOR FINAL SCORE")
    if current_room == 57:
      print("DOUBLE SCORE FOR REACHING HERE!")
      score *= 2

  print(f"YOUR SCORE={score}")

    # SCORE is only > 18 if we have returned to the gate, which doubles our score, and only does so if our score is already 17
  if score > 18:
    print("WELL DONE! YOU FINISHED THE GAME")
    sys.exit()

  input("PRESS RETURN TO CONTINUE")



def handle_save_game(game_context):
  current_room = game_context['room'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling SAVE")

  # Write the object to a file
  # When loading or saving a pickle file using the with open(...) context manager in Python, you do not need to explicitly close the file. The context manager automatically handles opening and closing the file for you, ensuring that resources are properly managed and that the file is closed even if an error occurs.
  with open('write-your-own-adventure-computer-game.pkl', 'wb') as file:
    try:
      dump(game_context, file)
      game_context['message'] = "GAME SAVED"
    except:
      print(f"Error encountered:")# {e}")
      game_context['message'] = "GAME SAVE FAILED"

# TODO: This function isn'tw orking, for some reason the game_context is not being loaded,
def handle_load_game(game_context):
  current_room = game_context['room'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling LOAD")

  # Write the object to a file
  # When loading or saving a pickle file using the with open(...) context manager in Python, you do not need to explicitly close the file. The context manager automatically handles opening and closing the file for you, ensuring that resources are properly managed and that the file is closed even if an error occurs.
  if os.path.exists('write-your-own-adventure-computer-game.pkl'):
    # Read the object from a file
    with open('write-your-own-adventure-computer-game.pkl', 'rb') as file:
      try:
#        game_context = load(file)
        loaded_game_context = load(file)
#        game_context = copy.deepcopy(loaded_game_context)
        #pprint(game_context)
#        print_game_context_changes(game_context, loaded_game_context)
        # Clear the existing game_context dictionary
        # Doing a deepcopy didn't work, so instead clear and update
        game_context.clear()  # Clear the existing game_context dictionary
        game_context.update(loaded_game_context)  # Update with loaded data (merge, which is bad if the save file is from an old version of the game!)
        game_context['message'] = "GAME LOADED"
      except:
#        print(f"Error encountered: {e}")
        game_context['message'] = "GAME LOAD FAILED"
  else:
    game_context['message'] = "GAME SAVE FILE NOT FOUND"

# Not in the original.
# TODO: Disable this
# If the user types "DUMP" we just dump the entire game_context to the screen
# Good luck sifting through that!
def handle_dump(game_context):
  current_room = game_context['room'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling DUMP")
  pprint(game_context)

  game_context['message'] = "GAME DUMP COMPLETE"

def handle_debug(game_context):
  current_room = game_context['room'] # set this for code readability
  current_verb = game_context['verb'] # set this for code readability
  current_word = game_context['word'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling DEBUG")

  match current_word:
    case "ON":
      game_context['debug'] = True
      game_context['message'] = "GAME DEBUG ON"
    case "OFF":
      game_context['debug'] = False
      game_context['message'] = "GAME DEBUG OFF"
    case _:
      # The only parameters are debug on or off
      game_context['message'] = "USAGE: DEBUG ON|OFF"

# Not in the original.
# TODO: Disable this
def handle_quit(game_context):
  current_room = game_context['room'] # set this for code readability

  if game_context['debug'] is True:
    print("Handling QUIT")
  sys.exit()

def main():

  # Display the welcome message
  display_welcome_message()

  # Setup initial variables
  game_context = {} # this will hold the game state
  init(game_context)

  # When debug is first enabled, it will display a diff of the original context
  # and the changes since, so take a copy of the game_context after initialisaion
  old_game_context = copy.deepcopy(game_context)

  while(True):
    current_room = game_context['room'] # set this for code readability

    # Game Play

    # If DEBUG is enabled, dump the game_context

    # print_game_context_changes is a debug function that prints the diff of the previous and current game_context, so takes two objects, old and dew context
    if game_context['debug'] is True:
      print_game_context_changes(old_game_context, game_context)



    # Lines 90 onward
    print(f'HAUNTED HOUSE')
    print(f'-------------')
    print(f'YOUR LOCATION:')
    print(f"{game_context['locations'][current_room]['description']}")# (room:{current_room})")
    # In the original a semi-colon after the print statement meant to print without a newline character
    print(f'EXITS:')

    # This is a lot easier in Python than in C, no for loop required
    # routes just contains a string e.g. "NWE", meaning exists to North, West and East
    print(','.join(game_context['locations'][current_room]['routes']))

    display_visible_items(game_context)

    print(f"{game_context['message']}") #this is the message from the last action
    game_context['message']="WHAT" # reset message


    # Analysis of Input
    # (Page 21 is the original explanation)
    # we do some things here that weren't done in the original
    game_context['query'] = input('WHAT WILL YOU DO NOW\n')

    analyse_input(game_context)

    #print(f"analyse_input:MESSAGE:{game_context['message']}")

    #
    # Handle Override Coniditions
    #

    # Line 440. Page 18
    # In the original F(0) was used for the candle status, this is because
    # The candle has two states, lit and visible. LL was used to track
    # how long the candle could stay lit, and was decremented on each move
    # Perhaps LL means Light Limit?
    # We are going to keep all these variables in our objects list

    # If the candle is lit, decrement the counter
    get_candle_status_message(game_context)



    # Line 420
    # If bats are present, player is in Rear Turret Room, random number is not 3 and player hasn't used verb 21 (SPRAY) in his instructions, then M$ is set to "BATS ATTACKING" and player cannot go any further in the game.
    if check_bats_status(game_context):
      game_context['message'] = "BATS ATTACKING"
      continue

    # Line 430
    # If player is in Cobwebby Room, random number value is 1 and vacuum cleaner is switched off, then flag is set for paralysing ghosts to appear, i.e. F(27) is set to 1.
    ghosts_randomly_appear_in_cobwebby_room(game_context)




    #input("PRESS RETURN TO CONTINUE:")

    # Line 460 GOSUB verb handling
#    print(f"verb:{verb}")
#    print(f"word:{word}")
    handle_verb(game_context)

#    print(f"interim message:{game_context['message']}")
#    print(f"game_context['locations'][49]['routes']:{game_context['locations'][49]['routes']}")

    # Line 470 Candle Status messages
    # the candle status will overwrite the current messsage
    get_candle_status_message(game_context)
    #print(f"interim message:'{message}'")

    # loop ends
    # this is spaghetti code

    # Line 450
    # If LL is zero, then candle on/off flag, F(0), is set to zero.

if __name__ == "__main__":
  main()
