import pytest
from unit import Hero, Monster, Unit

class TestTakeDamage:
    """Тесты метода take_damage()"""
    @pytest.mark.parametrize("incoming, defense, expected", [
        (25,10, 15),
        (20, 21, 0),
        (100, 0, 100)
    ])
    def test_take_damage_parametrize(self, hero, incoming, defense, expected):
        hero._defense = defense
        hero.take_damage(incoming)
        assert hero._hp == 100 - expected

from unittest.mock import patch
class TestCritHit:
    """Тест критического удара"""
    @patch('random.random',return_value=0.0)
    def test_crit_always(self, mock_random):
        hero = Hero(name="TestHero", hp=100, attack=20, defense=0, crit_chance=0.15, crit_multiplier=2.0)
        target = Monster(name="Target", hp=100, attack=1, defense=0)
        dmg,is_crit = hero.attack(target)
        assert is_crit is True
        assert dmg == 40

    @patch('random.random',return_value=0.99)
    def test_no_chance_crit_when_low(self, mock_random):
        hero = Hero(name="TestHero", hp=100, attack=20, defense=0, crit_chance=0.15, crit_multiplier=2.0)
        target = Monster(name="Target", hp=100, attack=1, defense=0)
        dmg,is_crit = hero.attack(target)
        assert is_crit is False
        assert dmg == 20

class TestInventory:
    """Тесты инвентаря и зелий"""
    def test_equip_and_get_weapon(self):
        """Получение оружия и его бонуса"""
        from unit import Item
        hero = Hero(name="TestHero", hp=100, attack=1, defense= 5)
        sword = Item(name="Меч", item_type="weapon", bonus=10)
        hero.get_inventory().equip(sword)
        assert hero.get_inventory().get("weapon") == sword
        assert hero.get_attack() == 11

    def test_equip_and_get_armor(self):
        """Получение брони и бонуса"""
        from unit import Item
        hero = Hero(name="TestHero", hp=100, attack=1, defense=5)
        sword = Item(name="Броня", item_type="armor", bonus=10)
        hero.get_inventory().equip(sword)
        assert hero.get_inventory().get("armor") == sword
        assert hero.get_defense() == 15

    def test_use_potion_restores_hp(self):
        from unit import Item
        hero = Hero(name="TestHero", hp=50, attack=1, defense=5)
        hero._max_hp = 100
        potion = Item("Зелье", "potion", 30)
        hero.get_inventory().equip(potion)
        result = hero.use_potion()
        assert result is True
        assert hero.get_hp() == 80
        assert hero.get_inventory().get("potion") is None

    def test_use_potion_when_empty(self):
        from unit import Item
        hero = Hero(name="TestHero", hp=50, attack=1, defense=5)
        result = hero.use_potion()
        assert result is False
        assert hero.get_hp() == 50

    
class TestLevelUp:
    """Тесты повышения уровня"""
    def test_get_xp_trigger_level_up(self):
        """При достижение 100 опыта лвл повышается"""
        hero = Hero(name="TestHero", hp=100, attack=1, defense=5)
        hero._experience = 90
        hero._level = 1
        hero.gain_xp(11)
        assert hero._level == 2
        assert hero._experience == 0
        assert hero.get_max_hp() == 121
        assert hero.get_hp() == 121
        assert hero.get_attack() == 4
        assert hero.get_defense() == 7

    def test_get_xp_no_level_up(self):
        hero = Hero(name="TestHero", hp=100, attack=1, defense=5)
        hero._experience = 50
        hero._level = 1
        hero.gain_xp(30)
        assert hero._experience == 80
        assert hero._level == 1
