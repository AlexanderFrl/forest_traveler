import pytest
from unit import Hero

@pytest.fixture
def hero():
    """Фикстура на создание базового ТестГероя"""
    return Hero(name="TestHero", hp=100, attack=1, defense=10)