import random

class Unit:
    def __init__(self, name, hp, attack, defense, crit_chance=0.15, crit_multiplier=2.0):
        self._name = name
        self._hp = hp
        self._max_hp = hp
        self._attack = attack
        self._defense = defense
        self._crit_chance = crit_chance    # шанс крита 0.15 = 15%
        self._crit_multiplier = crit_multiplier

    #Здоровье
    def get_hp(self):
        return self._hp
    def get_max_hp(self):
        return self._max_hp

    #Защита
    def get_defense(self):
        return self._defense


    #Фактический урон
    def take_damage(self, dmg):

        actual = max(0, dmg - self.get_defense())
        self._hp = max(0, self._hp - actual)
        return actual

    #Жив ли?
    def is_alive(self):
        return self._hp > 0

    #Имя
    def get_name(self):
        return self._name

    #Урон
    def get_attack(self):
        return self._attack

    def attack(self, target):
        dmg = self.get_attack()

        if random.random() < self._crit_chance:
            dmg = int(dmg * self._crit_multiplier)
            actual = target.take_damage(dmg)
            return actual, True  # (урон, крит?)
        else:
            actual = target.take_damage(dmg)
            return actual, False

    def __str__(self):
        return f"{self._name} [HP {self._hp}/{self._max_hp}]"

class Hero(Unit):
    def __init__(self, name, hp, attack, defense, crit_chance=0.15, crit_multiplier=2.0):
        super().__init__(name, hp, attack, defense, crit_chance, crit_multiplier)
        self._level = 1
        self._experience = 0
        self._inventory = Inventory()

    def gain_xp(self, amount):
        self._experience += amount
        if self._experience >= 100:
            self._level_up()

    def use_potion(self):
        potion = self._inventory.get("potion")
        if potion:
            self._hp = min(self._max_hp, self._hp + potion.get_bonus())
            self._inventory.remove("potion")
            return True
        return False

    def _level_up(self):
        self._level += 1
        self._experience = 0
        self._attack += 3
        self._defense += 2
        self._max_hp += 21
        self._hp = self._max_hp

    def get_inventory(self):
        return self._inventory

    def get_attack(self):
        return self._attack + self._inventory.total_attack_bonus()

    def get_defense(self):
        return self._defense + self._inventory.total_defense_bonus()

#class Location:
 #   def __init__(self, description, left=None, right=None, is_end=False):
  #     self._left = left
   #     self._right = right
    #    self._is_end = is_end

 #   def get_description(self): return self._description
  #  def get_left(self): return self._left
   # def get_right(self): return self._right
    #def is_end(self): return self._is_end

class Monster(Unit):
    def __init__(self,name,hp,attack,defense,xp=0):
        super().__init__(name,hp,attack,defense)
        self._xp = xp

    def get_xp_reward(self):
        return self._xp

    def special_attack(self, target):
        base = self._attack * 2
        variance = random.randint(-3, 3)

        crit = random.random() < self._crit_chance
        dmg = int((base + variance) * (self._crit_multiplier if crit else 1))
        actual = target.take_damage(dmg)
        return actual, crit

#class ItemBag:
 #   def __init__(self,items):
  #      self.items = items

   # def __iter__(self):
    #    return iter(self.items)
#
 #   def __len__(self):
  #      return len(self.items)

class Item:
    def __init__(self, name, item_type, bonus):
        self._name = name
        self._type = item_type
        self._bonus = bonus

    def get_name(self): return self._name
    def get_type(self): return self._type
    def get_bonus(self): return self._bonus

class Inventory:
    def __init__(self):
        self._slots = {}

    def show(self):
        lines = []
        for slot, item in self._slots.items():
            lines.append(f"{item.get_name()} (+{item.get_bonus()})")
        return "\n".join(lines) if lines else "(пусто)"

    def equip(self, item):
        self._slots[item.get_type()] = item

    def get(self, item_type):
        return self._slots.get(item_type)

    def remove(self, item_type):
        if item_type in self._slots:
            del self._slots[item_type]

    def total_attack_bonus(self):
        w = self._slots.get("weapon")
        return w.get_bonus() if w else 0

    def total_defense_bonus(self):
        a = self._slots.get("armor")
        return a.get_bonus() if a else 0

    def total_potion_bonus(self):
        p = self._slots.get("potion")
        return p.get_bonus() if p else 0

    def has_potion(self):
        return "potion" in self._slots

    def __len__(self):
        return len(self._slots)
 
    def __iter__(self):
        return iter(self._slots.values())

class Battle:
    def __init__(self, hero, monster):
        self._hero = hero
        self._monster = monster
        self._log = [] #События

    def fight(self, choose_action):
        while self._hero.is_alive() and self._monster.is_alive():
            action = choose_action(list(self._log))

            if action == "flee":
                if random.random() < 0.5:
                    return self._log, "fled"
                else:
                    self._log.append("Убежать не вышло")
                    action = "attack"

            if action == "potion":
                if self._hero.use_potion():
                    self._log.append("Зелье использовано")
                else:
                    self._log.append("Зелья нет, бьёшь впустую")
                    action = "attack"

            if action == "attack" or action != "flee":
                dmg, crit = self._hero.attack(self._monster)
                if crit:
                    self._log.append(f"Ты наносишь КРИТИЧЕСКИЙ урон {dmg}!")
                else:
                    self._log.append(f"Ты наносишь {dmg} урона")
                if not self._monster.is_alive():
                    break

            if self._monster.is_alive():
                if random.random() < 0.3:
                    dmg, crit = self._monster.special_attack(self._hero)
                    self._log.append(f"{self._monster.get_name()} использует особую атаку: {dmg} урона")
                else:
                    dmg, crit = self._monster.attack(self._hero)
                    s = "КРИТИЧЕСКИЙ " if crit else ""
                    self._log.append(f"{self._monster.get_name()} наносит {s}{dmg} урона")

        if self._hero.is_alive():
            self._log.append("Ты победил!")
            return self._log, "win"
        return self._log, "dead"


WEAPONS = [
    Item("Ржавый нож",        "weapon", 9),
    Item("Дубина", "weapon", 2),
    Item("Стальной клинок",   "weapon", 5),
    Item("Двуручный топор",   "weapon", 7),
    Item("'Лук охотника'",      "weapon", 6),
    Item("Посох странника",   "weapon", 8),
    Item("Легендарный меч",   "weapon", 33),
]

ARMORS = [
    Item("Кожаная куртка",  "armor", 4),
    Item("Тканевые доспехи)х",   "armor", 50),
    Item("Кольчуга",        "armor", 5),
    Item("Кожа", "armor", 7),
    Item("Латный доспех",   "armor", 11),
    Item("Дырявый 'Доспех стража'",   "armor", 3),
    Item("Платиновая броня", "armor", 21),
]

POTIONS = [
    Item("Маленькое зелье здоровья", "potion", 30),
    Item("Большое зелье здоровья",   "potion", 60),
]
# Реестр видов монстров
MONSTER_BASES = [
    {"name": "Гоблин",      "hp": 50,  "attack": 10, "defense": 2, "xp": 30},
    {"name": "Волк",        "hp": 60,  "attack": 13, "defense": 3, "xp": 40},
    {"name": "Скелет",      "hp": 80,  "attack": 15, "defense": 5, "xp": 55},
    {"name": "Лесная тварь","hp": 70,  "attack": 12, "defense": 4, "xp": 45},
    {"name": "Паук",        "hp": 45,  "attack": 11, "defense": 2, "xp": 35},
    {"name": "Гниющий зомби","hp": 90, "attack": 14, "defense": 3, "xp": 60},
    {"name": "Лесной дух",  "hp": 65,  "attack": 16, "defense": 4, "xp": 50},
    {"name": "Ворона-мутант","hp": 40, "attack": 12, "defense": 2, "xp": 32},
    {"name": "Грибной гуль", "hp": 75, "attack": 13, "defense": 5, "xp": 48},
    {"name": "Шакал",       "hp": 55,  "attack": 14, "defense": 2, "xp": 38},
]
BOSS_TYPES = [
    {"name": "Лесной король",     "hp": 200, "attack": 25, "defense": 8,  "xp": 200},
    {"name": "Древний тролль",     "hp": 250, "attack": 28, "defense": 10, "xp": 250},
    {"name": "Тень из костра",     "hp": 180, "attack": 30, "defense": 6,  "xp": 220},
    {"name": "Хранитель оврага",   "hp": 220, "attack": 24, "defense": 12, "xp": 240},
    {"name": "Повелитель ночи",    "hp": 300, "attack": 32, "defense": 12, "xp": 320},
]
def spawn_random_monster():
    data = random.choice(MONSTER_BASES)
    hp = int(data["hp"] * random.uniform(0.85, 1.15))
    attack = int(data["attack"] * random.uniform(0.9,1.1))
    return Monster(data["name"], hp, attack, data["defense"], data["xp"])

def spawn_random_boss():
    data = random.choice(BOSS_TYPES)
    return Monster(data["name"],data["hp"] ,data["attack"], data["defense"], data["xp"])



if __name__ == "__main__":
    print("=== ТЕСТ РЕЕСТРОВ ===\n")
    print("Случайный моб:", spawn_random_monster())
    print("Случайный босс:", spawn_random_boss())
    print("\nОружие:", ", ".join(w.get_name() for w in WEAPONS))
    print("Доспехи:", ", ".join(a.get_name() for a in ARMORS))
    print("Зелья:", ", ".join(p.get_name() for p in POTIONS))

