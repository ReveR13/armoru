# ../colors.py

"""Provides Color objects with RGBA values."""

# =============================================================================
# >> FORWARD IMPORTS
# =============================================================================
# Source.Python Imports
#   Colors
from _colors import Color


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ('GOLD',
           'IMMORTAL',
           'ANCIENT',
           'LEGENDARY',
           'BLUEVIOLET',
           'AZURE',
           'BLUWHITE'
	   )


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
GOLD = Color(255, 215, 0)  #:
IMMORTAL = Color(228, 174, 51)  #: Immortal DOTA2
ANCIENT = Color(235, 75, 75) #: Redish color DOTA2
LEGENDARY = Color(211, 44, 230) #: Legendary purplish color
BLUEVIOLET = Color(138, 43, 226) #: Blue Violet
AZURE = Color(0, 127, 255) # Azure color
BLUWHITE = Color(240, 240, 255) #Blueish White