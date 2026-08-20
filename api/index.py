from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse,Response
from pydantic import BaseModel
from pathlib import Path
import time

app = FastAPI(title="Sargam Game")

STATIC_DIR = Path(__file__).parent.parent / "static"

MAX_HP = 1000
DAMAGE_PER_HIT = 20
BANDAGED_THRESHOLD = 500
REGEN_TRIGGER_HP = 100
REGEN_TARGET_HP = 500


def fresh_state():
    return {
        "hp": MAX_HP,
        "max_hp": MAX_HP,
        "sprite_tier": "normal",
        "alive": True,
        "friends": False,
        "cycle": 1,
        "regen_queued": False,
        "last_event": None,
        "event_id": 0,
        "history": [],
    }

state = fresh_state()


def push_event(kind: str, **extra):
    state["event_id"] += 1
    state["last_event"] = {
        "id": state["event_id"],
        "kind": kind,
        "timestamp": time.time(),
        **extra,
    }
    state["history"].append(state["last_event"])
    if len(state["history"]) > 50:
        state["history"] = state["history"][-50:]


def sprite_tier_for(hp: int) -> str:
    if hp <= BANDAGED_THRESHOLD:
        return "bandaged"
    return "normal"


def start_new_cycle():
    state["cycle"] += 1
    state["regen_queued"] = False


def apply_hit(amount: int = DAMAGE_PER_HIT):
    if not state["alive"] or state["friends"]:
        return

    prev_hp = state["hp"]
    new_hp = max(0, prev_hp - amount)
    state["hp"] = new_hp

    push_event("hit", damage=amount, hp=new_hp)

    prev_tier_100 = prev_hp // 100
    new_tier_100 = new_hp // 100
    if new_tier_100 < prev_tier_100 or (new_hp == 0 and prev_hp > 0):
        push_event("fall_get_up", hp=new_hp)

    state["sprite_tier"] = sprite_tier_for(new_hp)

    if new_hp <= REGEN_TRIGGER_HP:
        if new_hp > 0 and state["regen_queued"]:
            state["hp"] = REGEN_TARGET_HP
            state["sprite_tier"] = sprite_tier_for(state["hp"])
            push_event("regen", hp=state["hp"])
            start_new_cycle()
        elif new_hp <= 0:
            state["hp"] = 0
            state["alive"] = False
            state["friends"] = True
            state["sprite_tier"] = "friends"
            push_event("friends", hp=0)


class LeaderboardEvent(BaseModel):
    correct: bool


# ===========================================================================
# LEADERBOARD INTEGRATION POINT
# The leaderboard's backend should POST here every time it grades an answer.
# Body: {"correct": true/false, "user": "...", "question_id": "...", "meta": {...}}
# Only "correct" is required. On correct=true, the villain takes damage;
# correct=false is a no-op. No changes needed inside this function.
# ===========================================================================
@app.post("/webhook/leaderboard-event")
async def leaderboard_event(evt: LeaderboardEvent):
    triggered = False
    if evt.correct:
        apply_hit(DAMAGE_PER_HIT)
        triggered = True
    return Response(status_code=200)


@app.get("/state")
async def get_state():
    return state


class RegenChoice(BaseModel):
    regenerate: bool


@app.post("/regen")
async def set_regen(choice: RegenChoice):
    if not state["alive"] or state["friends"]:
        return state
    state["regen_queued"] = choice.regenerate
    push_event(
        "regen_queued" if choice.regenerate else "regen_unqueued",
        cycle=state["cycle"],
    )
    return state


@app.post("/admin/reset")
async def reset():
    global state
    state = fresh_state()
    return state


# ---------------------------------------------------------------------------
# DEV/TEST ONLY — simulate leaderboard events without a real leaderboard.
# Delete these two endpoints (and the matching dev-panel buttons in
# index.html) once /webhook/leaderboard-event above is wired to the real
# leaderboard. Keep /admin/reset — that one's useful to leave in.
# ---------------------------------------------------------------------------
@app.post("/admin/simulate-correct")
async def simulate_correct():
    apply_hit(DAMAGE_PER_HIT)
    return state


@app.post("/admin/simulate-wrong")
async def simulate_wrong():
    push_event("no_damage_wrong_answer")
    return state


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/regen")
async def regen_page():
    return FileResponse(STATIC_DIR / "regen.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")