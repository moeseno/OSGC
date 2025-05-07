import math

class Card():
    """Base object for game cards."""
    def __init__(self):
        self.name="Card"
        self.hp=10
        self.speed=10

    #Checks if target's HP is <= 0, sets HP to 0 if true.
    def death_check(self,target):
        if target.hp<=0:
            target.hp=0
            return True
        return False

    #Calculates damage based on whether the target is the opponent's active card.
    def damage_calc(self,opponent,target_index,damage_number):
        if opponent.active_card_index==target_index:
            return damage_number
        elif opponent.active_card_index==None:
            return 0
        else:
            return math.floor(damage_number/2)

    #Applies damage from ability 1 and returns action details.
    def ability1(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,1)
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    #Applies damage from ability 2 and returns action details.
    def ability2(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,2)
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    #Applies damage from ability 3 and returns action details.
    def ability3(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,3)
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

class Card2():
    """Base object for game cards."""
    def __init__(self):
        self.name="Card2"
        self.hp=30
        self.speed=10

    #Checks if target's HP is <= 0, sets HP to 0 if true.
    def death_check(self,target):
        if target.hp<=0:
            target.hp=0
            return True
        return False

    #Calculates damage based on whether the target is the opponent's active card.
    def damage_calc(self,opponent,target_index,damage_number):
        if opponent.active_card_index==target_index:
            return damage_number
        elif opponent.active_card_index==None:
            return 0
        else:
            return math.floor(damage_number/2)

    #Applies damage from ability 1 and returns action details.
    def ability1(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,3)
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    #Applies damage from ability 2 and returns action details.
    def ability2(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,6)
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    #Applies damage from ability 3 and returns action details.
    def ability3(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,9)
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

class Card3():
    """Base object for game cards."""
    def __init__(self):
        self.name="Card3"
        self.hp=10
        self.speed=10

    #Checks if target's HP is <= 0, sets HP to 0 if true.
    def death_check(self,target):
        if target.hp<=0:
            target.hp=0
            return True
        return False

    #Calculates damage based on whether the target is the opponent's active card.
    def damage_calc(self,opponent,target_index,damage_number):
        if opponent.active_card_index==target_index:
            return damage_number
        elif opponent.active_card_index==None:
            return 0
        else:
            return math.floor(damage_number/2)

    #Applies damage from ability 1 and returns action details.
    def ability1(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,10)
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    #Applies damage from ability 2 and returns action details.
    def ability2(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,20)
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    #Applies damage from ability 3 and returns action details.
    def ability3(self,caster,opponent,target,target_index):
        target.hp-=self.damage_calc(opponent,target_index,50)
        death_status=self.death_check(target)
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }