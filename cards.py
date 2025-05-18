import math

class Card():
    """Base object for game cards."""
    def __init__(self):
        self.name="Card"
        self.hp=10
        self.speed=10
        self.ability_damages={1:1,2:2,3:3}

    def death_check(self,target):
        if target.hp<=0:
            target.hp=0
            return True
        return False

    def damage_calc(self,opponent,target_index,damage_number):
        if opponent.active_card_index==target_index:
            return damage_number
        elif opponent.active_card_index==None:
            return 0
        else:
            return math.floor(damage_number/2)

    def _create_action_payload(self,caster,opponent,target,death_status):
        return {
            "type":"action",
            "attacking_player_uid":caster.uid,
            "targeted_player_uid":opponent.uid,
            "attacking_card_index":caster.cards_list.index(self),
            "targeted_card_index":opponent.cards_list.index(target),
            "target_hp":target.hp,
            "death":death_status
        }

    def _perform_ability(self,ability_number,caster,opponent,target,target_index):
        base_damage=self.ability_damages.get(ability_number,0)
        actual_damage=self.damage_calc(opponent,target_index,base_damage)
        target.hp-=actual_damage
        death_status=self.death_check(target)
        return self._create_action_payload(caster,opponent,target,death_status)

    def ability1(self,caster,opponent,target,target_index):
        return self._perform_ability(1,caster,opponent,target,target_index)

    def ability2(self,caster,opponent,target,target_index):
        return self._perform_ability(2,caster,opponent,target,target_index)

    def ability3(self,caster,opponent,target,target_index):
        return self._perform_ability(3,caster,opponent,target,target_index)



class Card2(Card):
    def __init__(self):
        self.name="Card2"
        self.hp=30
        self.speed=10
        self.ability_damages={1:3,2:6,3:9}



class Card3(Card):
    def __init__(self):
        self.name="Card3"
        self.hp=10
        self.speed=10
        self.ability_damages={1:10,2:20,3:50}