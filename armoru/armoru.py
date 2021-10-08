# based on most_damage.py by satoon101, url = "http://forums.sourcepython.com/viewtopic.php?f=7&t=64"
# ../armoru/armoru.py

"""Sends messages on round end about the player who caused the most damage."""

# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python
from config.manager import ConfigManager
from colors import Color
from colors import WHITE, PURPLE, YELLOW, RED, GREEN, DARK_RED, LIGHT_GREEN
from engines.sound import Sound
from entities import TakeDamageInfo
from entities.constants import DamageTypes
from entities.entity import Entity
from entities.hooks import EntityCondition, EntityPreHook
from memory import make_object
from events import Event
from events.hooks import PreEvent
from filters.players import PlayerIter
from listeners.tick import Delay, Repeat
from memory import make_object
from messages import HintText
from messages import HudDestination
from messages import HudMsg
from messages import SayText2
from messages import KeyHintText
from messages import TextMsg
from players.entity import Player
from players.helpers import index_from_userid
from pprint import pprint
from settings.player import PlayerSettings
from stringtables import string_tables
from time import time
from weapons.entity import Weapon

import math, random, soundlib

# Additional
from .colors import GOLD, BLUWHITE, AZURE, BLUEVIOLET, LEGENDARY, IMMORTAL, ANCIENT


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================


# BLUWHITE, AZURE, BLUEVIOLET, GOLD, ANCIENT
armor_colour = {'0': BLUWHITE, '1': AZURE, '2': BLUEVIOLET, '3': GOLD, '4': ANCIENT, '5': RED, '6': DARK_RED}
total_colour = {'100': BLUWHITE, '300': AZURE, '800': BLUEVIOLET, '1500': GOLD, '2500': ANCIENT}
round_bonus_color = {0: WHITE, 1: BLUWHITE, 2: AZURE, 3: BLUEVIOLET, 4: IMMORTAL, 5: YELLOW, 6: GOLD, 7: ANCIENT, 8: RED, 9: DARK_RED, 10: DARK_RED}
hit_color = {0: BLUWHITE, 1: DARK_RED, 2: ANCIENT, 3: GOLD, 4: IMMORTAL, 5: IMMORTAL, 6: PURPLE, 7: PURPLE, 8: BLUEVIOLET, 9: BLUWHITE, 10: WHITE}

COLOR_START = (225, 93, 81)
COLOR_END = (210, 48, 39)

round_count = 0
round_bonus = {0: 0, 1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1, 7: 2, 8: 2, 9: 2, 10: 2, 11: 3, 12: 3, 13: 3, 14: 3, 15: 3, 16: 4, 17: 4, 18: 4, 19: 5, 20: 5, 21: 6, 22: 7, 23: 8, 24: 9, 25: 10}

dmg_bonus = [0, 0, 0, 1, 1, 2, 3, 5]
dmgred = {0: 0, 1: 1, 2: 2, 3: 3, 4: 5, 5: 7}
damagered = 0

randomy = [2, 4, 6, 8, 10, 12]

total_dmg = 0
kill = 0
tempkill = 0
tempdmg = 0

boom = 'quake/boomheadshot.mp3'
hedshot = 'quake/ding.mp3'
acrack = 'quake/cracked.mp3'
hcrack = 'quake/break.mp3'
lvlsound = 'quake/levelup.mp3'
throw = 'quake/throw.mp3'

throwable = ['weapon_knife', 'weapon_hegrenade', 'weapon_flashbang', 'weapon_smokegrenade']
hitboxes = {0: 'GENERIC', 1: 'HEAD', 2: 'BODY', 3: 'STOMACH', 4: 'LEFTARM', 5: 'RIGHTARM', 6: 'LEFTLEG', 7: 'RIGHTLEG', 10: 'GEAR'}
hitgrup = [1, 2, 3]
levelsymbol = {0: ' ', 1: ' + ', 2: ' + + ', 3: ' + + + ', 4: ' ~ ~ ~ ~ ~ '}

weaponbonus25 = ['weapon_glock', 'weapon_m3', 'weapon_elite', 'weapon_fiveseven', 'weapon_mac10', 'weapon_tmp', 'weapon_galil']
weaponbonus10 = ['weapon_famas', 'weapon_scout', 'weapon_deagle', 'weapon_aug', 'weapon_hegrenade']

PLAYERS = dict()

Target = {}


# =============================================================================
# >> CLASSES
# =============================================================================
class Vector3:
    def __init__(self, x: int, y: int, z: int):
        self.x, self.y, self.z = x, y, z

    def linear_interpolate(self, target, t: float):
        x = int((target.x - self.x) * t) + self.x
        y = int((target.y - self.y) * t) + self.y
        z = int((target.z - self.z) * t) + self.z
        return Vector3(x, y, z)

    @property
    def get_as_tuple(self) -> tuple:
        return self.x, self.y, self.z


class _ArmorA(dict):
    """Armor Reworks for Counter Strike Source and display damage info."""

    def __init__(self):
        """Create the user settings."""
        # Call super class' init
        super().__init__()
    
    def __missing__(self, userid):
        """Add the userid to the dictionary with the default values."""
        value = self[userid] = {'maxhp': 100, 'initarmor': 25, 'armorhp': 25, 'helmet': 0, 'helmhp': 0, 'level': 0, 'damage': 0, 'nextlvl': 150, 'dmgcut': 0, 'dmgbonus': 0, 'kills': 0, 'streak': 0}
        return value

    def __delitem__(self, userid):
        """Verify the userid is in the dictionary before removing them."""
        if userid in self:
            super().__delitem__(userid)
            
    def shopping(self, game_event):
        player = Player(index_from_userid(game_event['userid']))
        shopper = game_event['userid']
        item = str(game_event['item'])
        
        if (item == "vesthelm"):
            self[shopper]['armorhp'] = 60
            if self[shopper]['helmet'] <= 1 or self[shopper]['dmgcut'] <= 0.10:
                self[shopper]['helmet'] = 1
                self[shopper]['dmgcut'] = 0.10
                for i in range(self[shopper]['level'] + 1):
                    self[shopper]['dmgcut'] += (0.04 * i)
            elif self[shopper]['helmet'] > 1:
                self[shopper]['dmgcut'] = 0.15
                for i in range(self[shopper]['level'] + 1):
                    self[shopper]['dmgcut'] += (0.055 * i)
            if self[shopper]['level'] > 2:
                self[shopper]['helmhp'] = 55
            else:
                self[shopper]['helmhp'] = 40
        elif (item == "vest"):
            self[shopper]['armorhp'] = 60
        elif (item in "nvgs"):
            self[shopper]['helmet'] += 1
            self[shopper]['helmhp'] += 15
            self[shopper]['maxhp'] += 10
            self[shopper]['dmgcut'] += 0.05

        armora.healtharmor(game_event)
    
    def healtharmor(self, game_event):
        """ Assign player health and armor """
        player = Player(index_from_userid(game_event['userid']))
        user = game_event['userid']
        player.health = self[user]['maxhp']
        player.armor = self[user]['helmhp'] + self[user]['armorhp']
        
    def spawn_armor(self, game_event):
        """Add spawn armor."""
        user = game_event['userid']
        player = Player(index_from_userid(game_event['userid']))
        if self[user]['maxhp'] > 100:
            self[user]['maxhp'] = max(110, self[user]['maxhp'])
        elif self[user]['maxhp'] < 100:
            self[user]['maxhp'] = 100
        
        """
        if self[user]['helmet'] == 1:
            self[user]['dmgcut'] = 0.10
            self[user]['helmhp'] = min(40, math.floor(player.armor * (2 / 5)))
            self[user]['armorhp'] = min(60, math.ceil(player.armor * (3 / 5)))
            for i in range(self[user]['level'] + 1):
                self[user]['dmgcut'] += (0.04 * i)
        elif self[user]['helmet'] >= 2:
            self[user]['dmgcut'] = 0.15
            self[user]['helmhp'] = min(40, math.floor(player.armor * (2 / 5)))
            self[user]['armorhp'] = min(60, math.ceil(player.armor * (3 / 5)))
            for i in range(self[user]['level'] + 1):
                self[user]['dmgcut'] += (0.055 * i)
        elif player.armor < self[user]['initarmor']:
            self[user]['armorhp'] = self[user]['initarmor']
            player.armor = self[user]['initarmor']
        else:
            self[user]['armorhp'] = player.armor
        """
        
        if self[user]['armorhp'] < 25:
            self[user]['armorhp'] = self[user]['initarmor']
        
        armora.healtharmor(game_event)
        """
        player.armor = self[user]['helmhp'] + self[user]['armorhp']
        player.health = self[user]['maxhp']
        """
        """        DEBUG
        user = 0
        print('MaxHp: {}, Level: {}'.format(self[user]['maxhp'], self[user]['level']))
        print('Helm: {}, DmgCut: {}'.format(self[user]['helmet'], self[user]['helmhp'], self[user]['dmgcut']))
        print('HelmHP: {}, ArmorHP: {}'.format(self[user]['helmhp'], self[user]['armorhp']))
        """

    
    def add_kill(self, game_event):
        global total_dmg
        
        attacker = game_event['attacker']
        victim = game_event['userid']
        
        #=========================================

        headshot = game_event['headshot']
        revenge = game_event['revenge']     # true (1)
        dominate = game_event['dominated']  # true (1)
        weapon2 = game_event['weapon']
        streakbonus = 0
        
        diff = max(0, self[victim]['level'] - self[attacker]['level'])
        headshotbonus = (15 + (5 * max(0, self[attacker]['level'] - 2)))
        #streakbonus = 25 * max(0, (self[victim]['streak'] - 3))
        for i in range(self[victim]['streak'] + 1):
            if self[victim]['streak'] > 2:
                streakbonus += (i * 10)
            else:
                streakbonus = 0
        
        # Add a kill to the attacker's stats
        self[attacker]['kills'] += 1
        self[attacker]['streak'] += 1
        
        if weapon2 in weaponbonus25:
            self[attacker]['damage'] += 24
            total_dmg += 24
        elif weapon2 in weaponbonus10:
            self[attacker]['damage'] += 10
            total_dmg += 10
            
        if revenge == 1:
            self[attacker]['damage'] += (20 + (diff * 20))
            total_dmg += (10 + (diff * 20))

        if headshot:
            self[attacker]['damage'] += headshotbonus
            total_dmg += headshotbonus
        elif dominate == 1:
            self[attacker]['damage'] += 5
            total_dmg += 5
        else:
            self[attacker]['damage'] += 10
            total_dmg += 10
            
        self[attacker]['damage'] += streakbonus
        total_dmg += streakbonus
        
        self[victim]['armorhp'] = 0
        self[victim]['helmet'] = 0
        self[victim]['helmhp'] = 0
        self[victim]['dmgcut'] = max(0, self[victim]['dmgcut'] / 2)
        self[victim]['streak'] = 0
        
        return
        #=========================================

    def add_damage(self, game_event):
        """Add the damage for the player."""
        global total_dmg
        global kill
        global armour
        global dmg
        global maxhp
        global maxarmor
        
        attacker = game_event['attacker']
        victim = game_event['userid']
        
        key = str(game_event['userid'])
        player = Player(index_from_userid(game_event['userid']))
        damager = index_from_userid(game_event['attacker'])
        player2 = Player(index_from_userid(game_event['attacker']))
        
        damage = game_event['dmg_health']
        armour = game_event['dmg_armor']
        bedil = str(game_event['weapon'])
        hitbox = game_event['hitgroup']
        varmor = game_event['armor']
        
        rndm = random.randrange(0,6)
        rndma = random.randrange(1,5)
        rndmy = random.choice(randomy)
        
        global tempdmg
        global round_count
        
        # total_dmg = 0
        addamage = 0
        dmg = 0
        
        if key not in PLAYERS:
            PLAYERS[key] = 0
        x = 0.615 - (rndm * 0.018)
        xa = 0.66 - (rndma * 0.021)
        y = 0.502 - ((damage + rndmy) // 8) * 0.018
        ya = 0.512 - ((armour + rndm) // 7) * 0.0215
        PLAYERS[key] += 1
        
        #health damage color
        t = (damage + 1) / max(1, player.health)
        if not(0 <= t <= 1):
            t = 0 if t < 0 else 1
        
        if hitbox == 1:
            t = 1
        color = Vector3(*COLOR_START).linear_interpolate(Vector3(*COLOR_END), t)
    
        # Is this self inflicted?
        if attacker in (victim, 0):
            return

        # Was this a team inflicted?
        attacker_team = Player.from_userid(attacker).team
        victim_team = Player.from_userid(victim).team
        if attacker_team == victim_team:
            return
            
        # if Player.from_userid(attacker).alive == false:
        #   return
        
        # Add dmg bonus to attacker
        self[attacker]['dmgbonus'] = random.choice(dmg_bonus) + round_bonus[round_count]
        dmgbonus = self[attacker]['dmgbonus']
        dmgcut = self[victim]['dmgcut']
        maxhp = self[victim]['maxhp']
        maxarmor = self[victim]['armorhp'] + self[victim]['helmhp']
        
        maxhptemp = self[attacker]['maxhp']
        maxarmortemp = self[attacker]['armorhp'] + self[attacker]['helmhp']
        
        armor_repair = (100 - (15 * self[attacker]['level']))
        armorhp_fix = (60 - (10 * self[attacker]['level'])) # max 60
        helmhp_fix = (40 - (8 * self[attacker]['level'])) # max 40
        
        damagered = dmgred[self[victim]['level']]
        if (self[victim]['armorhp'] <= 0) or (prearmor <= 0):
            damagered = 0
        
        # This is player_hurt, so add the damage
        if (damage > 150) and (newdamage > (1.75 * prearmor)):
            armour = damage
            player.armor = 0
            self[victim]['armorhp'] = 0
            player.health = self[victim]['maxhp']
            soundlib.playgamesound(attacker, acrack)
            if (damage >= 250) and (newdamage > (2.75 * prearmor)):
                self[victim]['helmet'] = 0
                self[victim]['helmhp'] = 0
                soundlib.playgamesound(attacker, hedshot)
                soundlib.playgamesound(attacker, hcrack)
                player.health = 0
                return

        
        if (prearmor > 0):
            if (hitbox == 1):
                soundlib.playgamesound(attacker, hedshot)
                if (self[victim]['helmet'] >= 1):
                    self[victim]['helmhp'] -= armour
                    helmhp = prearmor - self[victim]['armorhp']
                    addamage = math.floor(armour * 0.36 * (1 - dmgcut)) + dmgbonus # 4 (100) * 0.3 * 0.9 = 27
                    self[victim]['helmhp'] -= min(self[victim]['helmhp'], addamage)
                    if armour > (helmhp * 3.0):
                        self[victim]['maxhp'] -= max(math.floor(newdamage * 0.5) - helmhp, 0)
                        armora.show_damage_armored((maxhp - self[victim]['maxhp']), victim)
                    if self[victim]['helmhp'] <= 0:
                        self[victim]['helmet'] = 0
                        self[victim]['dmgcut'] -= ((self[victim]['level'] + 1) * 0.05)
                        if helmhp and (self[victim]['helmhp'] <= 0):
                            soundlib.playgamesound(attacker, hcrack)
                            helmhp = 0
                    armora.show_damage_helmet((armour + addamage), victim)
                else:
                    armour = math.floor(newdamage * 0.6) + dmgbonus # 4 * 0.5
                    dmg = min(math.ceil(armour / 20), 4) # 42/20 = 1.6 -> (2 + 42 + bonus)
                    self[victim]['maxhp'] -= min(armour + dmg - damagered, self[victim]['maxhp'])
            elif (hitbox == 2):
                if self[victim]['armorhp'] > 0:
                    armorhp = prearmor - self[victim]['helmhp']
                    self[victim]['armorhp'] -= armour
                    addamage =  max(0, (math.ceil(armour * 0.7) + dmgbonus - damagered)) # 1 * 0.6
                    self[victim]['armorhp'] -= min(self[victim]['armorhp'], addamage)
                    if armour > (self[victim]['armorhp'] * 2.0):
                        self[victim]['maxhp'] -= max(math.floor(armour - ((self[victim]['armorhp'] * 3.0))), 0)
                    if (self[victim]['armorhp'] == 0) and (0 < armorhp):
                        soundlib.playgamesound(attacker, acrack)
                        armorhp = 0
                    armora.show_damage_armored((armour + addamage), victim)
                else:
                    armour = math.floor(newdamage * 0.875) + dmgbonus # 1.0 * 0.9
                    dmg = min(math.ceil(armour / 10), 1) # 7.5 + bonus / 2.5 = (3 + 7.5)
                    # player.armor = self[victim]['helmhp']
                    self[victim]['maxhp'] -= min(self[victim]['maxhp'], max(armour + dmg - damagered, 1))
            elif (hitbox == 3):
                if (self[victim]['armorhp'] > 0) and (self[victim]['level'] > 0):
                    armorhp = prearmor - self[victim]['helmhp']
                    self[victim]['armorhp'] -= armour
                    addamage = max(0, (math.ceil(armour * 0.6) + dmgbonus - (damagered - 1))) # 1.25 * 0.6
                    self[victim]['armorhp'] -= min(self[victim]['armorhp'], addamage)
                    if armour > (armorhp * 1.6):
                        self[victim]['maxhp'] -= max(armour - armorhp, 0)
                    if (0 == self[victim]['armorhp']) and (0 < armorhp):
                        soundlib.playgamesound(attacker, acrack)
                        armorhp = 0
                    armora.show_damage_armored((armour + addamage), victim)
                else:
                    armour = math.floor(newdamage * 0.8) + dmgbonus   # 1.25 * 0.8
                    dmg = min(math.ceil(armour / 12), 2) # 9 / 2.5 = (3 + 9)
                    # player.armor = self[victim]['helmhp']
                    self[victim]['maxhp'] -= min(self[victim]['maxhp'], max(armour + dmg - damagered, 2))
            elif (hitbox == 6) or (hitbox == 7):
                armour = max(0, math.floor(newdamage * 0.9) + dmgbonus - 1)  # 0.75 * 0.9
                dmg = min(math.ceil(armour / 7), 1) # 3 + bonus / 2.5 = (1 + 3 + bonus)
                self[victim]['maxhp'] -= min(self[victim]['maxhp'], max(armour + dmg, 1))
            else:
                armour = math.floor(newdamage * 0.9) + dmgbonus # 1 * 0.9
                dmg = min(math.ceil(armour / 8), 1) # 5 / 3.0 = 1.6 ~ 2 ==> (1 + 5 + bonus)
                self[victim]['maxhp'] -= min(self[victim]['maxhp'], max(armour + dmg - damagered, 1))


            # assign player health to own maxhp
            player.health = self[victim]['maxhp']
            player.armor = self[victim]['armorhp'] + self[victim]['helmhp']
            
            
            # add damage to user damage
            self[attacker]['damage'] += (armour + dmg + addamage)
            tempdmg += (armour + dmg + addamage)
            total_dmg += (armour + dmg + addamage + 1)
            
            if player.health < maxhp:
                armora.show_damage_maxhp(victim, hitbox, armour=(maxhp - player.health))
            
            HudMsg(
                message=str(tempdmg), # (armour + dmg + addamage)
                hold_time=1.5,
                fade_out=1.0,
                x=xa,
                y=ya,
                color1 = armor_colour[str(self[victim]['level'])],
                channel=PLAYERS[key]
	        ).send(damager)

            """     DEBUG
            print('  ')
            print('  DAMAGE to ARMOR     HITBOX: {}'.format(hitboxes[hitbox]))
            print('DMG ARMOR: {}, DMG HEALTH: {}, '.format(game_event['dmg_armor'], game_event['dmg_health']))
            print('ARMOR LEFT: {}, HEALTH LEFT: {}, '.format(game_event['armor'], game_event['health']))
            print('ARMOUR: {}, ADDMG: {}, DMG: {}, BONUS: {}'.format(armour, addamage, dmg, dmgbonus))
            print('Player.Armor: {}, MAXHP: {}, Player.Health: {}'.format(player.armor, self[victim]['maxhp'], player.health))
            print('UserArmor HP: {}, UserHelm HP: {}'.format(self[victim]['armorhp'], self[victim]['helmhp']))
            print('  ')
            """
            
        else:
            if (hitbox == 1):
                soundlib.playgamesound(attacker, hedshot)
                damage = math.floor(damage * 0.8) #4.0 * 0.8 = 3.2
            elif (hitbox == 2):
                damage = math.floor(damage * 0.95) # 1.0 * 0.95
            elif (hitbox == 3):
                damage = math.floor(damage * 1.20) # 1.25 * 0.95
            elif (hitbox == 6) or (hitbox == 7):
                damage = math.floor(damage * 1.12) # 0.75 * 1.12
            else:
                damage = math.floor(damage * 1.1) # 1.1

            # player.health = max(1, player.health)
            self[attacker]['damage'] += damage
            self[victim]['maxhp'] -= min(self[victim]['maxhp'], damage)
            player.health = self[victim]['maxhp']
            total_dmg += damage + 1
            tempdmg += damage
            
            if player.health < maxhp:
                armora.show_damage_maxhp(victim, hitbox, armour=(maxhp - player.health))
            
            #"""
            HudMsg(
                message=str(tempdmg), #damage
                hold_time=1.3,
                fade_out=1.2,
                x=x,
                y=y,
                color1 = Color(*color.get_as_tuple),
                #color2 = RED,
                channel=PLAYERS[key]
	        ).send(damager)
            #"""
            
            """     DEBUG
            print('    ')
            print('  DAMAGE HEALTH     HITBOX: {}'.format(hitboxes[hitbox]))
            print('DMG HEALTH: {}  HEALTH LEFT: {}'.format(game_event['dmg_health'], game_event['health']))
            print('MAXHP: {}, Health: {}'.format(self[victim]['maxhp'], player.health))
            print('    ')
            """
            
        harmor2 = self[attacker]['helmhp']
        armor2 = self[attacker]['armorhp']
        #check new ARMOR LVL and Calculate DMG CUT and DMG REDUCTION
        if (self[attacker]['damage'] > self[attacker]['nextlvl']) and (self[attacker]['level'] <= 3):
            self[attacker]['level'] += 1
            self[attacker]['nextlvl'] += (100 + (self[attacker]['level'] * 150)) # 100 + level*150
            soundlib.playgamesound(attacker, lvlsound)
            
            # check repair armor on level up
            if (0 < player2.armor < armor_repair) and self[attacker]['level'] < 4:
                # recover maxhp by medium ammount
                if self[attacker]['level'] == 3:
                    if self[attacker]['maxhp'] <= 50:
                        self[attacker]['maxhp'] = 25 + (self[attacker]['level'] * 25)
                    else:
                        self[attacker]['maxhp'] = 125
                elif self[attacker]['maxhp'] <= 50:
                    self[attacker]['maxhp'] = 30 + (self[attacker]['level'] * 30)
                else:
                    self[attacker]['maxhp'] = 50 + (self[attacker]['level'] * 25)
                    
                # repair armorhp by medium ammount
                if (0 < self[attacker]['armorhp'] < armorhp_fix): #48 36 24 12
                    self[attacker]['armorhp'] += (12 * self[attacker]['level'])
                    self[attacker]['armorhp'] = max(60, self[attacker]['armorhp'])
                
                if self[attacker]['helmet'] >= 2 and (0 < self[attacker]['helmhp'] < helmhp_fix): #32 24 16 8
                    self[attacker]['dmgcut'] += (0.055 * self[attacker]['level'])
                    self[attacker]['helmhp'] += (10 * self[attacker]['level'])
                    self[attacker]['helmhp'] = max(40, self[attacker]['helmhp'])
                elif self[attacker]['helmet'] == 1 and (0 < self[attacker]['helmhp'] < helmhp_fix): #32 24 16 8
                    self[attacker]['dmgcut'] += (0.04 * self[attacker]['level'])
                    self[attacker]['helmhp'] += (8 * self[attacker]['level'])
                    self[attacker]['helmhp'] = max(40, self[attacker]['helmhp'])
            elif self[attacker]['level'] == 4:
                self[attacker]['helmet'] += 1
                self[attacker]['helmhp'] = 40
                self[attacker]['armorhp'] = 60
                if self[attacker]['maxhp'] < 100:
                    self[attacker]['maxhp'] = 100
                else:
                    self[attacker]['maxhp'] = 125
            
            """
            elif (player2.armor >= armor_repair):
                # repair armorhp by small ammount
                if (0 < self[attacker]['armorhp']):
                    self[attacker]['armorhp'] += (8 * self[attacker]['level'])
                    player2.armor += (8 * self[attacker]['level'])
                    #player2.health += (12 * self[attacker]['level'])
                
                if self[attacker]['helmet'] >= 2 and (0 < self[attacker]['helmhp']): #32 24 16 8
                    self[attacker]['dmgcut'] += (0.045 * self[attacker]['level'])
                    self[attacker]['helmhp'] += (8 * self[attacker]['level'])
                    player2.armor += (8 * self[attacker]['level'])
                elif self[attacker]['helmet'] == 1 and (0 < self[attacker]['helmhp']): #32 24 16 8
                    self[attacker]['dmgcut'] += (0.035 * self[attacker]['level'])
                    self[attacker]['helmhp'] += (5 * self[attacker]['level'])
                    player2.armor += (6 * self[attacker]['level'])
            """
            
            player2.armor = self[attacker]['armorhp'] + self[attacker]['helmhp']
            player2.health = self[attacker]['maxhp']
            
            HudMsg(
                message='ARMOR LEVEL UP',
                hold_time=4.0,
                fade_out=4.0,
                x=0.441,
                y=0.65,
                color1 = armor_colour[str(self[attacker]['level'])],
                channel=9 #armor level up notif
            ).send(damager)
            
            HudMsg(
                message=levelsymbol[self[attacker]['level']],
                hold_time=2.0 + (self[attacker]['level'] * 3.0),
                fade_out=3.0 + (self[attacker]['level'] * 3),
                x=0.36,
                y=0.939,
                color1 = armor_colour[str(self[attacker]['level'])],
                channel=10 # 10 symbol
            ).send(damager)
            
            HudMsg(
                message='+{}'.format(player2.health - maxhptemp), # healed
                hold_time=3.0,
                fade_out=4.0,
                x=0.112,
                y=0.939, #0.06 * 720
                color1 = LIGHT_GREEN,
                channel=11 # 11 maxhp, 12 helm
            ).send(damager)
            
            HudMsg(
                message='+{}'.format(abs(self[attacker]['helmhp'] - harmor2)), # repaired helm
                hold_time=3.0,
                fade_out=4.0 + self[attacker]['level'],
                x=0.27,
                y=0.918, #0.06 * 720
                color1 = armor_colour[str(self[attacker]['level'])],
                channel=12  # 11 maxhp, 12 harmor2
            ).send(damager)
            
            HudMsg(
                message='+{}'.format(abs(self[attacker]['armorhp'] - armor2)), # repaired armor
                hold_time=3.0,
                fade_out=4.0 + self[attacker]['level'],
                x=0.27,
                y=0.952, #0.06 * 720
                color1 = armor_colour[str(self[attacker]['level'])],
                channel=13  # 11 maxhp, 12 harmor, 13 armor2
            ).send(damager)
            
        if self[victim]['maxhp'] <= 0:
            self[victim]['armorhp'] = 0
            self[victim]['helmet'] = 0
            self[victim]['helmhp'] = 0
            self[victim]['dmgcut'] = max(0, self[victim]['dmgcut'] / 2)
          
        Delay(2.5, armora._reset_tempdmg)
            
    def _reset_tempdmg(self):
    # Helper to reset tempdmg.
        global tempdmg
        tempdmg = 0
    
    def show_damage_maxhp(self, victim, hitbox, armour):
    #
        #victim = game_event['userid']
        #player = Player(index_from_userid(game_event['userid']))
    
        HudMsg(
            message='-{}'.format(armour), # damaged
            hold_time=2.0,
            fade_out=1.5,
            x=0.112,
            y=0.94, #0.06 * 720
            color1 = hit_color[hitbox],
            channel=11  # 11 maxhp, 12 armor
        ).send(index_from_userid(victim))

    
    def show_damage_helmet(self, armour, victim):
    #Show helmet damage inflicted to victim
        HudMsg(
            message='-{}'.format(armour), # damaged helm
            hold_time=2.0,
            fade_out=1.5,
            x=0.27,
            y=0.918, #0.06 * 720
            color1 = armor_colour[str(self[victim]['level'])],
            channel=12 # 11 maxhp, 12 helm, 13 armor
        ).send(index_from_userid(victim))
    
    
    def show_damage_armored(self, armour, victim):
    #Show armor damage inflicted to victim
        HudMsg(
            message='-{}'.format(armour), # damaged armor
            hold_time=2.0,
            fade_out=1.5,
            x=0.27,
            y=0.952, #0.06 * 720
            color1 = armor_colour[str(self[victim]['level'])],
            channel=13 # 11 maxhp, 12 helm, 13 armor
        ).send(index_from_userid(victim))
        
        
    def add_count(self, game_event):
        """Add round count."""
        global round_count
        
        round_count += 1
        
    def damage_now(self, game_event):
        """Add round count."""
        
        attacker = game_event['userid']
        userid = index_from_userid(game_event['userid'])
        bedil = str(game_event['weapon'])
        
        if bedil in throwable:
            soundlib.playgamesound(attacker, throw)
        
        HudMsg(
            message=str(self[attacker]['damage']),
            hold_time=4.0,
            fade_out=5.0,
            x=0.93,
            y=0.46,
            color1 = armor_colour[str(self[attacker]['level'])],
            channel=15 #user damage now
        ).send(userid)
        
    
    def armor_now(self, game_event):
        """Show user current armor."""
        
        user = game_event['userid']
        
        if self[user]['helmet'] == 0:
            colourh = WHITE
        elif self[user]['helmhp'] <= 10:
            colourh = AZURE
        elif self[user]['helmhp'] <= 20:
            colourh = LIGHT_GREEN
        elif self[user]['helmhp'] <= 30:
            colourh = GREEN
        else:
            colourh = ANCIENT
            
        if self[user]['dmgcut'] == 0:
            colourh2 = BLUWHITE
        elif self[user]['dmgcut'] <= 0.10:
            colourh2 = AZURE
        elif self[user]['dmgcut'] <= 0.15:
            colourh2 = BLUEVIOLET
        elif self[user]['dmgcut'] <= 0.35:
            colourh2 = GREEN
        elif self[user]['dmgcut'] <= 0.5:
            colourh2 = GOLD
        else:
            colourh2 = IMMORTAL

        HudMsg(
            message=str(self[user]['helmhp']), # helm now
            hold_time=4.0,
            fade_out=5.0,
            x=0.272,
            y=0.918, #0.06 * 720
            color1 = colourh,
            color2 = colourh2,
            channel=12  # 11 maxhp, 12 harmor2
        ).send(index_from_userid(user))
            
        HudMsg(
            message=str(self[user]['armorhp']), # armor now
            hold_time=4.0,
            fade_out=5.0,
            x=0.272,
            y=0.952, #0.06 * 720
            color1 = armor_colour[str(self[user]['level'])],
            channel=13  # 11 maxhp, 12 harmor, 13 armor2
        ).send(index_from_userid(user))


    def send_total_dmg(self):
        """Send total damage for this round."""
        global coloure
        global tempkill
        coloure = BLUWHITE
        
        # userid = game_event['userid']
        # playerid = index_from_userid(game_event['userid'])
        
        if not self:
            return

        if total_dmg <= 250:
            coloure = armor_colour['0']
        elif total_dmg < 750:
            coloure = armor_colour['1']
        elif total_dmg < 1250:
            coloure = armor_colour['2']
        elif total_dmg < 2250:
            coloure = armor_colour['3']
        else: coloure = armor_colour['4']
        
        HudMsg(
	        message=str(total_dmg),
	        hold_time=4.5,
	        fade_out=2.5,
	        x=0.49,
	        y=0.40,
	        color1 = coloure,
	        channel=14 #total damage
        ).send()
        

    def show_round_bonus(self):
        """Show round bonus to players on round start."""
        global round_bonus
        global round_count
        global round_bonus_color
        
        real_count = ((round_count - 1) // 3) + 1
        round_round = (round_count % 3)
        if round_round == 0:
            round_round = 3
        
        HudMsg(
            message='Round {}-{} ({})'.format(real_count, round_round, round_count),
            hold_time=6.5,
            fade_out=6.5,
            x=0.035,     #0.44
            y=0.25,     #0.08
            color1 = round_bonus_color[round_bonus[round_count]],
            channel=3
	    ).send()
        
        HudMsg(
            message='Bonus: {}'.format(round_bonus[round_count]),
            hold_time=6.5,
            fade_out=6.5,
            x=0.035,     #0.44
            y=0.285,     #0.08
            color1 = round_bonus_color[round_bonus[round_count]],
            channel=4
	    ).send()

    
armora = _ArmorA()


# =============================================================================
# >> GAME EVENTS
# =============================================================================
@Event('player_spawn')
def _player_action(game_event):
    armora.spawn_armor(game_event)
    #armora.armor_now(game_event)


@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def _pre_take_damage(stack_data):
    global prearmor
    global newdamage
    victim = make_object(Player, stack_data[0])
    damage_info = make_object(TakeDamageInfo, stack_data[1])
    attacker = Entity(damage_info.attacker)
    if attacker.classname != 'player':
        return

    attacker = Player(attacker.index)
    #weapon = Weapon(damage_info.weapon)
    prearmor = victim.armor 

    # Decrease the damage if victim armored
    if victim.armor > 0:
        """
        if victim.hitgroup == 1:
            newdamage = math.floor(damage_info.damage * 0.7)
            #victim.armor -= math.floor(newdamage / 1.5)
            damage_info.damage = 0
        elif victim.hitgroup == 2:
            newdamage = math.floor(damage_info.damage * 1.0)
            #victim.armor -= math.floor(newdamage / 2.0)
            damage_info.damage = 0
        elif victim.hitgroup == 3:
            newdamage = math.floor(damage_info.damage * 1.05)
            #victim.armor -= math.floor(newdamage / 1.6)
            damage_info.damage = 0
        else:
        """
        newdamage = math.floor(damage_info.damage * 0.95)
        damage_info.damage = math.floor(damage_info.damage * 1.0)
        
        """     DEBUG
        print('    ')
        print('Victim Armor: {}, Damage: {}'.format(victim.armor, damage_info.damage))
        print('     NewDamage: {}'.format(newdamage))
        # print('Hitbox: {},   NewDamage: {}'.format(hitboxes[victim.hitgroup], newdamage))
        print('    ')
        """
    else:
        dmgrng = random.choice(dmg_bonus)
        damage_info.damage = math.floor((damage_info.damage * 0.95) + dmgrng)
        """     DEBUG
        print('    ')
        print('Pre-Damage: {},   rng: {}'.format(damage_info.damage, dmgrng))
        print('    ')
        """


@PreEvent('player_hurt')
def _pre_damage(game_event):
    armora.add_damage(game_event)

    
@Event('player_death')
def _player_kills(game_event):
    armora.add_kill(game_event)

    
@Event('weapon_fire')
def _weapon_fired(game_event):
    """Show current damage."""
    armora.damage_now(game_event)


@Event('player_disconnect')
def _player_disconnect(game_event):
    """Remove the player from the dictionary."""
    del armora[game_event['userid']]
    

@Event('round_start')
def _round_start(game_event):
    """Clear the dictionary each new round."""
    global total_dmg
    global round_count
    total_dmg = 0
    if (round_count % 3 == 1) and (round_count > 3):
        armora.clear()
    armora.show_round_bonus()


@Event('player_spawn')
def _player_spawn(game_event):
    #Assign player armor
    armora.spawn_armor(game_event)
    armora.armor_now(game_event)
    
    
@Event('item_pickup')
def _item_buy(game_event):
    """Calculate armor to dict."""
    armora.shopping(game_event)


@Event('round_end')
def _round_end(game_event):
    """Send messages about total damage each end of round."""
    armora.add_count(game_event)
    if round_count > 0:
        armora.send_total_dmg()
    # armora.send_message()


@Event('server_spawn')
def _new_map(game_event):
    global round_count
    armora.clear()
    round_count = 0