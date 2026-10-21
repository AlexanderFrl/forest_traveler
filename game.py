import random
from unit import Hero, Battle, WEAPONS, ARMORS, POTIONS, spawn_random_monster, spawn_random_boss, Item
LOCATIONS = {
    "start": {
        "stage_index": 0,
        "name": "ПЕПЕЛЬНАЯ ПУСТОШЬ",
        "text": (
            "Ты открываешь глаза. С чёрного неба медленно осыпается серый пепел.\n"
            "Твоя память пуста, но инстинкт вопит: нужно идти вперед, или эта земля поглотит тебя.\n"
            "Впереди виднеется гнилой лес, а справа — ущелье, из которого тянет трупным ядом."
        ),
        "choices": {
            "1": ("Войти в Мёртвый лес", "forest"),
            "2": ("Спуститься в Гнилое ущелье", "canyon"),
        },
        "event": None,
    },
    "forest": {
        "stage_index": 1,
        "name": "МЁРТВЫЙ ЛЕС",
        "text": "Изувеченные деревья тянут к тебе ветви. Из темноты раздается хруст костей — на тебя выходит тварь.",
        "choices": {"1": ("Продвигаться глубже", "swamp")},
        "event": "monster",
    },
    "canyon": {
        "stage_index": 1,
        "name": "ГНИЛОЕ УЩЕЛЬЕ",
        "text": "Ты бредешь по колено в костях. Внезапно кости начинают собираться воедино...",
        "choices": {"1": ("Выбраться к топям", "swamp")},
        "event": "monster",
    },
    "swamp": {
        "stage_index": 2,
        "name": "КРОВАВАЯ ТОПЬ",
        "text": "Под ногами чавкает багровая жижа. В центре топи возвышается алтарь с брошенным предметом.",
        "choices": {
            "1": ("Подойти к алтарю (Взять предмет)", "swamp_item"),
            "2": ("Обойти стороной к Часовне", "chapel")
        },
        "event": None,
    },
    "swamp_item": {
        "stage_index": 2,
        "name": "АЛТАРЬ",
        "text": "Как только твоя рука касается предмета, вода закипает. Хранитель алтаря пробудился!",
        "choices": {"1": ("Бежать к Часовне", "chapel")},
        "event": "boss",
    },
    "chapel": {
        "stage_index": 3,
        "name": "ОСКВЕРНЁННАЯ ЧАСОВНЯ",
        "text": "Запах ладана смешался с запахом гнили. Внутри тебя ждет Хозяин этих земель.",
        "choices": {"1": ("Принять бой", "ending_win")},
        "event": "boss",
    },
    "ending_win": {
        "stage_index": 4,
        "name": "ВРАТА БЕЗДНЫ",
        "text": "Тварь издает предсмертный хрип и рассыпается прахом. Врата открыты. Ты свободен... но какой ценой?",
        "choices": {},
        "event": None,
        "is_end": True,
    }
}

def make_hero():
    """Создаёт героя со случайной стартовой экипировкой."""
    hero = Hero("Обречённый", 150, 15, 5)
    inv = hero.get_inventory()
    # Рандомный лут на старте из реестров unit_2.py
    inv.equip(random.choice(WEAPONS))
    inv.equip(random.choice(ARMORS))
    inv.equip(random.choice(POTIONS))
    return hero

def choose_action(log):
    # Показываем весь накопленный лог боя
    for line in log[-3:]:  # последние 3 события
        print("  " + line)

    print("\n[1] Атаковать   [2] Выпить зелье   [3] Сбежать")

    while True:
        choice = input("Твой ход (1/2/3): ").strip()
        if choice == "1":
            return "attack"
        if choice == "2":
            return "potion"
        if choice == "3":
            return "flee"
        print("Некорректный ввод. Введи 1, 2 или 3.")

def encounter(hero, is_boss=False):
    """Один бой. is_boss=True — спавним босса. Возвращает True, если герой жив."""
    monster = spawn_random_boss() if is_boss else spawn_random_monster()
    print(f"\nНа тебя нападает {monster}!")
    battle = Battle(hero, monster)
    log, outcome = battle.fight(choose_action)
    for line in log:
        print("  " + line)
    if outcome == "win":
        hero.gain_xp(monster.get_xp_reward())
        print(f"Получено {monster.get_xp_reward()} опыта.")
        return True
    return False

def give_item(hero):
    """Даёт герою случайный предмет (заменяя старый в слоте)."""
    item = random.choice(WEAPONS + ARMORS + POTIONS)
    hero.get_inventory().equip(item)
    print(f"Ты находишь: {item.get_name()} (+{item.get_bonus()})")

def main():
    """Главная функция — управляет всей игрой."""
    print("=== Путник леса ===\n")
    hero = make_hero()
    current = "start"

    while True:
        loc = LOCATIONS[current]
        print("\n" + loc["text"])

        # Событие локации
        if loc["event"] == "monster":
            if not encounter(hero):
                print("\nТы погиб. Игра окончена.")
                break
        elif loc["event"] == "boss":
            if not encounter(hero, is_boss=True):
                print("\nТы погиб у босса. Игра окончена.")
                break
        elif loc["event"] == "item":
            give_item(hero)

        # Конец?
        if loc.get("is_end"):
            print("\n— КОНЕЦ ИГРЫ —")
            break

        # Выбор тропы
        print("\nКуда идти?")
        for key, (desc, _) in loc["choices"].items():
            print(f"  [{key}] {desc}")
        choice = input("Выбор: ")
        if choice in loc["choices"]:
            current = loc["choices"][choice][1]
        else:
            print("Некорректный ввод.")

if __name__ == "__main__":
    main()

