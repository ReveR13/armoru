# based on most_damage.py by satoon101, url = "http://forums.sourcepython.com/viewtopic.php?f=7&t=64"
# ../armoru/armoru.py

'''
Single damage reduction
helmet 1 = 0.10, 0.14, 0.22, 0.34, 0.50
helmet 1.5 = 0.15, 0.195, 0.285, 0.42, 0.60 (decreased, from 0.055 to 0.045 per level)
helmet 2 = 0.175, 0.2275, 0.3325, 0.49, 0.70 (increased by 0.0525 per level)

armor = [0, 7, 14, 18, 25, 30] percent

decreased ontakedamage damage

0.8     added armor repair on kill
        1/11 critical rate + heal on crit
0.10    rework damage bypass through armored
0.11    rewrite ontakedamage
0.13    cash bonus now working
0.14    added boots + falldamage
0.15    rewrite 1/3 code, added smiley on crit
0.16    added speed up/down
0.18.6  reworked prearmor condition
0.19    weapon script rebalance
0.21    rework dmgcut, added flashbang to freeze, nvgs on flash
0.22    huge update, much rework, damage simplyfy
0.23    0.22 fix: reserve ammo, weight, drop weapon
0.24    0.23 fix predamage, added armor ratio
0.25    fix small part
'''

# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python
from config.manager import ConfigManager
from colors import Color
from colors import WHITE, PURPLE, YELLOW, RED, GREEN, DARK_RED, LIGHT_GREEN, OLIVE
from engines.sound import Sound
from entities import TakeDamageInfo
from entities.constants import DamageTypes
from entities.entity import BaseEntity, Entity
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook, EntityPostHook
from memory import make_object
from events import Event
from events.hooks import PreEvent
from filters.players import PlayerIter
from filters.weapons import WeaponClassIter
from listeners.tick import Delay, Repeat
from memory import make_object
from messages import HintText
from messages import HudDestination
from messages import HudMsg, SayText2, KeyHintText, TextMsg
from players.constants import HitGroup, HideHudFlags
from players.entity import Player
from players.helpers import index_from_userid, userid_from_index
from pprint import pprint
from settings.player import PlayerSettings
from stringtables import string_tables
from time import time
from weapons.entity import Weapon

from mathlib import Vector

import math, random, soundlib

# Additional
from .colors import GOLD, BLUWHITE, AZURE, BLUEVIOLET, LEGENDARY, IMMORTAL, ANCIENT
from .colors import BLUBLU, BLEK, ORANGE, NOTRED, OLDRED, SILVERY


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================


# BLUWHITE, AZURE, BLUEVIOLET, GOLD, ANCIENT
armor_colour = {0: SILVERY, 1: AZURE, 2: BLUEVIOLET, 3: ORANGE, 4: GOLD, 5: DARK_RED, 6: SILVERY}
round_bonus_color = {0: WHITE, 1: BLUWHITE, 2: AZURE, 3: BLUEVIOLET, 4: IMMORTAL, 5: YELLOW, 6: GOLD, 7: ANCIENT, 8: RED, 9: DARK_RED, 10: DARK_RED}
hit_color = {0: BLUWHITE, 1: DARK_RED, 2: BLUBLU, 3: GOLD, 4: ORANGE, 5: ORANGE, 6: OLIVE, 7: OLIVE, 8: BLUEVIOLET, 9: BLUWHITE, 10: SILVERY}

rainbow = [ANCIENT, ORANGE, GOLD, OLIVE, BLUBLU, BLUEVIOLET, PURPLE]
rainbow2 = [LEGENDARY, ORANGE, YELLOW, OLIVE, AZURE, BLUEVIOLET, PURPLE]

round_count = 0
round_bonus = {0: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 1, 7: 2, 8: 2, 9: 2, 10: 2, 11: 3, 12: 3, 13: 3, 14: 3, 15: 4, 16: 4, 17: 4, 18: 5, 19: 5, 20: 5, 21: 6, 22: 7, 23: 8, 24: 9, 25: 10}

maxboots = {0: 24, 1: 30, 2: 36, 3: 45, 4: 54, 5: 64}

dmg_bonus = [0, 0, 1, 1, 1, 2, 4]
#dmgmod = {0: 1.0, 1: 0.92, 2: 0.85, 3: 0.82, 4: 0.76, 5: 0.70, 6: 0.60} # 8, 15, 18, 25, 30, 40 LEGACY
#dmgmod = {0: 1.0, 1: 0.90, 2: 0.82, 3: 0.76, 4: 0.70, 5: 0.64, 6: 0.60} # 10, 18, 24, 30, 36, 40 BUFFED
dmgmod = {0: 1.0, 1: 0.92, 2: 0.86, 3: 0.82, 4: 0.80, 5: 0.76, 6: 0.72} # 8, 14, 20, 24, 28, 30 ADJUSTED
dmgmod2 = {0: 1.0, 1: 0.95, 2: 0.90, 3: 0.88, 4: 0.86, 5: 0.84, 6: 0.80} # dmgmod 

# >>>  W E A P O N   C A T E G O R Y ==++==++==++==++
spe = ['deagle', 'm3', 'knife', 'tknife', 'tknifehs'] #0.32
ar = ['aug', 'ak47', 'm4a1', 'famas', 'sg552', 'm249'] #0.1
pistol = ['glock', 'usp', 'p228', 'elite', 'fiveseven'] #0.12
smg = ['mac10', 'tmp', 'mp5navy', 'ump45', 'p90', 'galil'] #0.09
sniper = ['awp', 'scout'] #0.24
dmr = ['sg550', 'g3sg1', 'xm1014'] #0.14

primeweapon = [weapon.basename for weapon in WeaponClassIter(is_filters='primary')]
secondweapon = [weapon.basename for weapon in WeaponClassIter(is_filters='secondary')]
specials = ['deagle', 'fiveseven', 'scout', 'm3', 'xm1014'] #multi bullet weapon


""" OLD WEIGHT
weightsmg = {'mac10': 0.019, 'tmp': 0.019, 'mp5navy': 0.026, 'ump45': 0.026, 'p90': 0.026, 'galil': 0.031}
weightar = {'famas': 0.034, 'ak47': 0.035, 'm4a1': 0.035, 'sg552': 0.035, 'aug': 0.035, 'm249': 0.054}
weightsniper = {'scout': 0.039, 'awp': 0.049, 'g3sg1': 0.033, 'sg550': 0.046}
weightshot = {'m3': 0.034, 'xm1014': 0.044}
"""

weightsmg = {'mac10': 0.028, 'tmp': 0.029, 'mp5navy': 0.035, 'ump45': 0.036, 'p90': 0.030, 'galil': 0.031}
weightar = {'famas': 0.042, 'ak47': 0.043, 'm4a1': 0.041, 'sg552': 0.042, 'aug': 0.042, 'm249': 0.059}
weightsniper = {'scout': 0.046, 'awp': 0.055, 'g3sg1': 0.036, 'sg550': 0.053}
weightshot = {'m3': 0.044, 'xm1014': 0.042}

weights2 = {'glock': 0.018, 'usp': 0.020, 'p228': 0.022, 'deagle': 0.026, 'elite': 0.032, 'fiveseven': 0.017}

'''
spe = ['weapon_deagle', 'weapon_m3', 'weapon_knife'] #0.32
ar = ['weapon_aug', 'weapon_ak47', 'weapon_m4a1', 'weapon_famas', 'weapon_sg552', 'weapon_m249'] #0.1
pistol = ['glock', 'usp', 'p228', 'elite', 'fiveseven'] #0.12
smg = ['weapon_mac10', 'weapon_tmp', 'weapon_mp5navy', 'weapon_ump45', 'weapon_p90', 'weapon_galil'] #0.09
sniper = ['weapon_awp', 'weapon_scout'] #0.24
dmr = ['weapon_sg550', 'weapon_g3sg1', 'weapon_xm1014'] #0.14
'''

# damage multiplier non critical (other, head, body, stomach, legs)
spe_dmg_mult = {0: 0.99, 1: 0.96, 2: 1.10, 3: 1.06, 4: 0.97, 5: 0.96, 6: 0.95, 7: 0.96, 10: 0.90}
asr_dmg_mult = {0: 0.95, 1: 0.93, 2: 1.05, 3: 0.94, 4: 0.95, 5: 0.95, 6: 1.00, 7: 1.00, 10: 0.95}
pst_dmg_mult = {0: 0.95, 1: 0.90, 2: 0.96, 3: 0.88, 4: 0.95, 5: 0.95, 6: 0.80, 7: 0.80, 10: 0.85}
smg_dmg_mult = {0: 1.00, 1: 0.92, 2: 1.16, 3: 1.00, 4: 0.98, 5: 0.98, 6: 0.90, 7: 0.90, 10: 0.92}
dmr_dmg_mult = {0: 1.05, 1: 0.90, 2: 1.12, 3: 1.00, 4: 1.05, 5: 1.05, 6: 1.04, 7: 1.04, 10: 0.90}
snp_dmg_mult = {0: 1.10, 1: 1.00, 2: 1.21, 3: 1.13, 4: 1.08, 5: 1.09, 6: 1.12, 7: 1.14, 10: 0.90}

# damage multiplier on CRITICAL (other, head, body, stomach, legs)  #buffed
spe_crit_mult = {0: 1.15, 1: 1.12, 2: 1.24, 3: 1.20, 4: 1.17, 5: 1.19, 6: 1.15, 7: 1.16, 10: 1.02}
asr_crit_mult = {0: 1.10, 1: 1.10, 2: 1.25, 3: 1.16, 4: 1.08, 5: 1.08, 6: 1.17, 7: 1.17, 10: 0.99}
pst_crit_mult = {0: 1.05, 1: 1.08, 2: 1.12, 3: 1.05, 4: 1.02, 5: 1.02, 6: 0.94, 7: 0.94, 10: 0.91}
smg_crit_mult = {0: 1.10, 1: 1.05, 2: 1.32, 3: 1.19, 4: 1.09, 5: 1.09, 6: 1.07, 7: 1.07, 10: 0.98}
dmr_crit_mult = {0: 1.20, 1: 1.02, 2: 1.24, 3: 1.21, 4: 1.20, 5: 1.20, 6: 1.15, 7: 1.15, 10: 0.99}
snp_crit_mult = {0: 1.25, 1: 1.30, 2: 1.48, 3: 1.30, 4: 1.20, 5: 1.20, 6: 1.25, 7: 1.25, 10: 1.00}

# ADD DAMAGE BONUS TO ARMORED
spe_dmg_bns = {0: 0.23, 1: 0.18, 2: 0.26, 3: 0.14, 4: 0.26, 5: 0.27, 6: 0.30, 7: 0.29, 10: 0.26}
asr_dmg_bns = {0: 0.20, 1: 0.12, 2: 0.23, 3: 0.13, 4: 0.18, 5: 0.21, 6: 0.20, 7: 0.24, 10: 0.18} #BASE
pst_dmg_bns = {0: 0.21, 1: 0.11, 2: 0.22, 3: 0.15, 4: 0.19, 5: 0.20, 6: 0.16, 7: 0.16, 10: 0.22}
smg_dmg_bns = {0: 0.24, 1: 0.13, 2: 0.21, 3: 0.19, 4: 0.25, 5: 0.24, 6: 0.23, 7: 0.23, 10: 0.23}
dmr_dmg_bns = {0: 0.22, 1: 0.11, 2: 0.17, 3: 0.15, 4: 0.25, 5: 0.25, 6: 0.25, 7: 0.25, 10: 0.27}
snp_dmg_bns = {0: 0.20, 1: 0.10, 2: 0.18, 3: 0.14, 4: 0.20, 5: 0.20, 6: 0.17, 7: 0.18, 10: 0.19}

# WEAPON KICK RATE
spe_push = {'deagle': 0.1, 'm3': 0.2, 'knife': 0.04}
asr_push = {'aug': 0.033, 'ak47': 0.03, 'm4a1': 0.025, 'famas': 0.03, 'sg552': 0.03, 'm249': 0.05}
pst_push = {'glock': 0.018, 'usp': 0.019, 'p228': 0.028, 'elite': 0.029, 'fiveseven': 0.024} #0.12
smg_push = {'mac10': 0.012, 'tmp': 0.013, 'mp5navy': 0.015, 'ump45': 0.017, 'p90': 0.012, 'galil': 0.025} #0.09
snp_push = {'awp': 0.07, 'scout': 0.04} #0.24
dmr_push = {'sg550': 0.03, 'g3sg1': 0.022, 'xm1014': 0.1}

# WEAPON ARMOR RATIO (from scripts/weapon_ )
spe_ratio = {'deagle': 1.24, 'm3': 0.926, 'knife': 1.69, 'tknife': 1.5, 'tknifehs': 1.75} #1.285
asr_ratio = {'aug': 1.24, 'ak47': 1.27, 'm4a1': 1.08, 'famas': 1.10, 'sg552': 1.40, 'm249': 1.24} #1.22
pst_ratio = {'glock': 0.68, 'usp': 0.61, 'p228': 0.91, 'elite': 0.88, 'fiveseven': 1.036} #0.8212
smg_ratio = {'mac10': 0.79, 'tmp': 0.76, 'mp5navy': 0.86, 'ump45': 0.76, 'p90': 0.90, 'galil': 1.15} #0.87
snp_ratio = {'awp': 1.42, 'scout': 1.37} #1.395
dmr_ratio = {'sg550': 1.28, 'g3sg1': 1.05, 'xm1014': 0.885} #1.055

# RESERVE AMMO EDIT
spe_ammo = {'deagle': 24, 'm3': 35, 'knife': 2, 'tknife': 2, 'tknifehs': 2}
asr_ammo = {'aug': 90, 'ak47': 90, 'm4a1': 120, 'famas': 100, 'sg552': 90, 'm249': 250}
pst_ammo = {'glock': 100, 'usp': 48, 'p228': 52, 'elite': 90, 'fiveseven': 80} #0.12
smg_ammo = {'mac10': 120, 'tmp': 160, 'mp5navy': 120, 'ump45': 100, 'p90': 200, 'galil': 140} #0.09
snp_ammo = {'awp': 12, 'scout': 40} #0.24
dmr_ammo = {'sg550': 90, 'g3sg1': 100, 'xm1014': 40}

critical_mod = {'spe': 5.0, 'ar': 10.0, 'pistol': 9.0, 'smg': 9.5, 'snp': 5.5, 'dmr': 7.5} #nerfed

cashbonus = {0: 2, 1: 9, 2: 2.7, 3: 5.5, 4: 1.6, 5: 1.6, 6: 1.2, 7: 1.2, 10: 16}
cashbonusw = {'spe': 22, 'ar': 8, 'pistol': 12, 'smg': 16, 'snp': 40, 'dmr': 20}

x0 = random.randint(0, 6)
y0 = random.choice([0, 1, 2, 3, 4])

total_dmg = 0
tempdmg = 0
timer = 2.4
timeroff = 0
delaybleed = 0
crit_rng = 1
pickup = 1
cashback = 4
bleeds = 0
running = False
gacha = 0

boom = 'armoru/boomheadshot.mp3'
hedshot = 'armoru/ding.mp3'
acrack = 'armoru/cracked.mp3'
hcrack = 'armoru/break.mp3'
abreak = 'armoru/abreak.mp3'
hbreak = 'armoru/hbreak.mp3'
bobreak = 'armoru/tsurara.mp3'
lvlsound = 'armoru/levelup.mp3'
throw = 'armoru/throw.mp3'
critsound = 'armoru/flip.mp3'

equipment = ['vesthelm', 'vest', 'nvgs', 'defuser', 'c4']
weighteq = {'vesthelm': 0.030, 'vest': 0.020, 'nvgs': 0.003, 'defuser': 0.007, 'c4': 0.020}

throwable = ['knife', 'tknife', 'tknifehs', 'hegrenade', 'flashbang', 'smokegrenade']
hitboxes = {0: 'GENERIC', 1: 'HEAD', 2: 'BODY', 3: 'STOMACH', 4: 'LEFTARM', 5: 'RIGHTARM', 6: 'LEFTLEG', 7: 'RIGHTLEG', 10: 'GEAR'}
levelsymbol = {0: ' ', 1: ' + ', 2: ' + + ', 3: ' + + + ', 4: ' ~ ~ ~ ~ ', 5: ' # # # # # ', 6: ' O O O O O O '}
critsymbol = [' ( @__v__@ ) ', ' ! ! ! ! ! ', ' & # % @ ! $ ', ' d(*v*)b ', ' (^O^)/ ~ ~ ']
armorsym = {0: ' ', 1: ' > ', 2: ' >> ', 3: ' > > > ', 4: ' > > > > ', 5: ' # # # # # ', 6: ' O O O O O O '}
armorsym2 = {0: ' ', 1: ' ! ', 2: ' ! ! ', 3: ' ! ? ! ', 4: ' ! ! ! ! ', 5: ' # # # # # ', 6: ' O O O O O O '}

weaponbonus50 = ['knife', 'tknife', 'tknifehs']
weaponbonus25 = ['glock', 'mac10', 'tmp', 'galil', 'elite']
weaponbonus10 = ['scout', 'deagle', 'p90', 'p228', 'm3']

"""
weaponbonus50 = ['weapon_knife']
weaponbonus25 = ['weapon_glock', 'weapon_m3', 'weapon_mac10', 'weapon_tmp', 'weapon_galil', 'weapon_elite']
weaponbonus10 = ['weapon_scout', 'weapon_deagle', 'weapon_p90', 'weapon_fiveseven', 'weapon_p228']
"""

PLAYERS = dict()
PDamage = {}
AllDamage = {}

CT_DMG = {}
T_DMG = {}
TCT_DMG = {}

GACHA = {}

# =============================================================================
# >> CLASSES
# =============================================================================

class _ArmorA(dict):
    """Armor Reworks for Counter Strike Source, display damage info and more. Created by KTMN_CH"""

    def __init__(self):
        """Create the user settings."""
        # Call super class' init
        super().__init__()
    
    def __missing__(self, userid):
        """Add the userid to the dictionary with the default values."""
        value = self[userid] = {'maxhp': 100, 'health': 100, 'initarmor': 25, 'armorhp': 25, 'helmet': 0, 'helmhp': 0, 'level': 0, 'damage': 0, 'nextlvl': 150, 'recharge': 3, 'dmgcut': 0, 'dmgblock': 1, 'dmgred': 0, 'streak': 0, 'hit': 0, 'shot': 0, 'tempdmg': 0, 'bleed': 0, 'nvgs': 0, 'speed': 1.0, 'maxspeed': 1.05, 'carry': 0.1, 'primary': '0', 'secondary': '0', 'boots': 24, 'gacha': 0}
        return value

    def __delitem__(self, userid):
        """Verify the userid is in the dictionary before removing them."""
        if userid in self:
            super().__delitem__(userid)
            
    def check_weight(self, item): # deagle, ak47, etc
        if item in equipment:
            weight = weighteq[item]
        elif item in pistol or item == 'deagle':
            weight = weights2[item]
        elif item == 'm3' or item == 'xm1014':
            weight = weightshot[item]
        elif item in ar:
            weight = weightar[item]
        elif item in smg:
            weight = weightsmg[item]
        elif item in sniper or item == 'sg550' or item == 'g3sg1':
            weight = weightsniper[item]
        else:
            weight = 0.007
        return weight
    
    def _check_push(self, weapon):
        if weapon in pistol:
            pushrate = pst_push[weapon]
        elif weapon in spe:
            pushrate = spe_push[weapon]
        elif weapon in ar:
            pushrate = asr_push[weapon]
        elif weapon in smg:
            pushrate = smg_push[weapon]
        elif weapon == 'awp' or weapon == 'scout':
            pushrate = snp_push[weapon]
        elif weapon in dmr:
            pushrate = dmr_push[weapon]
        else:
            pushrate = 0.01
        return pushrate
    
    # ARMOR RATIO CHECK
    def _check_armor_ratio(self, weapon):
        if weapon in spe:
            armor_ratio = spe_ratio[weapon] / 1.21
        elif weapon in pistol:
            armor_ratio = pst_ratio[weapon] / 1.12 # BASE
        elif weapon in ar:
            armor_ratio = asr_ratio[weapon] / 1.30
        elif weapon in smg:
            armor_ratio = smg_ratio[weapon] / 1.08
        elif weapon == 'awp' or weapon == 'scout':
            armor_ratio = snp_ratio[weapon] / 1.42
        elif weapon in dmr:
            armor_ratio = dmr_ratio[weapon] / 1.40
        else:
            armor_ratio = 0.56
        return armor_ratio
    
    # WEIGHT CHECK ON WEAPON PICK UP
    def item_pick(self, user, player, item):
        prefix = 'weapon_'
        picked = prefix + item
        if item in equipment or item in throwable:
            return
        elif picked in (secondweapon):
            self[user]['speed'] -= armora.check_weight(item)
        elif picked in (primeweapon):
            self[user]['speed'] -= (armora.check_weight(item) + 0.004)
        
        player.speed = max(0.76, min(self[user]['maxspeed'], self[user]['speed']))
        SayText2('ITEM PICK: \x03{:.3f} \n'.format(player.speed)).send(index_from_userid(user))
        
    def niu_weapon(self, player, weapon): # new weapon from shop
        #if pickup: # and player.in_buy_zone == 1
        #niuweapon = weapon.classname.replace('weapon_', '', 1)
        
        if player.primary: #weapon in primeweapon and 
            #if player.primary.classname.replace('weapon_', '', 1) == weapon:
            niuweapon = player.primary
            gun1 = player.primary.classname.replace('weapon_', '', 1)
            if gun1 in spe:
                niuweapon.ammo = spe_ammo[gun1]
            elif gun1 in ar:
                niuweapon.ammo = asr_ammo[gun1]
            elif gun1 in smg:
                niuweapon.ammo = smg_ammo[gun1]
            elif gun1 in sniper:
                niuweapon.ammo = snp_ammo[gun1]
            elif gun1 in dmr:
                niuweapon.ammo = dmr_ammo[gun1]
            else:
                return
        if player.secondary: #weapon in secondweapon and 
            #if player.secondary.classname.replace('weapon_', '', 1) == weapon:
            niuweapon2 = player.secondary
            gun2 = player.secondary.classname.replace('weapon_', '', 1)
            if gun2 in pistol:
                niuweapon2.ammo = pst_ammo[gun2]
            elif gun2 == 'deagle':
                niuweapon2.ammo = spe_ammo[gun2]
            else:
                return
            #niuweapon = weapon.classname.replace('weapon_', '', 1)
        SayText2('NEW AMMO !').send(userid_from_index(player.index))
    
        
    def player_weapon(self, user, player):
        if player.dead:
            return
        if player.primary:
            self[user]['primary'] = player.primary.classname.replace('weapon_', '', 1)
        else:
            self[user]['primary'] = '0'
        if player.secondary:
            self[user]['secondary'] = player.secondary.classname.replace('weapon_', '', 1)
        else:
            self[user]['secondary'] = '0'
    
    def shopping(self, game_event):
        global cashback
        shopper = game_event['userid']
        player = Player(index_from_userid(shopper))
        item = str(game_event['item'])
        rngcash = random.randint(1,6)
        #SayText2('ITEM: {}'.format(item)).send(index_from_userid(shopper))
        
        if item in throwable:
            weight = 0.005
            if item == 'knife':
                weight -= 0.002
        elif item == 'c4':
            weight = 0.020
        elif item == 'defuser':
            weight = 0.007
        elif item in primeweapon or item in secondweapon:
            armora.item_pick(shopper, player, item)
            weight = 0.00
        else:
            weight = 0.00
        self[shopper]['speed'] -= weight
        
        #SayText2('\x03ITEM: {}'.format(item)).send(index_from_userid(shopper))
        #player.delay(0.15, armora.item_pick, (shopper, player, item))
        
        """if player.primary: #self[shopper]['primary'] != '0':
            weaponheavy = player.primary.classname.replace('weapon_', '', 1)
            if armora._check_carry(shopper, weaponheavy) == 0:
                if player.secondary:
                    player.set_active_weapon(player.secondary)
                else:
                    player.drop_weapon(player.primary)
                #player.primary.remove()
        """
        
        if pickup: #pickup enabled 20 sec from spawn
            if (item == "vesthelm"):
                if self[shopper]['helmet'] == 0: #no helmet no nvgs
                    if self[shopper]['armorhp'] <= 25:
                        self[shopper]['speed'] -= 0.030
                    else:
                        self[shopper]['speed'] -= 0.010
                    self[shopper]['helmet'] = 1
                    self[shopper]['dmgcut'] = max(0.12, self[shopper]['dmgcut'])
                    for i in range(self[shopper]['level'] + 1):
                        self[shopper]['dmgcut'] += (0.024 * i)
                    self[shopper]['dmgcut'] = min(0.40, self[shopper]['dmgcut'])
                elif self[shopper]['helmet'] <= 0.5: #have nvgs, add helmet
                    if self[shopper]['armorhp'] <= 25:
                        self[shopper]['speed'] -= 0.030
                    else:
                        self[shopper]['speed'] -= 0.010
                    self[shopper]['helmet'] += 1
                    self[shopper]['dmgcut'] += 0.12
                    if self[shopper]['helmhp'] > 20:
                        for i in range(self[shopper]['level'] + 1):
                            self[shopper]['dmgcut'] += (0.03 * i)
                    else:
                        for i in range(self[shopper]['level'] + 1):
                            self[shopper]['dmgcut'] += (0.024 * i)
                    self[shopper]['dmgcut'] = min(0.50, self[shopper]['dmgcut'])
                elif self[shopper]['helmet'] == 1: #rehelmet only
                    if self[shopper]['armorhp'] <= 25:
                        self[shopper]['speed'] -= 0.020
                    self[shopper]['dmgcut'] = max(0.12, self[shopper]['dmgcut'])
                    if self[shopper]['helmhp'] > 20:
                        for i in range(self[shopper]['level'] + 1):
                            self[shopper]['dmgcut'] += (0.036 * i)
                    else:
                        for i in range(self[shopper]['level'] + 1):
                            self[shopper]['dmgcut'] += (0.030 * i)
                    self[shopper]['dmgcut'] = min(0.48, self[shopper]['dmgcut'])
                elif self[shopper]['helmet'] <= 1.5: #have both
                    if self[shopper]['armorhp'] <= 25:
                        self[shopper]['speed'] -= 0.020
                    self[shopper]['dmgcut'] = max(0.25, self[shopper]['dmgcut'])
                    if self[shopper]['helmhp'] > 20:
                        for i in range(self[shopper]['level'] + 1):
                            self[shopper]['dmgcut'] += (0.040 * i)
                    else:
                        for i in range(self[shopper]['level'] + 1):
                            self[shopper]['dmgcut'] += (0.032 * i)
                    self[shopper]['dmgcut'] = min(0.60, self[shopper]['dmgcut'])
                else: #helmet 2 level 4
                    self[shopper]['dmgcut'] = 0.16
                    for i in range(self[shopper]['level'] + 1):
                        self[shopper]['dmgcut'] += (0.048 * i)
                    self[shopper]['dmgcut'] = min(0.76, self[shopper]['dmgcut'])
                    
                if self[shopper]['recharge'] <= 1:
                    self[shopper]['recharge'] += 1.5
                    
                if self[shopper]['level'] == 3:
                    self[shopper]['armorhp'] = max(75, self[shopper]['armorhp'])
                    self[shopper]['dmgblock'] = min(60, max(self[shopper]['armorhp'], self[shopper]['dmgblock']))
                else:
                    self[shopper]['armorhp'] = max(60, self[shopper]['armorhp'])
                nvgsplus = 10 if self[shopper]['nvgs'] == 1 else 0
                self[shopper]['helmhp'] = max(40 + nvgsplus, self[shopper]['helmhp'])

            elif (item == "vest"):
                if self[shopper]['armorhp'] <= 25:
                    self[shopper]['speed'] -= 0.020
                if self[shopper]['recharge'] <= 1:
                    self[shopper]['recharge'] += 1
                if self[shopper]['level'] == 3:
                    self[shopper]['armorhp'] = max(75, self[shopper]['armorhp'])
                    self[shopper]['dmgblock'] = min(45, max(self[shopper]['armorhp'], self[shopper]['dmgblock']))
                else:
                    self[shopper]['armorhp'] = max(60, self[shopper]['armorhp'])
            
            elif (item in "nvgs"):
                self[shopper]['nvgs'] = 1
                self[shopper]['helmhp'] += 10
                self[shopper]['helmhp'] = min(50, self[shopper]['helmhp'])
                self[shopper]['maxhp'] += 10
                self[shopper]['helmet'] += 0.5
                self[shopper]['dmgcut'] += 0.05

            player.delay(0.14, armora.armordelay, (player, self[shopper]['helmhp'], self[shopper]['armorhp']))
            #Delay(0.16, armora.armor_now, (shopper, player))
            
        if player.in_buy_zone == 1:
            if rngcash % 4 == 0 and cashback and round_count > 1:
                if item in throwable:
                    cashrngbonus = 50
                elif item in weaponbonus25:
                    cashrngbonus = 200
                elif item in weaponbonus10:
                    cashrngbonus = 125
                else:
                    cashrngbonus = 100
                cashback -= 1
                Delay(0.8, armora.cash_back, (shopper, player, cashrngbonus))
                SayText2('\x04CASHBACK: +{} !!\n'.format(cashrngbonus)).send(index_from_userid(shopper))
                #armora.player_weapon(shopper, player)
            if item in primeweapon or item in secondweapon:
                player.delay(6.0, armora.niu_weapon, (player, item))
        
        player.speed = min(self[shopper]['maxspeed'], max(0.76, self[shopper]['speed']))
        #player.speed = max(0.67, min(1.05, self[shopper]['speed']))
        #SayText2('Your Speed: {:.3f} \n'.format(player.speed)).send(index_from_userid(shopper))
    
    def _check_ammo_clip(self, user, weapon):
        player = Player(index_from_userid(user))
        if (weapon in primeweapon) or (weapon in secondweapon):
            ammo = weapon.ammo
            clip = weapon.clip
            SayText2('CLIP: {}, AMMO: {}\n'.format(clip, ammo)).send(index_from_userid(user))
            return ammo
    
    def healtharmor(self, game_event):
        """ Assign player health and armor """
        user = game_event['userid']
        player = Player(index_from_userid(user))
        player.armor = min(125, max(0, self[user]['helmhp'] + self[user]['armorhp']))
        player.health = min(125, max(0, self[user]['health']))
        
        if self[user]['helmhp'] > 1:
            if self[user]['helmet'] < 1.0:
                self[user]['helmet'] == 1.0
        
        armora.armor_now(user, player)
        
    def armordelay(self, player, helm, armor):
        """ Assign player health and armor """
        #player = Player(index_from_userid(user))
        user = userid_from_index(player.index)
        if not player.dead:
            self[user]['helmhp'] = helm
            self[user]['armorhp'] = armor
            player.armor = min(125, max(0, self[user]['helmhp'] + self[user]['armorhp']))
        
        player.delay(0.14, armora.armor_now, (user, player))

        """if self[user]['health'] < 1 and not player.dead:
            SayText2('YOU ARE DEAD \n').send(index_from_userid(user))
            player.health -= 999"""
        #SayText2('\x03ARMORDELAY\n').send(index_from_userid(user))
        
    def healthdelay(self, user, hp):
        player = Player(index_from_userid(user))
        #user = index_from_userid(player.index)
        self[user]['health'] = hp
        #player.health = self[user]['health']
        if hp < 1 and not player.dead:
            player.health = self[user]['health']
            player.health -= 1000
            SayText2('\x03YOU DIED \n \n').send(index_from_userid(user))
            player.slay
        else:            
            player.health -= int((player.health - hp))
            player.armor = min(125, max(0, self[user]['helmhp'] + self[user]['armorhp']))
        #SayText2('\x04HEALTH DELAY\n').send(index_from_userid(user))
        #armora.armor_now(user, player)


    def spawn_armor(self, user, player):
        """Add spawn armor."""
        self[user]['bleed'] = 0
        hpadd = 10 if self[user]['nvgs'] == 1 else 0
        if self[user]['health'] < 100:
            self[user]['health'] = 100 + hpadd
        else:
            self[user]['health'] = max(self[user]['maxhp'], self[user]['health'])
            
        if self[user]['level'] == 3:
            self[user]['health'] = min(115 + hpadd, self[user]['maxhp'])
            self[user]['armorhp'] = max(40, self[user]['armorhp'])
        
        if self[user]['armorhp'] < 25:
            if self[user]['helmhp'] > 0:
                self[user]['armorhp'] = 20
            else:
                self[user]['armorhp'] = self[user]['initarmor']
        elif (self[user]['armorhp'] + self[user]['helmhp']) >= 100:
            if self[user]['recharge'] <= 1.5:
                self[user]['recharge'] += 1.0
              
        if self[user]['boots'] < maxboots[self[user]['level']]:
            self[user]['boots'] += int((maxboots[self[user]['level']] - self[user]['boots']) / 1.5)
            
        if self[user]['helmhp'] > 0:
            player.has_helmet == 1
            
        if user in PDamage:
            PDamage[kil] = 0
        
        player.speed = self[user]['speed'] if round_count != 1 else 1.0
        player.delay(0.12, armora.armordelay, (player, self[user]['helmhp'], self[user]['armorhp']))
        #player.delay(0.25, armora._check_ammo_clip, (user, player.active_weapon))
        #armora.healtharmor(game_event)
        """        DEBUG
        user = 0
        print('MaxHp: {}, Level: {}'.format(self[user]['health'], self[user]['level']))
        print('Helm: {}, DmgCut: {}'.format(self[user]['helmet'], self[user]['helmhp'], self[user]['dmgcut']))
        print('HelmHP: {}, ArmorHP: {}'.format(self[user]['helmhp'], self[user]['armorhp']))
        """

    def spawn_cash(self, user, player):
        """BONUS CASH on SPAWN."""
        spawncashbonus = 175
        if round_count > 2:
            for i in range(self[user]['level']): # 0-5
                spawncashbonus -= (25 * i) #175 150 125 100 75 50
            spawncashbonus += 125 if self[user]['armorhp'] > self[user]['initarmor'] else 0
            player.cash += spawncashbonus
            SayText2('\x03CASH BONUS: +{} \n'.format(spawncashbonus)).send(index_from_userid(user))
    
    def spawn_speed(self, user, player):
        if self[user]['speed'] <= 0.76:
            self[user]['speed'] += (0.8 - self[user]['speed'])
    
    def spawn_weapon(self, user, player):
        player.unrestrict_weapons(*primeweapon)
        player.unrestrict_weapons(*secondweapon)
        self[user]['carry'] += 0.04 if self[user]['carry'] < 0.05 else 0
        """if player.primary and player.primary == player.active_weapon:
            weapon = player.primary.classname.replace('weapon_', '', 1)
            #SayText2('Your 1st weapon is \x03{}\n'.format(weapon)).send(index_from_userid(user))
            if armora._check_carry(user, weapon) == 0:
            #player.restrict_weapons(*primeweapon)
                if player.secondary:
                    player.set_active_weapon(player.secondary)
                else:
                    player.drop_weapon(player.primary)
        """
        if pickup:
            player.delay(6.4, armora.niu_weapon, (player, 'ak47'))
            #player.delay(6.4, armora.niu_weapon, (player, 'deagle'))

    
    def _check_killer(self, game_event):
        victim = game_event['userid']
        #self[victim]['speed'] = 1.0

    
    # A D D    D A M A G E    T O    K I L L E R
    def add_kill(self, game_event):
        global total_dmg
        global PDamage
        
        victim = game_event['userid']
        #self[victim]['speed'] = 1.0
        
        try:
            attacker = game_event['attacker']
            player = Player(index_from_userid(attacker))
        except:
            attacker = None
            player = None
            return
        
        if game_event['attacker'] in (victim, 0): # U N T E S T E D
            if attacker != victim:
                self[victim]['speed'] = 1.0
            return
        
        player3 = Player(index_from_userid(victim))
        
        if victim == attacker:
            return
        
        #=========================================
        headshot = game_event['headshot']
        revenge = game_event['revenge']     # true (1)
        weapon2 = game_event['weapon']
        streakbonus = 0
        headshotbonus = 0
        
        # Add a kill to the attacker's stats
        self[attacker]['streak'] += 1
        if self[attacker]['streak'] > 2:
            armora.show_streak(attacker)
        
        #check weapon bonus for kill
        if weapon2 in weaponbonus50:
            self[attacker]['damage'] += (1 + self[attacker]['nextlvl'] - self[attacker]['damage'])
            total_dmg += 75
        elif weapon2 in weaponbonus25:
            self[attacker]['damage'] += 15
            total_dmg += 25
        elif weapon2 in weaponbonus10:
            self[attacker]['damage'] += 8
            total_dmg += 10
        
        #check if revenge kill and recover attacker's armor
        diff = max(0, self[victim]['level'] - self[attacker]['level'])
        if revenge == 1:
            self[attacker]['damage'] += (20 + (diff * 20))
            total_dmg += (12 + (diff * 20))
            player.cash = min(12000, player.cash + 500)
            for i in range(self[victim]['streak'] + 1):
                streakbonus += ((i - 1) * 30) if (i > 2) else 0
            for i in range(diff + 1):
                headshotbonus += (10 + (i * 10))
                
            if self[attacker]['recharge'] >= 1:
                if (0 < self[attacker]['armorhp'] <= 50):
                    self[attacker]['armorhp'] += 20
                if (0 < self[attacker]['helmhp'] <= 30) and self[attacker]['helmet'] > 0:
                    self[attacker]['helmhp'] += 14
            else:
                return
        else:
            for i in range(self[victim]['streak'] + 1):
                streakbonus += ((i - 1) * 20) if (i > 2) else 0
            for i in range(diff + 1):
                headshotbonus += (5 + (i * 4))
                
            if self[attacker]['recharge'] >= 1:
                if (0 < self[attacker]['armorhp'] <= 40):
                    self[attacker]['armorhp'] += 8
                if (0 < self[attacker]['helmhp'] <= 25) and self[attacker]['helmet'] >= 1:
                    self[attacker]['helmhp'] += 5
            else:
                return

        #check if headshot and recover armor and maxhp
        if headshot:
            self[attacker]['damage'] += headshotbonus
            total_dmg += headshotbonus
            
            player.cash = min(12000, player.cash + 250)
            player3.cash = max(0, player3.cash - 175)
                
            if self[attacker]['recharge'] < 1:
                return
            
            if (0 < self[attacker]['armorhp'] < 40):
                self[attacker]['armorhp'] += (8 + (self[attacker]['level'] * 2))
            
            if (0 < self[attacker]['helmhp'] < 25) and self[attacker]['helmet'] > 0.5:
                if self[attacker]['helmet'] <= 1:
                    self[attacker]['helmhp'] += (6 + (self[attacker]['level'] * 1)) # 6 + 1 2 3 4 5
                elif self[attacker]['helmet'] <= 1.5:
                    self[attacker]['helmhp'] += (6 + (self[attacker]['level'] * 3)) # 6 + 3 6 9 12 15
                else:
                    self[attacker]['helmhp'] += (5 + (self[attacker]['level'] * 5)) # 5 + 5 10 15 20 25
            
            if (12 <= self[attacker]['health'] < 60):
                self[attacker]['health'] += 16
            else:
                self[attacker]['health'] += 10
        else:
            if player3.cash >= 75:
                player.cash = min(12000, player.cash + 125)
                player3.cash -= 75

        self[attacker]['damage'] += streakbonus
        total_dmg += streakbonus
        vct = player3.name #str(victim)
        kil = player.name #str(attacker)
        
        #PDamage[vct] = self[victim]['damage']
        #PDamage[kil] = self[attacker]['damage']
        SayText2('{}: \x04{}\x01 VS \x03{}\x01 :{}\n'.format(vct, PDamage[vct], PDamage[kil], kil)).send(index_from_userid(victim))
        SayText2('{}: \x03{}\x01 VS \x04{}\x01 :{}\n'.format(kil, PDamage[kil], PDamage[vct], vct)).send(index_from_userid(attacker))
        
        player.armor = min(125, self[attacker]['armorhp'] + self[attacker]['helmhp'])
        player.health = min(125, self[attacker]['health'])
        player.delay(0.12, armora.armordelay, (player, self[attacker]['helmhp'], self[attacker]['armorhp']))
        #player.delay(0.16, armora.armor_now, (attacker, player))
        #player.delay(0.15, armora._check_distance, (player3, player))
        player.delay(0.16, armora.check_level, (attacker, player))
        
        armora.__delitem__(victim)
        return
        #=========================================
        
    def worldamage(self, game_event):
        victim = game_event['userid']
        player = Player(index_from_userid(victim))
        #damage = game_event['dmg_health']
        damage = int(game_event['damage'])
        armora.show_damage_boots(victim, player, damage)
        
        if self[victim]['boots'] > 0:
            self[victim]['boots'] -= int(damage)
            player.delay(0.15, armora._player_speed_down, (victim, player))
            #player.delay(0.2, armora.healthdelay, (victim, self[victim]['health']))
            if self[victim]['boots'] <= 0:
                soundlib.playgamesound(victim, bobreak)
                player.delay(0.4, armora._player_crippled, (victim, player, damage))
        else:
            player.delay(0.4, armora._player_crippled, (victim, player, damage))
            self[victim]['health'] -= damage
        
        player.health = self[victim]['health']
        #player.delay(0.2, armora.healthdelay, (player, self[victim]['health']))
        player.delay(0.12, armora.healthdelay, (victim, self[victim]['health']))
        #SayText2('\x03BOOTS: {}, MAXHP: {}\n'.format(self[victim]['boots'], self[victim]['health'])).send(index_from_userid(victim))
        

    # = = = = = = = = = = = = = = = = = = = = = = = =
    def apply_damage(self, victim, damage):
        player = Player(index_from_userid(victim))
        
        self[victim]['health'] -= damage
        player.armor = self[victim]['armorhp'] + self[victim]['helmhp']
        player.health = self[victim]['health']
        
    def add_damage(self, game_event):
        """Add the damage for the player."""
        global total_dmg
        global armour
        global dmg
        global maxhp
        global PDamage
        global TCT_DMG
        
        try:
            victim = game_event['userid']
        except:
            victim = None
            return
        
        # World damage?
        """if game_event['attacker'] == 0:
            #self[victim]['speed'] = 1.0
            attacker = 0
            return
        else:
            attacker = game_event['attacker']"""
            
        try:
            attacker = game_event['attacker']
            player2 = Player(index_from_userid(attacker))
        except:
            attacker = None
            player2 = None
            return
        
        key = str(game_event['userid'])
        player = Player(index_from_userid(victim))
        
        global tempdmg
        global round_count
        
        # total_dmg = 0
        dmg = 0
        dmghelm = 0
        dmgtrue = 0
        
        delaybleed = 0
        
        if key not in PLAYERS:
            PLAYERS[key] = 0
        PLAYERS[key] += 1
    
        # Is this self inflicted?
        if attacker in (victim, 0):
            return
        
        if player2.dead: #not player2.is_player or 
            return
        
        if not player2.is_player: # or not player2.is_bot:
            return

        # Was this a team inflicted?
        if player2.team == player.team:
            return
        
        damager = index_from_userid(attacker)
        
        damage = game_event['dmg_health']
        bedil = str(game_event['weapon'])
        
        #armor level 3 dmg block
        hitbox = game_event['hitgroup']
        if self[victim]['dmgblock'] > 1:
            hitbox == 2
        
        #check CRIT DMG MOD
        dmgmult = armora.dmgcrit_mult(bedil, hitbox)
        add_mult = armora.adddmg_mult(bedil, hitbox)
        
        # Add dmgbonus to attacker and dmgcut to victim
        dmgbonus = random.choice(dmg_bonus) + round_bonus[round_count]
        dmgcut = self[victim]['dmgcut']
        dmgred = self[victim]['dmgred']
        
        # CALCULATE ARMOUR DAMAGE
        """if game_event['dmg_armor'] == 0:
            armour0 = int(predamage * armora._check_armor_ratio(bedil))
        else:
            armour0 = game_event['dmg_armor']"""
        armour0 = int(predamage * armora._check_armor_ratio(bedil))
        armour = int((armour0 * (dmgmult + add_mult)) * dmgmod[self[victim]['level']]) # + dmgbonus
        
        if armora._check_armor_ratio(bedil) > 0.76:
            dmgmaxhp = int((armour0 * dmgmult) * dmgmod2[self[victim]['level']])
        else:
            dmgmaxhp = int((predamage * 0.76 * dmgmult) * dmgmod2[self[victim]['level']])
        dmgtrue = int(predamage * dmgmult)
        #SayText2('CRIT RNG : {}'.format((crit_rng))).send(index_from_userid(attacker))
        
        maxhp = self[victim]['health']
        helmhp = self[victim]['helmhp']
        armorhp = self[victim]['armorhp']
        
        self[attacker]['hit'] += 1
        colorm = RED
        
        #start tempdmg timer
        if not running:
            armora._start_tempdmg(victim, 2.4)

        #CHECK BLEED
        #if delaybleed > 0 and game_event['attacker'] not in (-1, 0):
        #delaybleed = armora._check_bleed(victim, damager, dmgmaxhp)
        
        # DAMAGE CALCULATION FOR PLAYER HURT
        if hitbox == 1: #HEADSHOT
            soundlib.playgamesound(attacker, hedshot)
            #player.hidden_huds = 1
            if self[victim]['nvgs'] == 1 and random.randint(1, 3) == 2:
                armora.player_nvgsbroken(victim, player)
            if (self[victim]['helmhp'] > 0): #HELMETED VICTIM
                dmghelm = int((armour0 * (dmgmult + add_mult)) * (1 - dmgcut))
                if dmghelm > helmhp: # DMG > Helmet armor --> Minus max hp
                    dmghead = max(4, int((dmghelm - helmhp) * max(0.1, 0.72 - dmgcut)))
                    self[victim]['helmhp'] = 0
                    self[victim]['health'] -= min(self[victim]['health'], max(dmghead, 1))
                    self[victim]['dmgcut'] -= ((self[victim]['level'] + self[victim]['helmet']) * 0.040)
                    self[victim]['dmgcut'] = max(0.0, self[victim]['dmgcut'])
                    self[victim]['helmet'] = max(0.4, (self[victim]['helmet'] - 1))
                    self[victim]['recharge'] -= 0.5
                    self[victim]['speed'] += 0.004
                    player.speed = self[victim]['speed']
                    player.has_helmet = 0
                    helmhp = 0
                    player2.delay(0.1, armora.cash_bonus, (victim, attacker, hitbox, bedil))
                    soundlib.playgamesound(attacker, hcrack)
                    soundlib.playgamesound(victim, hbreak)
                else:
                    self[victim]['helmhp'] -= min(self[victim]['helmhp'], dmghelm + dmgbonus)
                    helmhp = self[victim]['helmhp']
                    player.has_helmet = 1 if self[victim]['helmhp'] > 0 else 0
                armora.show_damage_helmet(dmghelm, victim)
            else: #NO HELMET
                if (prearmor > 0): # have armor no helm
                    armour = dmgmaxhp + dmgbonus #0.95 * 4.0 * 0.64 * lvlmod
                else:
                    armour = dmgtrue + dmgbonus #0.95 * 4.0 * 0.64 * lvlmod
                #dmg = min(int(armour / 24), 4) # 42/20 = 1.6 -> (2 + 42 + bonus)
                player2.delay(0.11, armora.cash_bonus, (victim, attacker, hitbox, bedil))
                self[victim]['health'] -= min(armour, self[victim]['health'])
                colorm = NOTRED
                delaybleed = armora._check_bleed(victim, damager, dmgmaxhp)
                if delaybleed > 0 and self[victim]['bleed'] == 0:
                    player.delay(0.12, armora._start_bleeding, (delaybleed, victim, player, attacker))
        elif (hitbox == 2): # Body shot
            if self[victim]['armorhp'] > 0:
                #self[victim]['armorhp'] -= armour
                if self[victim]['dmgblock'] > 1:
                    armourb = min(12, max(6, int(armour * 0.72)))
                    self[victim]['dmgblock'] = max(0, self[victim]['dmgblock'] - armourb)
                    if self[victim]['dmgblock'] < 1:
                        self[victim]['armorhp'] = 0
                        self[victim]['health'] -= 25
                elif ((armour - dmgred) > armorhp):
                    dmgbody = max(1, int((armour - dmgred - armorhp) * 0.56)) + dmgbonus
                    self[victim]['health'] -= min(self[victim]['health'], max(dmgbody, 1))
                    self[victim]['armorhp'] = 0
                    self[victim]['recharge'] -= 1
                    self[victim]['speed'] += 0.012
                    player.speed = self[victim]['speed']
                    armorhp = 0
                    player2.delay(0.1, armora.cash_bonus, (victim, attacker, hitbox, bedil))
                    soundlib.playgamesound(attacker, acrack)
                    soundlib.playgamesound(victim, abreak)
                    if self[victim]['level'] > 0:
                        self[victim]['nextlvl'] -= (100 + (150 * self[victim]['level']))
                        self[victim]['level'] -= 1
                        self[victim]['damage'] = self[victim]['nextlvl'] - (100 + (self[victim]['level'] * 150))
                        self[victim]['damage'] = max(0, self[victim]['damage'])
                else:
                    self[victim]['armorhp'] -= min(self[victim]['armorhp'], armour + dmgbonus - dmgred)
                    armorhp = self[victim]['armorhp']
                armora.show_damage_armored(armour, victim)
            else: #NO ARMOR
                if prearmor > 0: # have at least 1 armor point
                    armour = int(dmgmaxhp + dmgbonus - dmgred) # 0.76
                else:
                    armour = int(dmgtrue + dmgbonus) #-  0.85) 
                #dmg = min(int(armour / 8), 1) # 7.5 + bonus / 2.5 = (3 + 7.5)
                player2.delay(0.11, armora.cash_bonus, (victim, attacker, hitbox, bedil))
                self[victim]['health'] -= min(self[victim]['health'], max(armour, 1))
                colorm = NOTRED
                delaybleed = armora._check_bleed(victim, damager, dmgmaxhp)
                if delaybleed > 0 and self[victim]['bleed'] == 0:
                    player.delay(0.13, armora._start_bleeding, (delaybleed, victim, player, attacker))
        elif (hitbox == 3):
            if (self[victim]['armorhp'] > 0) and (self[victim]['level'] >= 1):
                armour = int((armour0 * (dmgmult + add_mult)) * dmgmod2[self[victim]['level']])
                if ((armour - dmgred) > armorhp):
                    dmgbody = max(1, int((armour - dmgred - armorhp) * 0.52)) + dmgbonus
                    self[victim]['health'] -= dmgbody
                    self[victim]['armorhp'] = 0
                    self[victim]['recharge'] -= 1
                    self[victim]['speed'] += 0.010
                    player.speed = self[victim]['speed']
                    armorhp = 0
                    soundlib.playgamesound(attacker, acrack)
                    soundlib.playgamesound(victim, abreak)
                    if self[victim]['level'] >= 1:
                        self[victim]['nextlvl'] -= (100 + (150 * self[victim]['level']))
                        self[victim]['level'] -= 1
                        for i in range(self[victim]['level']):
                            self[victim]['damage'] -= (75 + (i * 100))
                            self[victim]['damage'] = max(0, self[victim]['damage'])
                else:
                    self[victim]['armorhp'] -= min(self[victim]['armorhp'], armour + dmgbonus - dmgred)
                    armorhp = self[victim]['armorhp']
                armora.show_damage_armored(armour, victim)
            else:
                if prearmor > 0:
                    armour = int(dmgmaxhp + dmgbonus - dmgred) 
                else:
                    armour = int(dmgtrue + dmgbonus) # * 0.72) + 
                #dmg = min(max(int(armour / 12), 1), 3) # 9 / 2.5 = (3 + 9)
                player2.delay(0.11, armora.cash_bonus, (victim, attacker, hitbox, bedil))
                # player.armor = self[victim]['helmhp']
                self[victim]['health'] -= min(self[victim]['health'], max(armour, 2))
                colorm = NOTRED
                delaybleed = armora._check_bleed(victim, damager, dmgmaxhp)
                if delaybleed > 0 and self[victim]['bleed'] == 0:
                    player.delay(0.12, armora._start_bleeding, (delaybleed, victim, player, attacker))
        elif hitbox in (4, 5): #ARM HIT
            armour = int((dmgmaxhp * 1.05) - dmgred) + dmgbonus  # 1 * 0.9
            dmg = min(2, max(armour // 7, 0)) # at least 7 damage
            self[victim]['health'] -= min(self[victim]['health'], max(armour, 1))
            if dmg > 0:
                self[victim]['carry'] = max(0.030, self[victim]['carry'] - (0.009 * dmg))
                userbedil = player.active_weapon.classname.replace('weapon_', '', 1)
                armora.show_damage_arms(dmg, victim)
                if armora._check_carry(victim, userbedil) == 0:
                    player.drop_weapon(player.active_weapon)
                    player.restrict_weapons(*primeweapon)
                    player.delay(7.0, armora._carry_recover, (victim, player))
                """player.set_active_weapon(player.secondary)
                if player.primary and (player.primary == player.active_weapon):
                    #player.restrict_weapons(*primeweapon)
                    #player.drop_weapon(player.primary)
                    #player.primary.remove()
                """
            player2.delay(0.11, armora.cash_bonus, (victim, attacker, hitbox, bedil))
            colorm = NOTRED
            delaybleed = armora._check_bleed(victim, damager, dmgmaxhp)
            if delaybleed > 0 and self[victim]['bleed'] == 0:
                player.delay(0.12, armora._start_bleeding, (delaybleed, victim, player, attacker))
        elif hitbox in (6, 7): #LEG HIT, 6 LEFT, 7 RIGHT
            if self[victim]['boots'] > 0:
                armour = max(4, int((armour * 1.12) - 1)) + dmgbonus # 0.75 * 0.9
                dmg = min(3, max(1, int(armour // 7))) # 3 + bonus / 2.5 = (1 + 3 + bonus)
                if self[victim]['boots'] > armour:
                    self[victim]['boots'] -= armour
                    player.delay(0.15, armora._player_speed_down, (victim, player))
                else:
                    dmgboots = int((armour - self[victim]['boots']) * 0.56)
                    self[victim]['health'] -= min(self[victim]['health'], max(dmgboots, 1))
                    self[victim]['speed'] = max(0.76, self[victim]['speed'] - (0.06 * dmg))
                    player.speed = self[victim]['speed']
                    self[victim]['boots'] = 0
                    soundlib.playgamesound(victim, bobreak)
                    player.delay(0.27, armora._player_crippled, (victim, player, dmgboots))
                    #player.health = self[victim]['health']
                    #player.delay(0.18, armora.healthdelay, (victim, self[victim]['health']))
                HudMsg(
                    message='{} ({:.3f})'.format(armour, self[victim]['speed']),
                    hold_time=2.25,
                    fade_out=2.75,
                    x=0.555,
                    y=0.535,
                    color1 = OLIVE,
                    channel=4
                ).send(damager)
            else: #NO BOOTS
                armour = max(1, (int(dmgtrue * 1.05) - dmgred)) + dmgbonus # 0.75 * 0.9
                dmg = min(2, max(1, armour // 12)) # 3 + bonus / 2.5 = (1 + 3 + bonus)
                self[victim]['speed'] = max(0.67, self[victim]['speed'] - (0.14 * dmg))
                player.speed = self[victim]['speed'] #perma slow
                self[victim]['health'] -= min(self[victim]['health'], max(armour, 1))
                player2.delay(0.11, armora.cash_bonus, (victim, attacker, hitbox, bedil))
                colorm = NOTRED
                delaybleed = armora._check_bleed(victim, damager, dmgmaxhp)
                if delaybleed > 0 and self[victim]['bleed'] == 0:
                    player.delay(0.12, armora._start_bleeding, (delaybleed, victim, player, attacker))
        elif hitbox == 10: #GEAR HIT
            armour = max(1, int(dmgmaxhp * 1.08) - (dmgred + 1)) + dmgbonus
            #dmg = min(max(int(armour / 6), 1), 2)
            if player.has_defuser == 1 and (random.randint(1, 3) == 2):
                player.has_defuser = 0
                armour = int(dmgmaxhp * 0.89) + dmgbonus - (dmgred + 1)
                #dmg = min(max(int(armour / 7), 1), 2)
            self[victim]['health'] -= min(self[victim]['health'], max(armour, 2))
            player2.delay(0.1, armora.cash_bonus, (victim, attacker, hitbox, bedil))
            colorm = NOTRED
        else:
            armour = max(1, int(dmgtrue * 1.10) - (dmgred + 1)) + dmgbonus
            self[victim]['health'] -= min(self[victim]['health'], max(armour, 2))
            player2.delay(0.1, armora.cash_bonus, (victim, attacker, hitbox, bedil))
            colorm = NOTRED
        
        player.health = self[victim]['health']
        player.delay(0.09, armora.healthdelay, (victim, self[victim]['health']))
        player.delay(0.12, armora.armordelay, (player, self[victim]['helmhp'], self[victim]['armorhp']))
        
        """if helmhp > 0 and self[victim]['helmhp'] < helmhp: #
            dmgtaken = helmhp - self[victim]['helmhp']
            player.delay(0.17, armora.show_damage_helmet, (dmgtaken, victim))"""
        
        if self[victim]['armorhp'] < armorhp: #armorhp > 0 and 
            vestdmg = armorhp - self[victim]['armorhp']
            player.delay(0.18, armora.show_damage_armored, (vestdmg, victim))
        
        if maxhp > 0 and self[victim]['health'] < maxhp:
            armors = (maxhp - self[victim]['health'])
            player.delay(0.15, armora.show_damage_maxhp, (victim, hitbox, armors))
            
        # add damage to user damage
        self[attacker]['damage'] += max(armour, dmghelm)
        self[victim]['tempdmg'] += max(armour, dmghelm)
        #tempdmg += max(armour, dmghelm)
        total_dmg += max(armour, dmghelm)
            
        # CRITICAL RATE + HEAL ON CRIT ========================
        if (0 <= crit_rng <= 0.5):
            #player2.speed = min(1.16, player2.speed + 0.04)
            #armora._player_speed_up(attacker, player2, 0.025)
            critcolour = BLUBLU
            armora.show_crit(attacker)
            soundlib.playgamesound(attacker, critsound)
            if (15 <= player2.health < 75):
                hpheal = min(8, max(2, ((predamage // 12) - (self[attacker]['health'] // 10))))
                self[attacker]['health'] = min(self[attacker]['health'] + hpheal, self[attacker]['maxhp'])
                HudMsg(
                    message='+{}'.format(hpheal), # healed
                    hold_time=2.5,
                    fade_out=3.0,
                    x=0.112,
                    y=0.939, #0.06 * 720
                    color1 = LIGHT_GREEN,
                    channel=11 # 11 maxhp, 12 helm
                ).send(damager)
            if (8 < self[attacker]['armorhp'] < 50) and player2.health >= 100:
                armorheal = min(4, max(0, (armour // 9))) # int(armour * 0.225)
                self[attacker]['armorhp'] = min(75, self[attacker]['armorhp'] + armorheal)
                HudMsg(
                    message='+{}'.format(armorheal), # repaired armor
                    hold_time=2.5,
                    fade_out=3.0,
                    x=0.27,
                    y=0.952, #0.06 * 720
                    color1 = armor_colour[self[attacker]['level']],
                    channel=13  # 11 maxhp, 12 harmor, 13 armor2
                ).send(damager)
            """if (8 < self[attacker]['helmhp'] <= 30):
                helmheal = min(4, max(0, (armour // 4)))
                self[attacker]['helmhp'] += helmheal #int(armour * 0.175)
                HudMsg(
                    message='+{}'.format(helmheal), # repaired helm
                    hold_time=2.5,
                    fade_out=3.0,
                    x=0.27,
                    y=0.918, #0.06 * 720
                    color1 = armor_colour[self[attacker]['level']],
                    channel=12  # 11 maxhp, 12 harmor2
                ).send(damager)"""
            
            player2.armor = min(125, self[attacker]['armorhp'] + self[attacker]['helmhp'])
            player2.health = min(125, self[attacker]['health'])
            player2.delay(0.10, armora.armordelay, (player2, self[attacker]['helmhp'], self[attacker]['armorhp']))
            #player2.delay(0.18, armora.armor_now, (attacker, player2))
        elif colorm == RED:
            critcolour = armor_colour[self[victim]['level']]
        else:
            critcolour = colorm
        armora._show_dmg_player(attacker, self[victim]['tempdmg'], crit_rng, critcolour, bedil, PLAYERS[key])
        #armora._damage_round(attacker, player2, armour)
        player2.delay(0.15, armora.check_level, (attacker, player2))
        player2.delay(0.25, armora._damage_round, (attacker, player2, armour))
        
        vct = player.name #str(victim)
        kil = player2.name #str(attacker)
        
        if kil not in PDamage:
            PDamage[kil] = 0
        else:
            PDamage[kil] += max(armour, dmghelm) #self[attacker]['damage']
            
        if kil not in TCT_DMG:
            TCT_DMG[kil] = 0
        else:
            TCT_DMG[kil] += max(armour, dmghelm)
        
        pdistance = armora._check_distance(player2, player)
        
    """DEBUG
        #print('===== ==+== =++== =+++= ==++= ==+== =====')
        print('+++   ++   +On    Damage+   ++   +++')
        print('{} {} DMG to {} on {} at {}'.format(kil, bedil, vct, hitboxes[hitbox], pdistance))
        print('LVL: {}, DMGCUT: {:.2f}'.format(self[victim]['level'], dmgcut))
        print('DMGBLOCK: {}, DMGRED: {}'.format(self[victim]['dmgblock'], dmgred))
        print('  ')
        print('Dmg_Health: {}, Dmg_Armor: {}'.format(game_event['dmg_health'], game_event['dmg_armor']))
        #print('Health_After: {}, Armor_Left: {}'.format(game_event['health'], game_event['armor']))
        print('ARMOUR0: {}, BONUS: {}'.format(armour0, dmgbonus))
        print('DMGHELM: {}, ARMOUR: {}'.format(dmghelm, armour))
        print('USERARMOR HP: {}, USERHELM HP: {}'.format(self[victim]['armorhp'], self[victim]['helmhp']))
        print('Player.Health: {}, Player.Armor: {}'.format(player.health, player.armor))
        print('HP AFTER: {}, DMGTRUE: {}'.format(self[victim]['health'], dmgtrue))
        print('  ')"""
    

    def _show_dmg_player(self, attacker, dmg, crit, color, bedil, key):
        damager = index_from_userid(attacker)
        
        #RANDOM coordinate value
        #x0 = (random.randint(1, 5) * 0.0145) + (random.randint(2, 4) * 0.0105)
        x1 = armora.random_x0(x0)
        xa = 0.657 - (x1 * 0.0225)
        #y0 = random.choice([0, 1, 2, 3, 4]) #armora.random_ya(ya0)
        y1 = armora.random_y0(y0)
        ya = 0.521 - min(0.419, ((dmg // (6 + y1)) * 0.0223))
        
        dmg2 = max(1, dmg)
        #check attacker streak for rainbow damage number
        if (self[attacker]['streak'] > 5) or (bedil == 'm249'):
            HudMsg(
                message=str(dmg2), # armour
                hold_time = 2.4,
                fade_out = 3.1,
                fx_time = 0.9,
                effect = 2,
                x=xa,
                y=ya,
                color1 = random.choice(rainbow),
                color2 = random.choice(rainbow2),
                channel=key
	        ).send(damager)
        elif crit <= 0.5 or bedil in (throwable): # C R I T
            HudMsg(
                message=str(dmg2),
                hold_time = 2.5,
                fade_out = 3.2,
                fx_time = 1.2,
                effect = 2,
                x=0.6,
                y=0.4,
                color1 = BLUBLU,
                color2 = GOLD,
                channel=key
	        ).send(damager)
        elif self[attacker]['streak'] < 5:
            HudMsg(
                message=str(dmg2), # armour
                hold_time = 1.6,
                fade_out = 2.1,
                x=xa,
                y=ya,
                color1 = color,
                channel=key
	        ).send(damager)

    #   CHECK ARMOR LEVEL UP +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
    def check_level(self, attacker, player2):
        #check new ARMOR LVL and Calculate DMG CUT and DMG REDUCTION
        if (self[attacker]['damage'] > self[attacker]['nextlvl']) and (self[attacker]['level'] <= 3):
            self[attacker]['level'] += 1
            self[attacker]['nextlvl'] += (100 + (self[attacker]['level'] * 150)) # 100 + level*150 5vs5 3/round
            soundlib.playgamesound(attacker, lvlsound)
            armora._player_color_update(attacker, self[attacker]['level'])
            
            if self[attacker]['recharge'] < 1:
                return
            
            harmor2 = self[attacker]['helmhp']
            armor2 = self[attacker]['armorhp']
            maxhptemp = self[attacker]['health']
            
            armor_repair = (125 - (15 * self[attacker]['level'])) #125, 110, 95, 80, 65
            armorhp_fix = (64 - (6 * self[attacker]['level'])) # max 60 --> 64, 58, 52, 46, 40
            helmhp_fix = (46 - (4 * self[attacker]['level'])) # max 40 --> 42, 38, 34, 30, 26
            
            if self[attacker]['boots']:
                self[attacker]['boots'] += int(6 * self[attacker]['level'])
                self[attacker]['boots'] = min(maxboots[self[attacker]['level']], self[attacker]['boots'])
                if self[attacker]['level'] >= 4:
                    player2.speed += 0.05
            
            # recover maxhp by medium ammount
            if self[attacker]['level'] == 3:
                self[attacker]['maxhp'] += 15
                self[attacker]['maxhp'] = min(125, self[attacker]['maxhp'])
                self[attacker]['health'] = self[attacker]['maxhp']
            elif self[attacker]['health'] > 80: # 81 --> max
                self[attacker]['health'] = 100
            elif self[attacker]['health'] >= 50: # 79 --> 50
                self[attacker]['health'] += (self[attacker]['level'] * 8) # max (+ 16 health)
            elif self[attacker]['health'] >= 25: # 49 --> 25
                self[attacker]['health'] += int(self[attacker]['level'] * 10) # max (+ 20 health)
            elif self[attacker]['health'] > 0: # 1 --> 25
                self[attacker]['health'] += 25
            self[attacker]['health'] = min(self[attacker]['maxhp'], self[attacker]['health'])
            
            # check repair armor on level up
            if (0 < player2.armor < armor_repair) and self[attacker]['level'] < 4:
                # repair armorhp by medium ammount
                if (0 < self[attacker]['armorhp'] < armorhp_fix): #48 36 24 12
                    if self[attacker]['level'] == 3:
                        self[attacker]['armorhp'] += 40
                        self[attacker]['armorhp'] = min(75, self[attacker]['armorhp'])
                    else:
                        self[attacker]['armorhp'] += (10 * self[attacker]['level'])
                        self[attacker]['armorhp'] = min(60, self[attacker]['armorhp'])

                #helmet level up
                if self[attacker]['helmet'] >= 1.25 and (0 < self[attacker]['helmhp']):
                    self[attacker]['dmgcut'] += (0.042 * self[attacker]['level'])
                    if (self[attacker]['helmhp'] < helmhp_fix): #32 24 16 8
                        self[attacker]['helmhp'] += (10 * self[attacker]['level'])
                elif self[attacker]['helmet'] >= 1.0 and (0 < self[attacker]['helmhp']): #32 24 16 8
                    self[attacker]['dmgcut'] += (0.036 * self[attacker]['level'])
                    if (self[attacker]['helmhp'] < helmhp_fix):
                        self[attacker]['helmhp'] += (8 * self[attacker]['level'])
                elif self[attacker]['helmet'] >= 0.5 and (0 < self[attacker]['helmhp']): #32 24 16 8
                    self[attacker]['dmgcut'] += (0.030 * self[attacker]['level'])
                    if (self[attacker]['helmhp'] < helmhp_fix):
                        self[attacker]['helmhp'] += (4 * self[attacker]['level'])
                if self[attacker]['level'] == 3:
                    self[attacker]['helmhp'] = min(50, self[attacker]['helmhp'])
                else:
                    self[attacker]['helmhp'] = min(40, self[attacker]['helmhp'])

            elif self[attacker]['level'] == 4:
                self[attacker]['helmet'] += 1
                if self[attacker]['helmhp'] > 0:
                    self[attacker]['helmhp'] = 40
                    if self[attacker]['nvgs'] > 0:
                        self[attacker]['helmhp'] = 50
                self[attacker]['armorhp'] = 75 if self[attacker]['armorhp'] > 0 else 60
                self[attacker]['speed'] += 0.04
                player2.speed = min(self[attacker]['speed'], self[attacker]['maxspeed'])
                if self[attacker]['health'] < 100:
                    self[attacker]['health'] = 100
                else:
                    self[attacker]['health'] = self[attacker]['maxhp']
                    
            #give dmgblock when lvl = 3 ================================
            if self[attacker]['level'] == 3 and self[attacker]['dmgblock'] == 1:
                self[attacker]['dmgblock'] = min(45, self[attacker]['armorhp'])
                
            #BONUS DAMAGE REDUCTION FROM ARMOR LVL 4 ++++++++++++++++++++
            if self[attacker]['level'] >= 4 and self[attacker]['dmgred'] <= 0:
                self[attacker]['dmgred'] = (self[attacker]['level'] - 3)
            
            player2.armor = self[attacker]['armorhp'] + self[attacker]['helmhp']
            player2.delay(0.11, armora.armordelay, (player2, self[attacker]['helmhp'], self[attacker]['armorhp']))
            player2.health = self[attacker]['health']
            player2.delay(0.09, armora.healthdelay, (attacker, self[attacker]['health']))
            
            HudMsg(
                message='{} ARMOR LEVEL UP {}'.format(armorsym[self[attacker]['level']], armorsym2[self[attacker]['level']]),
                hold_time=3.0,
                fade_out=4.0,
                x=0.441 - (self[attacker]['level'] * 0.012),
                y=0.65,
                color1 = armor_colour[self[attacker]['level']],
                channel=9 #armor level up notif
            ).send(index_from_userid(attacker))
            
            HudMsg(
                message=levelsymbol[self[attacker]['level']],
                hold_time=2.6 + (self[attacker]['level'] * 1.5),
                fade_out=2.0 + (self[attacker]['level'] * 2.15),
                x=0.36,
                y=0.939,
                color1 = armor_colour[self[attacker]['level']],
                channel=10 # 10 symbol
            ).send(index_from_userid(attacker))
            
            if player2.health > maxhptemp:
                HudMsg(
                    message='+{}'.format(player2.health - maxhptemp), # healed
                    hold_time=3.0,
                    fade_out=4.0 + (self[attacker]['level'] * 1.4),
                    x=0.112,
                    y=0.939, #0.06 * 720
                    color1 = LIGHT_GREEN,
                    channel=11 # 11 maxhp, 12 helm
                ).send(index_from_userid(attacker))

            if self[attacker]['helmhp'] > harmor2:
                HudMsg(
                    message='+{}'.format(self[attacker]['helmhp'] - harmor2), # repaired helm
                    hold_time=3.0,
                    fade_out=4.0 + self[attacker]['level'],
                    x=0.27,
                    y=0.918, #0.06 * 720
                    color1 = armor_colour[self[attacker]['level']],
                    channel=12  # 11 maxhp, 12 harmor2
                ).send(index_from_userid(attacker))
            
            if self[attacker]['armorhp'] > armor2:
                HudMsg(
                    message='+{}'.format(self[attacker]['armorhp'] - armor2), # repaired armor
                    hold_time=3.0,
                    fade_out=4.0 + self[attacker]['level'],
                    x=0.27,
                    y=0.952, #0.06 * 720
                    color1 = armor_colour[self[attacker]['level']],
                    channel=13  # 11 maxhp, 12 harmor, 13 armor2
                ).send(index_from_userid(attacker))
        elif (self[attacker]['damage'] > self[attacker]['nextlvl']) and (self[attacker]['level'] == 4):
            if self[attacker]['helmet'] >= 1.25 and self[attacker]['helmhp'] > 0 and self[attacker]['dmgcut'] >= 0.5:
                self[attacker]['level'] += 1
                self[attacker]['speed'] += 0.04
                player2.speed = min(self[attacker]['maxspeed'], max(0.76, self[attacker]['speed']))
                self[attacker]['helmet'] = 2
                self[attacker]['dmgcut'] += 0.15
                #self[attacker]['maxlvl'] = max(self[attacker]['maxlvl'], self[attacker]['level'])
                self[attacker]['dmgcut'] = min(0.76, self[attacker]['dmgcut'])
        
        #Delay(timer, armora._reset_tempdmg)
        
    def _player_color_update(self, user, level):
        player = Player(index_from_userid(user))
        randc = min(255, random.randint(213, 230) + (level * 5))
        timelevel = (0.8 + (level * 0.6))
        
        if level == 0:
            player.color = Color(randc, 245, 240) #WHITE
        elif level == 1:
            player.color = Color(105, 100, randc) #BLUE
        elif level == 2:
            player.color = Color(randc, 65, 225) #PURPLE
        elif level == 3:
            #player.color = Color(255, 215, 0, 245) #GOLD
            player.color = Color(randc, 128, 0, 255) #ORANGE
        elif level == 4:
            #player.color = Color(randc, 75, 90) #RED RED
            player.color = Color(255, 215, 0, 250) #GOLD
        else:
            player.color = Color(randc, 54, 45) #REDD
        player.delay(timelevel, armora._player_color_reset, (user, player))
            

    def _player_color_reset(self, user, player):
        player.color = Color(255, 255, 255, 255)
        
        
    def _check_distance(self, player, player2):
        distance = Vector.get_distance(player2.view_vector, player.view_vector)
        distances = '{:.2f}'.format(distance * 100)
        return distances
        #SayText2('\nDistance : \x03{:.2f}\n'.format(distance)).send(player2.index)
        
    
    
    #=========================================================
    def _check_carry(self, user, weapon): # weapon short name
        weight = armora.check_weight(weapon)
        result = 0 if self[user]['carry'] <= weight else 1
        return result
    
    def _start_tempdmg(self, victim, timer):
        global running
        #global tempdmg
        reset_timer = Delay
        #running = True
        try:
            # Let's see if there's a reset delay.
            running = self.reset_timer.running
        except AttributeError:
            running = False
        
        # Well, is there?
        if running:
            # Update the execution with the newer duration.
            reset_timer.exec_time = time() + timer
        else:
            self[victim]['tempdmg'] = 0
            #Delay(0.1, armora._reset_tempdmg)
    
    def _reset_tempdmg(self, victim):
    # Helper to reset tempdmg.
        """global tempdmg
        tempdmg = 0"""
        self[victim]['tempdmg'] = 0
    
    # D A M A G E   D I C T     O 0 O 0 O 0 O 0 O 0 O 0 O 0 O 0 O 0 O 0
    def _damage_round(self, attacker, player, dmg):
    #  0 Both, 1 T, 2 CT
        global T_DMG
        global CT_DMG
        global TCT_DMG
        #user_team =  #Player.from_userid(attacker).team
        user = player.name
        if player.team == 0:
            return
        elif player.team == 1: # TERO TEAM
            T_DMG[user] = self[attacker]['damage']
        elif player.team == 2: # CT TEAM
            CT_DMG[user] = self[attacker]['damage']
        
        if user not in TCT_DMG:
            TCT_DMG[user] = 0
        else:
            TCT_DMG[user] += dmg
        """
        sorted_players = sorted(
            self, key=lambda userid: (self[user]['kills'], self[user]['damage']), reverse=True
        )
        """
    
    # ========== ========== PLAYER FALL ========== ==========
        
    def _player_speed_down(self, user, player):
        if not player.dead and pickup == 0:
            self[user]['speed'] -= 0.18
            player.speed = max(0.67, self[user]['speed'])
            #SayText2('Slowed...({})\n'.format(player.speed)).send(index_from_userid(user))
            player.delay(2.15, armora._player_speed_reset, (user, player, 0.15))
        
    def _player_crippled(self, user, player, damage):
        if not player.dead and pickup == 0:
            self[user]['health'] -= int(damage * 0.56)
            player.health = self[user]['health']
            self[user]['speed'] -= 0.32
            player.speed = max(0.67, self[user]['speed'])
            #SayText2('Crippled...({})\n'.format(player.speed)).send(index_from_userid(user))
            player.delay(4.25, armora._player_speed_reset, (user, player, 0.30))
        
    def _player_speed_reset(self, user, player, speed):
        if not player.dead and pickup == 0:
            self[user]['speed'] += speed
            player.speed = min(self[user]['maxspeed'], max(0.76, self[user]['speed']))
            SayText2('\nYour Speed: \x04{:.3f} \n'.format(player.speed)).send(index_from_userid(user))
            
    
    # ===== ======== ===== ======== ===== ======== ===== ========
    # >> C H E C K   B L E E D I N G  >>
    # ===== ======== ===== ======== ===== ======== ===== ========
    
    def _check_bleed(self, victim, attacker, dmg): #ADDED DMG, 1% PER DMG
        bleedrng = 1 if (random.randint(1, 100) % max(1, int(100 / max(1, dmg)))) == 0 else 0
        player2 = Player(attacker)
        if bleedrng == 1 and self[victim]['bleed'] == 0:
            victim_name = Player(index_from_userid(victim)).name
            delaybleed = random.randint(2, 4)
            self[victim]['bleed'] = 1
            player2.say_team('\x02{}\x01 is bleeding... ({})'.format(victim_name, delaybleed))
            #SayText2('\x02{}\x01 is bleeding... ({})'.format(victim_name, delaybleed)).send(attacker)
        else:
            delaybleed = 0
        return delaybleed
    
    def _start_bleeding(self, delay, victim, player, attacker):
        dur = random.randint(2,4)
        if victim in (-1, 0):
            return
        
        player.delay(delay - 0.2, armora._bleeding, (player, attacker))
        player.delay(delay + 0.8, armora._bleeding, (player, attacker))
        if dur > 2 and not player.dead:
            player.delay(delay + 1.8, armora._bleeding, (player, attacker))
            if dur > 3 and not player.dead:
                player.delay(delay + 2.7, armora._bleeding, (player, attacker))
        player.delay(delay + 3.6, armora._bleeding_stop, (victim, player))

    def _bleeding(self, player, attacker):
        victim = userid_from_index(player.index)
        damager = index_from_userid(attacker)
        dmg = random.choice([1, 1, 1, 2, 2, 3])
        if not player.dead and self[victim]['health'] > 1 and bleeds:
            """self[victim]['health'] -= dmg
            player.health = self[victim]['health']
            """
            player.take_damage(damage=dmg)
            player.delay(0.16, armora.healthdelay, (victim, self[victim]['health']))
            HudMsg(
                message='-{}'.format(dmg), #
                hold_time=0.2,
                fade_out=0.3,
                x=0.112,
                y=0.939, #0.06 * 720
                color1 = NOTRED,
                channel=11 # 11 maxhp, 12 helm
            ).send(index_from_userid(victim))
            armora._bleeding_color(victim, player)
            #SayText2('Bleeding... {} (-{})'.format(self[victim]['health'], dmg)).send(damager)
        elif self[victim]['health'] <= dmg:
            self[victim]['health'] = 0
            player.health = self[victim]['health']
            player.take_damage(damage=10)
            player.delay(0.1, armora.healthdelay, (victim, self[victim]['health']))
            player.slay
            return
            
    def _bleeding_stop(self, victim, player):
        #player = Player(index_from_userid(victim))
        self[victim]['bleed'] = 0
        if self[victim]['health'] < 1:
            self[victim]['health'] -= 1000
            #player.health -= 1000
            player.health = self[victim]['health']
            player.delay(0.15, armora.healthdelay, (victim, self[victim]['health']))
            player.slay
            return
        else:
            player.health = self[victim]['health']
            player.delay(0.16, armora.healthdelay, (victim, self[victim]['health']))
        
        
    def _bleeding_color(self, user, player):
        player.color = Color(215, 105, 95)
        player.delay(0.45, armora._player_color_reset, (user, player))
        
    
    def _check_recover(self, user, mhp):
        player = Player(index_from_userid(user))
        if player.dead:
            return
        
        rtime = mhp - self[user]['health']
        i = 1.0
        while self[user]['health'] < mhp:
            self[user]['health'] = player.delay(i, armora._regen_mhp, (user, 1))
            i += 1.0
        else:
            return
            
    def _regen_mhp(self, user, regen):
        player = Player(index_from_userid(user))
        self[user]['health'] += regen
        HudMsg(
            message='+{}'.format(regen), #
            hold_time=0.2,
            fade_out=0.3,
            x=0.112,
            y=0.939, 
            color1 = GREEN,
            channel=11 # 11 maxhp, 12 helm
        ).send(index_from_userid(user))
        player.health = self[user]['health']
        player.delay(0.15, armora.healthdelay, (user, self[user]['health']))
        return self[user]['health']
    
    # ======== ======== ======== ======== ======== ======== ======== 
    # >>>  C A S H   H E L P E R
    # ======== ======== ======== ======== ======== ======== ========
    
    def cash_bonus(self, victim, attacker, hitbox, bedil):
        player = Player(index_from_userid(victim))
        player2 = Player(index_from_userid(attacker))
        if bedil in spe:
            cashplus = int(cashbonusw['spe'] * cashbonus[hitbox])
            cashminus = int(cashplus * 0.4)
        elif bedil in ar:
            cashplus = int(cashbonusw['ar'] * cashbonus[hitbox])
            cashminus = int(cashplus * 0.32)
        elif bedil in pistol:
            cashplus = int(cashbonusw['pistol'] * cashbonus[hitbox])
            cashminus = int(cashplus * 0.36)
        elif bedil in smg:
            cashplus = int(cashbonusw['smg'] * cashbonus[hitbox])
            cashminus = int(cashplus * 0.45)
        elif bedil in dmr:
            cashplus = int(cashbonusw['dmr'] * cashbonus[hitbox])
            cashminus = int(cashplus * 0.35)
        elif bedil in sniper:
            cashplus = int(cashbonusw['snp'] * cashbonus[hitbox])
            cashminus = int(cashplus * 0.4)
        else:
            cashplus = int(24 * cashbonus[hitbox])
            cashminus = int(cashplus * 0.5)
        if player.cash >= cashminus:
            player.cash = max(0, player.cash - cashminus)
            if 0 <= player2.cash < 12000:
                player2.cash = min(12000, player2.cash + cashplus)
    
    def cash_back(self, shopper, player, cashback):
        player.cash = min(12000, player.cash + cashback)
    
    #CRIT ============================================================
    def dmgcrit_mult(self, weapon, hitbox):
        global dmg_mult
        global crit_rng
        rng80 = random.randint(0, 80) #80 on normal
        if weapon in spe:
            crit_rng = rng80 % critical_mod['spe'] # mod 3.6
            dmg_mult = spe_dmg_mult[hitbox]
            crit_mult = spe_crit_mult[hitbox]
        elif weapon in ar:
            crit_rng = rng80 % critical_mod['ar'] # 10%
            dmg_mult = asr_dmg_mult[hitbox]
            crit_mult = asr_crit_mult[hitbox]
        elif weapon in pistol:
            crit_rng = rng80 % critical_mod['pistol'] # 12%
            dmg_mult = pst_dmg_mult[hitbox]
            crit_mult = pst_crit_mult[hitbox]
        elif weapon in smg:
            crit_rng = rng80 % critical_mod['smg'] # 9%
            dmg_mult = smg_dmg_mult[hitbox]
            crit_mult = smg_crit_mult[hitbox]
        elif weapon in dmr:
            crit_rng = rng80 % critical_mod['snp'] # ~15%
            dmg_mult = dmr_dmg_mult[hitbox]
            crit_mult = dmr_crit_mult[hitbox]
        elif weapon in sniper:
            crit_rng = rng80 % critical_mod['dmr'] # 25%
            dmg_mult = snp_dmg_mult[hitbox]
            crit_mult = snp_crit_mult[hitbox]
        else:
            crit_rng = 1.0
            dmg_mult = pst_dmg_mult[hitbox]
            crit_mult = 1.20
        #SayText2('RNG: {}, CRIT: {}'.format(rng80, weapon)).send()
        value = crit_mult if (0 <= crit_rng <= 0.5) else dmg_mult
        return value
        
    #A D D I T I O N  +  D A M A G E =+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
    def adddmg_mult(self, weapon, hitbox):
        global addmg_mult
        if weapon in spe or weapon == 'xm1014':
            addmg_mult = spe_dmg_bns[hitbox]
        elif weapon in ar:
            addmg_mult = asr_dmg_bns[hitbox]
        elif weapon in pistol:
            addmg_mult = pst_dmg_bns[hitbox]
        elif weapon in smg:
            addmg_mult = smg_dmg_bns[hitbox]
        elif weapon in dmr:
            addmg_mult = dmr_dmg_bns[hitbox]
        elif weapon in sniper:
            addmg_mult = snp_dmg_bns[hitbox]
        else:
            addmg_mult = pst_dmg_bns[hitbox]
        return addmg_mult
        
    def _player_speed_up(self, user, player, speed):
        if player.dead or self[user]['speed'] >= 1.05:
            return
        elif self[user]['speed'] < 1.0:
            dur = random.randint(2, 4)
            self[user]['speed'] += speed
            player.speed = min(self[user]['maxspeed'], self[user]['speed'])
            SayText2('SPEED UP: \x03{:.3f}\x01, DURATION: \x04{}'.format(player.speed, dur)).send(player.index)
            player.delay(dur, armora._player_speed_normal, (user, player, speed))
        
    def _player_speed_normal(self, user, player, speed_down):
        if player.dead:
            return
        elif pickup == 0:
            self[user]['speed'] -= speed_down
            player.speed = min(self[user]['maxspeed'], max(0.76, self[user]['speed']))
        #SayText2('SPEED UP: {:.3f}, DURATION: {}'.format(player.speed, dur)).send(player.index)
        
    def _player_speed_upup(self, player, weapon):
        user = userid_from_index(player.index)
        if not player.dead and armora.check_weight(weapon) > 0.0:
            self[user]['speed'] += armora.check_weight(weapon)
            player.speed = min(self[user]['maxspeed'], max(0.76, self[user]['speed']))
            SayText2('SPEED UPUP: \x04{:.3f}'.format(player.speed)).send(player.index)
        
    def _player_velocity_up(self, player, speed):
        velocity = player.velocity
        dur = random.randint(2, 3)
        velocity.x *= max(1.08, 1 + speed)
        #velocity.y *= max(1.08, 1 + speed)
        player.base_velocity = velocity
        speed_down = 1 / (max(1.05, 1 + speed))
        SayText2('VELOCITY: {}'.format(player.base_velocity)).send(player.index)
        player.delay(dur, armora._player_velocity_normal, (player, speed_down))

        
    def _player_velocity_normal(self, player, speed):
        velocity = player.velocity
        velocity.x *= speed
        velocity.y *= speed
        player.base_velocity = velocity
        
    
    def bomb_dropped(self, game_event):
        user = game_event['userid']
        player = Player(index_from_userid(user))
        
        if not player.dead:
            self[user]['speed'] += 0.020
            player.speed = self[user]['speed']
            
    def _player_stamina(self, user, player):
        SayText2('STAMINA : {:.2f}'.format(player.stamina)).send(index_from_userid(user))
            
            
    def _weapon_now(self, game_event):
        attacker = game_event['userid']
        player = Player(index_from_userid(attacker))
        
        if player.dead:
            return
            
        if not player.primary and self[attacker]['primary'] != '0':
            self[attacker]['speed'] += armora.check_weight(self[attacker]['primary'])
            player.speed = min(self[attacker]['maxspeed'], max(0.76, self[attacker]['speed']))
            self[attacker]['primary'] = '0'
            SayText2('NO PRIMARY, SPEED++ : \x03{:.3f}'.format(player.speed)).send(index_from_userid(attacker))

        if not player.secondary and self[attacker]['secondary'] != '0':
            self[attacker]['speed'] += armora.check_weight(self[attacker]['secondary'])
            player.speed = min(self[attacker]['maxspeed'], max(0.76, self[attacker]['speed']))
            self[attacker]['secondary'] = '0'
            SayText2('NO PISTOL, SPEED+ : \x03{:.3f}'.format(player.speed)).send(index_from_userid(attacker))
        
        """if player.health != self[attacker]['health']:
            player.health = self[attacker]['health']
            armora.healthdelay(attacker, self[attacker]['health'])"""
        
    def player_frozen(self, game_event):
        user = game_event['userid']
        player = Player(index_from_userid(user))
        freeze_dur = max(0.8, ((random.randint(1, 3) * 0.65) + player.flash_duration - self[user]['level']))
        player.delay(0.1, armora.player_flashlight, (user, player, freeze_dur))
        if freeze_dur > 0:
            player.set_frozen(True)
            player.delay(freeze_dur, armora.player_unfrozen, (user, player))
            i = 0
            while i <= (freeze_dur + 0.5):
                player.delay(i + 0.4, armora._player_freeze_recovery, (user, player))
                i += 0.4
        
    def player_unfrozen(self, user, player):
        player.set_frozen(False)
        
    def _player_freeze_recovery(self, user, player):
        if player.dead:
            return
        elif self[user]['health'] < self[user]['maxhp']:
            self[user]['health'] = min(self[user]['maxhp'], self[user]['health'] + 1)
            player.health = self[user]['health']
            #player.delay(0.2, armora.healthdelay, (user, self[user]['health']))
            HudMsg(
                message='+1', #
                hold_time=0.3,
                fade_out=0.5,
                x=0.112,
                y=0.939, #0.06 * 720
                color1 = NOTRED,
                channel=11 # 11 maxhp, 12 helm
            ).send(index_from_userid(user))
            
    def player_flashlight(self, user, player, time):
        i = 0
        while i <= (time + 0.4):
            player.delay(i + 0.1, armora.player_flashlighton, (user, player))
            player.delay(i + random.choice([0.36, 0.48, 0.54]), armora.player_flashlightoff, (user, player))
            i += 0.3
    
    def player_flashlighton(self, user, player):
        player.set_flashlight(True)
    
    def player_flashlightoff(self, user, player):
        player.set_flashlight(False)
    
    
    def _check_nvgs(self, game_event):
        user = game_event['userid']
        player = Player(index_from_userid(user))
        return True if self[user]['nvgs'] == 1 else False
        
    def player_nvgsbroken(self, user, player):
        if not player.dead:
            i = 0
            while i <= 1.5 and not player.dead:
                dur_on = random.choice([0.30, 0.42, 0.56, 0.67])
                dur_off = random.choice([0.12, 0.24, 0.36, 0.48])
                player.delay(i + dur_on, armora.player_nvgson2, (user, player))
                player.delay(i + dur_on + dur_off, armora.player_nvgsoff, (user, player))
                #self[user]['health'] -= 1
                player.health = self[user]['health'] - 1
                player.delay(i + max(dur_on, dur_off), armora.healthdelay, (user, self[user]['health']))
                HudMsg(
                    message='-1', #
                    hold_time=0.2,
                    fade_out=0.3,
                    x=0.112,
                    y=0.939, #0.06 * 720
                    color1 = NOTRED,
                    channel=11 # 11 maxhp, 12 helm
                ).send(index_from_userid(user))
                i += min(dur_on, dur_off)
            self[user]['nvgs'] = 0
            self[user]['maxhp'] = 100

    def player_nvgson(self, game_event):
        user = game_event['userid']
        player = Player(index_from_userid(user))
        player.delay(0.1, armora.player_nvgson2, (user, player))
        player.flash_alpha = 86
        player.delay(0.15 + (player.flash_duration * 0.3), armora.player_nvgsoff, (user, player))
        
    def player_nvgson2(self, user, player):
        if player.nightvision_on == False:
            player.nightvision_on = True
    
    def player_nvgsoff(self, user, player):
        if player.nightvision_on == True:
            player.nightvision_on = False
            
    
    def _carry_recover(self, user, player):
        if not player.dead and self[user]['carry'] <= 0.040:
            self[user]['carry'] = min(0.1, max(0.08, self[user]['carry'] + 0.04))
            player.unrestrict_weapons(*primeweapon)
            player.unrestrict_weapons(*secondweapon)
    

# ====================================== ======================================
# >> SHOW HELPER
# ====================================== ======================================
    
    def damage_now(self, game_event):
        """Show player's damage."""
        global accuracy
        
        attacker = game_event['userid']
        player = Player(index_from_userid(attacker))
        userid = index_from_userid(attacker)
        bedil = str(game_event['weapon'])
        
        self[attacker]['shot'] += 1
        accuracy = (self[attacker]['hit'] / self[attacker]['shot']) * 100
        
        """
        0   damage 0    -->     next 150    = 0/150     = 0
        1   damage 150  -->     next 400    = 150/400   = 0.375 --> 0 - 250
        2   damage 400  -->     next 800    = 400/800   = 0.5   --> 0 - 400
        3   damage 800  -->     next 1350   = 800/1350  = 0.59  --> 0 - 550
        4   damage 1350  -->    next 2050   = 1350/2050 = 0.65  --> 0 - 700
        5   damage 2050  -->    next 2900   = 2050/2900 = 0.7   --> 0 - 850
        """
        
        if bedil in throwable:
            soundlib.playgamesound(attacker, throw)
            if bedil != 'knife':
                player.delay(0.25, armora._player_speed_upup, (player, bedil))
            #self[attacker]['speed'] += 0.005
            #player.speed = self[attacker]['speed']
        elif bedil == 'scout': #and player.primary.getclip > 1:
            player.primary.clip -= min(1, player.primary.clip)
        elif bedil == 'fiveseven': #and player.secondary.getclip > 1:
            player.secondary.clip -= min(1, player.secondary.clip)

        format_acc = "{:.1f}%".format(accuracy)
        dmgperhit = "{:.1f} DMG".format(self[attacker]['damage'] / max(1, self[attacker]['hit']))
        colortime = 2.25 * (1 + (self[attacker]['damage'] / self[attacker]['nextlvl']))
        
        HudMsg(
            message=str(self[attacker]['damage'])+"\n\n"+str(self[attacker]['hit'])+" / "+str(self[attacker]['shot'])+" "+format_acc+"\n"+dmgperhit,
            hold_time=4.0,
            fade_out=5.5,
            fx_time=colortime,
            effect=2,
            x=0.915,
            y=0.455,
            color1 = armor_colour[self[attacker]['level']],
            color2 = armor_colour[self[attacker]['level'] + 1],
            channel=8 #user damage now
        ).send(userid)
           
    
    def armor_now(self, user, player):
        """Show user current armor."""
        if player.dead:
            return

        if self[user]['helmet'] == 0:
            colourh = WHITE
        elif self[user]['helmhp'] <= 10:
            colourh = AZURE
        elif self[user]['helmhp'] <= 20:
            colourh = LIGHT_GREEN
        elif self[user]['helmhp'] <= 30:
            colourh = OLIVE
        elif self[user]['helmhp'] <= 40:
            colourh = GREEN
        else:
            colourh = ANCIENT
            
        if self[user]['dmgcut'] == 0:
            colourh2 = BLUWHITE
        elif self[user]['dmgcut'] <= 0.20:
            colourh2 = AZURE
        elif self[user]['dmgcut'] <= 0.30:
            colourh2 = BLUEVIOLET
        elif self[user]['dmgcut'] <= 0.40:
            colourh2 = GREEN
        elif self[user]['dmgcut'] < 0.50:
            colourh2 = GOLD
        else:
            colourh2 = IMMORTAL
            
        if self[user]['recharge'] < 1:
            addtimer = 3.45
            alphac = 135
            colorarmor = Color(105, 105, 105)
        elif self[user]['recharge'] <= 2:
            addtimer = 2.25
            alphac = 195
            colorarmor = Color(135, 135, 135)
        else:
            addtimer = 1.0
            alphac = 252
            colorarmor = armor_colour[self[user]['level']]
        
        HudMsg(
            message=str(self[user]['armorhp']), # armor now
            hold_time=4.0,
            fade_out=4.0 + addtimer,
            x=0.272,
            y=0.952, #0.06 * 720
            color1 = colorarmor.with_alpha(alphac),
            channel=13  # 11 maxhp, 12 harmor, 13 armor2
        ).send(index_from_userid(user))
        
        if self[user]['helmhp'] > 0:
            HudMsg(
                message=str(self[user]['helmhp']), # helm now
                hold_time=2.5,
                fade_out=3.5,
                x=0.272,
                y=0.918, #0.06 * 720
                color1 = colourh,
                channel=12  # 11 maxhp, 12 harmor2
            ).send(index_from_userid(user))
            Delay(3.6, armora.show_dmgcut, (user, self[user]['dmgcut'], colourh2))
        
    def show_damage_maxhp(self, victim, hitbox, damage):
    #Show maxhp damage
        #victim = game_event['userid']
        #player = Player(index_from_userid(game_event['userid']))
        HudMsg(
            message='-{}'.format(damage), # damaged
            hold_time=2.0,
            fade_out=4.0,
            x=0.112,
            y=0.94, #0.06 * 720
            color1 = hit_color[hitbox],
            channel=11  # 11 maxhp, 12 armor
        ).send(index_from_userid(victim))
    
    
    def show_damage_helmet(self, damage, victim):
    #Show helmet damage inflicted to victim
        HudMsg(
            message='-{}'.format(damage), # damaged helm
            hold_time=1.75,
            fade_out=3.5,
            x=0.27,
            y=0.918, #0.06 * 720
            color1 = armor_colour[self[victim]['level']],
            channel=12 # 11 maxhp, 12 helm, 13 armor
        ).send(index_from_userid(victim))
    
    
    def show_damage_armored(self, damage, victim):
    #Show armor damage inflicted to victim
        HudMsg(
            message='-{}'.format(damage), # damaged armor
            hold_time=1.75,
            fade_out=3.5,
            x=0.27,
            y=0.952, #0.06 * 720
            color1 = armor_colour[self[victim]['level']],
            channel=13 # 11 maxhp, 12 helm, 13 armor
        ).send(index_from_userid(victim))
        
    def show_damage_arms(self, dmg, victim):
    #Show damage to victim's arms
        player = Player(index_from_userid(victim))
        HudMsg(
            message='-{}'.format(dmg), # damaged armor
            hold_time=1.75,
            fade_out=3.0,
            x=0.48,
            y=0.79, #0.06 * 720
            color1 = ANCIENT,
            channel=10 # 11 maxhp, 12 helm, 13 armor
        ).send(index_from_userid(victim))
        player.delay(2.25, armora.show_carry, (victim, player))
        
    def show_carry(self, victim, player):
        HudMsg(
            message='{:.3f}'.format(self[victim]['carry']), # player arms carry
            hold_time=1.75,
            fade_out=3.0,
            x=0.476,
            y=0.79, #0.06 * 720
            color1 = OLIVE,
            channel=10 # 11 maxhp, 12 helm, 13 armor
        ).send(index_from_userid(victim))
    
    def show_damage_boots(self, user, player, fdamage):
        if self[user]['boots'] > 0:
            HudMsg(
                message='-{}'.format(fdamage), # damaged
                hold_time=2.25,
                fade_out=4.0,
                x=0.305,
                y=0.953, #0.06 * 720
                color1 = OLIVE,
                channel=10  # 11 maxhp, 12 armor
            ).send(index_from_userid(user))
        else:
            HudMsg(
                message='-{}'.format(int(fdamage)), # damaged
                hold_time=2.0,
                fade_out=4.0,
                x=0.112,
                y=0.94, #0.06 * 720
                color1 = NOTRED,
                channel=10  # 11 maxhp, 12 armor
            ).send(index_from_userid(user))
            armora.armordelay(player, self[user]['helmhp'], self[user]['armorhp'])

    def show_dmgcut(self, user, dmgcut, colourh2):
    # Helper to show dmgcut.
        #user = game_event['userid']
        HudMsg(
            message="{:.1f}%".format(dmgcut * 100), # dmg cut now
            hold_time=2.5,
            fade_out=3.0,
            x=0.272,
            y=0.918, #0.06 * 720
            color1 = colourh2,
            channel=12  # 11 maxhp, 12 harmor2
        ).send(index_from_userid(user))


    def show_crit(self, attacker):
        HudMsg(
            message=random.choice(critsymbol), # @ % $ % # ^ & !
            hold_time = 4.0,
            fade_out = 5.5,
            fx_time = 2.0,
            effect = 2,
            x=0.359,
            y=0.939,
            color1 = OLDRED,
            color2 = NOTRED,
            channel=10 # 10 symbol
        ).send(index_from_userid(attacker))
        
    def show_streak(self, attacker):
        HudMsg(
            message='x{}'.format(self[attacker]['streak']),
            hold_time=4.5,
            fade_out=5.5,
            fx_time = 2.25,
            effect = 2,
            x=0.489, #0.589
            y=0.376, #0.939
            color1 = random.choice(rainbow),
            color2 = NOTRED,
            channel=14 # 10 symbol
        ).send(index_from_userid(attacker))
        
    def show_round_bonus(self):
        """Show round bonus to players on round start."""
        global round_bonus
        global round_count
        
        HudMsg(
            message='Round: {}\nBonus: {}'.format(round_count, round_bonus[round_count]),
            hold_time=6.5,
            fade_out=6.5,
            x=0.035,     #0.44
            y=0.25,     #0.08
            color1 = round_bonus_color[round_bonus[round_count]],
            channel=3
	    ).send()


    def show_total_dmg(self):
        """Send total damage for this round."""
        global coloure
        coloure = BLUWHITE
        
        if not self:
            return

        if total_dmg <= 250:
            coloure = armor_colour[0]
        elif total_dmg < 750:
            coloure = armor_colour[1]
        elif total_dmg < 1500:
            coloure = armor_colour[2]
        elif total_dmg < 2500:
            coloure = armor_colour[3]
        else: coloure = armor_colour[4]
        
        HudMsg(
	        message=str(total_dmg),
	        hold_time=4.0,
	        fade_out=5.0,
	        x=0.492,
	        y=0.401,
	        color1 = coloure,
	        channel=14 #total damage
        ).send()
        
        
# =================== =================== =================== ===================
# >>       MISC               MISC               MISC               MISC
# =================== =================== =================== ===================

    def add_count(self, game_event):
        """Add round count."""
        global round_count
        global pickup
        global bleeds
        global gacha
        pickup = 1
        round_count += 1
        bleeds = 0
        gacha = 0

    #PICKUP HELPER
    def round_not_started(self):
        global cashback
        global bleeds
        cashback = 4
        bleeds = 0
        Delay(18, armora.round_started)
    
    def round_started(self):
        global pickup
        global bleeds
        pickup = 0
        bleeds = 1
        #SayText2('Pickup DISABLED...\n').send()
        
    # >> COORDINATE for HudMsg
    
    def random_x0(self, xa):
        global x0
        x0 = random.randint(1,5)
        while x0 == xa:
            x0 = random.randint(1,5)
        return x0
        
    def random_y0(self, ya):
        global y0
        y0 = random.choice([0, 1, 2, 3])
        while y0 == ya:
            y0 = random.choice([1, 1, 2, 3])
        return y0
        
    def player_gacha(self, game_event):
        global gacha
        text = game_event['text']
        user = game_event['userid']
        player = Player(index_from_userid(user))
        if text == 'gacha' and gacha < 10:
            if user not in GACHA:
                GACHA[user] = 0
            else:
                GACHA[user] += 1
            if GACHA[user] > 5:
                for i in range(4):
                    time_i = (1.0 * (i + 1)) + (i * 0.2)
                    player.delay(time_i, armora._player_gacha_roll, (user, player, i + 1))
                player.delay(5.2, armora._player_gacha_result, (user, 99))
                return
            elif player.cash >= 200:
                player.cash -= 200
                GACHA[user] += 1
                gacha += 1
                roll = random.randint(0, 6)
                for i in range(3):
                    time_i = (0.9 * (i + 1)) + (i * 0.15)
                    player.delay(time_i, armora._player_gacha_roll, (user, player, i + 1))
                if roll in (0, 1, 3, 4, 6):
                    player.delay(4.0, armora._player_gacha_result, (user, 1))
                elif roll == 2:
                    player.delay(4.8, armora.cash_back, (user, player, 500))
                    player.delay(4.0, armora._player_gacha_result, (user, 50))
                else:
                    player.delay(5.5, armora.cash_back, (user, player, 900))
                    player.delay(4.0, armora._player_gacha_result, (user, 90))
            else:
                SayText2('\n NOT ENOUGH CASH!!! \n').send(index_from_userid(user))
        elif text == 'pevelul' and not player.dead:
            self[user]['damage'] = self[user]['nextlvl'] + 1
            armora.check_level(user, player)
        elif text == 'cmgdut':
            if self[user]['helmet'] <= 0.5 or player.has_helmet == 0:
                SayText2('\n\n CHEAT TEROOO\x03SSSSx01!!!!! \n').send(index_from_userid(user))
                return
            elif self[user]['helmet'] >= 1.0:
                self[user]['dmgcut'] += 0.10
                self[user]['dmgcut'] = min(0.76, self[user]['dmgcut'])
                armora.show_dmgcut(user, self[user]['dmgcut'], BLUBLU)
        elif text == 'lemteh':
            if self[user]['helmet'] < 1.5:
                player.has_helmet == 1
                self[user]['helmet'] += 0.5
                self[user]['helmhp'] == max(40, self[user]['helmhp'])
                player.armor += self[user]['helmhp']
                player.delay(1.0, armora.armordelay, (player, self[user]['helmhp'], self[user]['armorhp']))
            else:
                SayText2('\n\n \x02CHEAT\x01 TER\x03OOO\x01SSSS!!!!! \n').send(index_from_userid(user))
                return


    def _player_gacha_roll(self, user, player, i):
        titik = {1: '. ', 2: '. . ', 3: '. . . ', 4: '. . . . ', 5: '. . . . . ', 6: '. . . . . . '}
        SayText2('{}\n'.format(titik[i])).send(index_from_userid(user))
    def _player_gacha_result(self, user, n):
        hasil = {1: '\x02 ZONK ', 50: '\x03 BONUS +500 ', 90: '\x04 BONUS +900 ', 99: '\n\n \x02GACHA\x01 TEROOOSSSS!!!!!! \n\n'}
        SayText2('{} \n'.format(hasil[n])).send(index_from_userid(user))


armora = _ArmorA()


# =============================================================================
# >> GAME EVENTS
# =============================================================================
@Event('player_spawn')
def _player_spawn(game_event):
    #Assign player armor
    user = game_event['userid']
    player = Player(index_from_userid(user))
    
    armora.round_not_started()
    Delay(1.3, armora.spawn_cash, (user, player))
    Delay(0.25, armora.spawn_armor, (user, player))
    Delay(0.30, armora.player_weapon, (user, player))
    #Delay(3.0, armora._player_stamina, (user, player))
    Delay(1.0, armora.spawn_weapon, (user, player))
    Delay(1.5, armora.spawn_speed, (user, player))


@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def _pre_take_damage(stack_data):
    global prearmor
    global predamage
    
    try:
        victim = make_object(Player, stack_data[0])
    except:
        victim = None
        return

    #victim = Player(victim.index)
    damage_info = make_object(TakeDamageInfo, stack_data[1])
    
    # World damage
    if damage_info.attacker in (-1, 0):
        damage_info.damage = int(damage_info.damage * 1.15)
        return
    
    try:
        attacker = Entity(damage_info.attacker)
    except:
        attacker = None
        return
    
    try:
        atkindex = attacker.index
        attacker = Player(atkindex)
    except ValueError:
        atkindex = None
        attacker = None
        return
    """if Player(attacker.index) == None:
        return"""
        
    # attacker = Player(attacker.index)
    
    if attacker.classname != 'player':
        return

    #if damage_info.type & 2:
    #weapon = Weapon(damage_info.weapon)
    #weapon = attacker.active_weapon
    try:
        weapon = damage_info.weapon
        weaponame = weapon.classname.replace('weapon_', '', 1)
        #SayText2('YOUR WEAPON: {}'.format(weaponame)).send(attacker.index)
    except:
        weapon = None
        weaponame = 'none'

    prearmor = victim.armor
    
    #user = userid_from_index(victim.index)
    #victim.health = self[user]['health']
    
    # Decrease the damage if victim armored
    if victim.armor > 0:
        #predamage = int(damage_info.damage * 0.70) # DEFAULT TEST 0.818 --> 0.7771
        damage_info.damage = int(damage_info.damage * 0.95) #1.0
        #print('==+== =+++= ARMORED =+++= ==+==')
        """
            DEBUG
        print('    ')
        print('Victim Armor: {}, Damage: {}'.format(victim.armor, damage_info.damage))
        print('     NewDamage: {}'.format(predamage))
        # print('Hitbox: {},   NewDamage: {}'.format(hitboxes[victim.hitgroup], predamage))
        print('    ')
        """
    else:
        #predamage = int(damage_info.damage * 0.81)
        rngpredmg = random.choice([0, 1, 1, 1, 2]) if weaponame not in specials else 0
        damage_info.damage = int(damage_info.damage * 1.0) + rngpredmg #0.95
        #print('===== ===== HEALTH ===== =====')
    predamage = int(damage_info.damage * 0.90) #0.82 default
    
    """print('===== ==+== =++== =+++= ==++= ==+== =====')
    print('    ')
    print('VICTIM HP: {}, ARMOR: {}'.format(victim.health, victim.armor))
    print('BASE_DMG: {}, DAMAGE: {}'.format(damage_info.base_damage, damage_info.damage))
    print('PRE_DAMAGE: {}'.format(predamage))
    print('    ')
    
    
    
        DEBUG
    
        print('    ')
        print('Pre-Damage: {},   rng: {}'.format(damage_info.damage, dmgrng))
        print('    ')
    """

#POST HOOK DROP WEAPON
@EntityPostHook(EntityCondition.is_player, "drop_weapon")
def post_drop_weapon(stack_data, return_value):
    try:
        player = make_object(Player, stack_data[0])
    except ValueError:
        return
        
    weapon_info = make_object(Weapon, stack_data[1])    
    weapondrop = weapon_info.classname.replace('weapon_', '', 1)
    weight = armora.check_weight(weapondrop)
    
    if not player.dead:
        SayText2('\x03DROPPED WEAPON: {}, +speed: {}'.format(weapondrop, weight)).send(player.index)
        player.delay(0.12, armora._player_speed_upup, (player, weight))
        player.delay(0.16, armora.player_weapon, (userid_from_index(player.index), player))
    #else:
        #weapon_info.remove()

        #player.delay(0.1, player.speed = max(0.48, player.speed + dropitem)
        #speedf = "{:.3f}".format(player.speed)
        #SayText2('YOUR SPEED: {}'.format(speedf)).send(player.index)

@EntityPostHook(EntityCondition.is_player, 'weapon_switch')
def post_weapon_switch(stack_data, return_value):
    try:
        player = make_object(Player, stack_data[0])
    except ValueError:
        return
    
    weapon2 = make_object(Weapon, stack_data[1])
    weaponsw = weapon2.classname.replace('weapon_', '', 1)
    
    if not player.dead:
        if player.primary and player.primary == weapon2: #player.active_weapon:
            weaponsw = player.primary.classname.replace('weapon_', '', 1)
            if armora._check_carry(userid_from_index(player.index), weaponsw) == 0:
                if player.secondary:
                    player.set_active_weapon(player.secondary)
                else:
                    player.drop_weapon(player.primary)
        elif player.secondary and player.secondary == weapon2: #player.active_weapon:
            weaponsw = player.secondary.classname.replace('weapon_', '', 1)
            if armora._check_carry(userid_from_index(player.index), weaponsw) == 0:
                player.drop_weapon(player.secondary)


@Event('player_hurt')
def _damage(game_event):
    """if game_event['attacker'] in (-1, 0):
        armora.worldamage(game_event)
    else:    
        """
    armora.add_damage(game_event)
    #Delay(0.2, armora.healthafter, (game_event, 0.15))


@PreEvent('player_death')
def _player_dying(game_event):
    armora._check_killer(game_event)

@Event('player_death')
def _player_kills(game_event):
    armora.add_kill(game_event)
    
@Event('weapon_fire')
def _weapon_fired(game_event):
    """Show current damage."""
    #user = game_event['userid']
    #player = Player(index_from_userid(user))
    #armora.player_weapon(user, player)
    
    armora.damage_now(game_event)
    

@Event('player_falldamage')
def _player_falls(game_event):
    #Player Falls.
    """
    user = game_event['userid']
    damage = game_event['damage']
    player = Player(index_from_userid(user))
    armora.player_falling(user, player, damage)
    """
    armora.worldamage(game_event)

@Event('player_disconnect', 'player_connect')
def _player_disconnect(game_event):
    #Remove the player from the dictionary.
    del armora[game_event['userid']]

@Event('round_start')
def _round_start(game_event):
    #Clear the dictionary each new round.
    global total_dmg
    total_dmg = 0
    armora.show_round_bonus()

@Event('item_pickup')
def _item_buy(game_event):
    """Calculate item pickup to dict."""
    armora.shopping(game_event)
    
@Event('player_footstep')
def _player_run(game_event):
    armora._weapon_now(game_event)

@Event('bomb_dropped', 'bomb_planted')
def _bomb_drop(game_event):
    armora.bomb_dropped(game_event)
    
@Event('player_blind')
def _player_freeze(game_event):
    if armora._check_nvgs(game_event) == True:
        armora.player_nvgson(game_event)
    else:
        armora.player_frozen(game_event)

    
@Event('player_say')
def _player_chat(game_event):
    armora.player_gacha(game_event)

@Event('round_end')
def _round_end(game_event):
    """Send messages about total damage each end of round."""
    if round_count > 0:
        armora.show_total_dmg()
    armora.add_count(game_event)


@Event('server_spawn')
def _new_map(game_event):
    global round_count
    global TCT_DMG
    global PDamage
    armora.clear()
    round_count = 0
    clear(TCT_DMG)
    clear(PDamage)
    
    
"""
from players.constants 
HideHudFlags.RADAR / CROSSHAIR / HEALTH / 
LifeState.ALIVE DEAD DYING DISCARDBODY




"""