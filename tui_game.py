import random
from queue import Queue
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, RichLog
from textual import work

from Fan.unit import Battle, WEAPONS, ARMORS, POTIONS, spawn_random_monster, spawn_random_boss
from game import LOCATIONS, make_hero

import random
from queue import Queue
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, RichLog
from textual import work

# Импортируем ваши классы из оригинальных файлов
from Fan.unit import Battle, WEAPONS, ARMORS, POTIONS, spawn_random_monster, spawn_random_boss
from game import LOCATIONS, make_hero


class HeroStats(Static):
    """Виджет для красивого отображения статов героя слева."""

    def update_stats(self, hero):
        inv = hero.get_inventory()
        # Форматируем текст с помощью rich-тегов (цвета и стили)
        stats = (
            f"[b]{hero.get_name()}[/b] (Уровень {hero._level})\n\n"
            f"HP: [red]{hero.get_hp()} / {hero.get_max_hp()}[/red]\n"
            f"Опыт: {hero._experience} / 100\n\n"
            f"[b]Характеристики:[/b]\n"
            f"Урон: {hero.get_attack()}\n"
            f"Защита: {hero.get_defense()}\n\n"
            f"[b]Инвентарь:[/b]\n"
            f"{inv.show()}"
        )
        self.update(stats)


class ForestTUI(App):
    """Главный класс приложения."""

    # CSS-стили для сетки из 3-х колонок
    CSS = """
    Screen { layout: horizontal; }
    #left-panel { width: 25%; border: solid green; padding: 1; }
    #center-panel { width: 45%; border: solid blue; padding: 1; }
    #right-panel { width: 30%; border: solid red; padding: 1; }
    #story-log { height: 1fr; }
    #combat-log { height: 1fr; }
    #action-panel { height: auto; align: center bottom; margin-top: 1; }
    Button { margin: 1; }
    .panel-title { text-align: center; width: 100%; text-style: bold; }
    """

    def compose(self) -> ComposeResult:
        yield Header("Путник леса - Textual Edition")

        with Horizontal():
            # Левая колонка: Персонаж
            with Vertical(id="left-panel"):
                yield Static("ГЕРОЙ", classes="panel-title")
                yield HeroStats(id="hero-stats")

            # Центральная колонка: Сюжет и Выборы
            with Vertical(id="center-panel"):
                yield Static("ИСТОРИЯ", classes="panel-title")
                yield RichLog(id="story-log", wrap=True)
                yield Horizontal(id="action-panel")  # Место для кнопок

            # Правая колонка: Бой
            with Vertical(id="right-panel"):
                yield Static("ЛОГ БОЯ", classes="panel-title")
                yield RichLog(id="combat-log", wrap=True)

        yield Footer()

    def on_mount(self) -> ComposeResult:
        # Инициализация игры
        self.action_queue = Queue()  # Очередь для связи UI и потока боя
        self.hero = make_hero()
        self.current_loc = "start"
        self.state = "EXPLORING"

        # Получаем ссылки на виджеты
        self.story_log = self.query_one("#story-log", RichLog)
        self.combat_log = self.query_one("#combat-log", RichLog)
        self.hero_stats = self.query_one("#hero-stats", HeroStats)
        self.action_panel = self.query_one("#action-panel", Horizontal)

        self.update_hero_stats()
        self.load_location()

    def update_hero_stats(self):
        self.hero_stats.update_stats(self.hero)

    def load_location(self):
        """Парсинг локации из словаря LOCATIONS."""
        loc = LOCATIONS[self.current_loc]
        self.story_log.write(f"\n[b]--- Вы здесь: {self.current_loc.upper()} ---[/b]")
        self.story_log.write(loc["text"])

        if loc["event"] in ["monster", "boss"]:
            self.start_battle(is_boss=(loc["event"] == "boss"))
        elif loc["event"] == "item":
            self.give_random_item()
            self.show_location_choices(loc)
        elif loc.get("is_end"):
            self.story_log.write("\n[b red]— КОНЕЦ ИГРЫ —[/b red]")
            self.clear_buttons()
        else:
            self.show_location_choices(loc)

    def give_random_item(self):
        item = random.choice(WEAPONS + ARMORS + POTIONS)
        self.hero.get_inventory().equip(item)
        self.combat_log.write(f"[green]Ты находишь: {item.get_name()} (+{item.get_bonus()})[/green]")
        self.update_hero_stats()

    def clear_buttons(self):
        """Удаляем старые кнопки перед показом новых."""
        for btn in list(self.action_panel.children):
            btn.remove()

    def show_location_choices(self, loc):
        self.state = "EXPLORING"
        self.clear_buttons()
        # Создаем кнопки на основе словаря 'choices'
        for key, (desc, next_loc) in loc["choices"].items():
            btn = Button(desc, id=f"loc_{next_loc}", variant="primary")
            self.action_panel.mount(btn)

    def show_battle_choices(self):
        self.state = "BATTLE"
        self.clear_buttons()
        self.action_panel.mount(Button("Атаковать", id="btn_attack", variant="error"))
        self.action_panel.mount(Button("Зелье", id="btn_potion", variant="success"))
        self.action_panel.mount(Button("Сбежать", id="btn_flee", variant="warning"))

    @work(thread=True)
    def start_battle(self, is_boss):
        """Этот метод работает в фоне и не вешает UI."""
        self.call_from_thread(self.show_battle_choices)

        monster = spawn_random_boss() if is_boss else spawn_random_monster()
        self.call_from_thread(self.combat_log.write, f"\n[bold red]Враг: {monster.get_name()}![/bold red]")

        battle = Battle(self.hero, monster)

        log_cursor = 0  # Чтобы не печатать лог целиком каждый ход, запоминаем, где остановились

        # Кастомная функция callback для ядра игры
        def sync_choose_action(log):
            nonlocal log_cursor
            # Отправляем в UI только новые строчки лога
            while log_cursor < len(log):
                self.call_from_thread(self.combat_log.write, f"  {log[log_cursor]}")
                log_cursor += 1

            self.call_from_thread(self.update_hero_stats)

            # ТУТ МАГИЯ: Поток засыпает и ждет, пока игрок не нажмет кнопку в UI
            action = self.action_queue.get()
            return action

        # Запускаем оригинальный fight() [не меняя unit.py]
        final_log, outcome = battle.fight(sync_choose_action)

        # Выводим оставшиеся (финальные) строчки лога
        while log_cursor < len(final_log):
            self.call_from_thread(self.combat_log.write, f"  {final_log[log_cursor]}")
            log_cursor += 1

        self.call_from_thread(self.end_battle, monster, outcome)

    def end_battle(self, monster, outcome):
        """Завершение боя и возврат к сюжету."""
        self.update_hero_stats()
        if outcome == "win":
            xp = monster.get_xp_reward()
            self.hero.gain_xp(xp)
            self.combat_log.write(f"[bold green]Получено {xp} опыта.[/bold green]")
            self.update_hero_stats()
            self.show_location_choices(LOCATIONS[self.current_loc])
        else:
            self.story_log.write("\n[bold red]Ты погиб. Игра окончена.[/bold red]")
            self.clear_buttons()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Слушатель всех нажатий кнопок в интерфейсе."""
        button_id = event.button.id

        if self.state == "EXPLORING":
            if button_id and button_id.startswith("loc_"):
                self.current_loc = button_id.replace("loc_", "")
                self.load_location()

        elif self.state == "BATTLE":
            # Разблокируем фоновый поток с боем, передав ему строку-команду
            if button_id == "btn_attack":
                self.action_queue.put("attack")
            elif button_id == "btn_potion":
                self.action_queue.put("potion")
            elif button_id == "btn_flee":
                self.action_queue.put("flee")


if __name__ == "__main__":
    app = ForestTUI()
    app.run()

