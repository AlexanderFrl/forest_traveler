import json
import asyncio
import threading
import queue
import random
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from game import LOCATIONS, make_hero
from unit import Battle, spawn_random_monster, spawn_random_boss, WEAPONS, ARMORS, POTIONS

app = FastAPI()

with open("index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

@app.get("/")
async def get():
    return HTMLResponse(html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    action_queue = queue.Queue()
    message_queue = asyncio.Queue()

    def send_sync(msg_dict):
        websocket.app.state.loop.call_soon_threadsafe(message_queue.put_nowait, msg_dict)

    def send_stats(hero):
        send_sync({
            "type": "stats",
            "hp": hero.get_hp(),
            "max_hp": hero.get_max_hp(),
            "level": hero._level,
            "xp": hero._experience,
            "inventory": hero.get_inventory().show()
        })

    def update_map(stage_idx, location_name):
        send_sync({
            "type": "map",
            "stage": stage_idx,
            "name": location_name
        })

    def web_choose_action(log):
        send_sync({
            "type": "choices", 
            "options": [
                {"text": "⚔️ Рубить", "action": "attack"},
                {"text": "🩸 Выпить кровь (Зелье)", "action": "potion"},
                {"text": "🏃 Отступить во тьму", "action": "flee"}
            ]
        })
        return action_queue.get()

    def game_thread():
        hero = make_hero()
        current = "start"
        send_stats(hero)
        send_sync({"type": "combat", "text": "Ты осматриваешь себя. Боги послали тебе случайное снаряжение..."})

        while True:
            loc = LOCATIONS[current]
            update_map(loc["stage_index"], loc["name"])
            send_sync({"type": "story", "location": loc["name"], "text": loc["text"]})

            is_dead = False
            
            if loc["event"] in ["monster", "boss"]:
                monster = spawn_random_boss() if loc["event"] == "boss" else spawn_random_monster()
                send_sync({"type": "combat", "text": f"\nИз теней шагает {monster.get_name()}!"})
                
                battle = Battle(hero, monster)
                log_cursor = 0
                
                def sync_action(log):
                    nonlocal log_cursor
                    while log_cursor < len(log):
                        send_sync({"type": "combat", "text": log[log_cursor]})
                        log_cursor += 1
                    send_stats(hero)
                    return web_choose_action(log)

                final_log, outcome = battle.fight(sync_action)
                
                while log_cursor < len(final_log):
                    send_sync({"type": "combat", "text": final_log[log_cursor]})
                    log_cursor += 1
                
                if outcome == "win":
                    xp = monster.get_xp_reward()
                    hero.gain_xp(xp)
                    
                    # ГАРАНТИРОВАННЫЙ ЛУТ ПОСЛЕ БОЯ
                    dropped_item = random.choice(WEAPONS + ARMORS + POTIONS)
                    hero.get_inventory().equip(dropped_item)
                    
                    send_sync({"type": "combat", "text": f"Ты поглощаешь {xp} душ."})
                    send_sync({"type": "combat", "text": f"С растерзанного трупа падает: {dropped_item.get_name()} (+{dropped_item.get_bonus()})"})
                    send_stats(hero)
                else:
                    send_sync({"type": "story", "location": "ПУСТОТА", "text": "Твоя плоть разорвана. Тьма поглотила тебя."})
                    is_dead = True

            if is_dead or loc.get("is_end"):
                send_sync({"type": "choices", "options": []}) # Убираем кнопки
                break

            choices_list = [{"text": desc, "action": f"loc_{next_loc}"} for key, (desc, next_loc) in loc["choices"].items()]
            send_sync({"type": "choices", "options": choices_list})
            
            choice_action = action_queue.get()
            if choice_action.startswith("loc_"):
                current = choice_action.replace("loc_", "")

    websocket.app.state.loop = asyncio.get_running_loop()
    threading.Thread(target=game_thread, daemon=True).start()

    async def receive_from_browser():
        try:
            while True:
                action_queue.put(json.loads(await websocket.receive_text())["action"])
        except Exception: pass

    async def send_to_browser():
        try:
            while True: await websocket.send_json(await message_queue.get())
        except Exception: pass

    await asyncio.gather(receive_from_browser(), send_to_browser())