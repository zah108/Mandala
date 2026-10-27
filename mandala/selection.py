"""Выбор цветов и стилей: взвешенный random, запрет соседних повторов,
   счётчики цветов по областям, ограничение повторов стилей."""
import random

from .config import Config


# ---------------------------------------------------------------
# Состояние палитры (инициализируется в init())
# ---------------------------------------------------------------
COLOR_ENABLED = False
SELECTED_FAMILY = None
ACTIVE_PALETTE = []

recent_colors = []
_fallback_warnings = []

prev_colors = set()
prev2_colors = set()


def init():
    global COLOR_ENABLED, SELECTED_FAMILY, ACTIVE_PALETTE

    if Config.COLOR_MODE == "random":
        COLOR_ENABLED = random.choice([False, True])
    elif Config.COLOR_MODE == "yes":
        COLOR_ENABLED = True
    else:
        COLOR_ENABLED = False

    family_keys = list(Config.COLOR_FAMILIES.keys())

    if Config.PALETTE_CHOICE == "random":
        SELECTED_FAMILY = random.choice(family_keys)
        ACTIVE_PALETTE = Config.COLOR_FAMILIES[SELECTED_FAMILY]["colors"]
    elif Config.PALETTE_CHOICE == "all":
        SELECTED_FAMILY = "all"
        ACTIVE_PALETTE = []
        for k in family_keys:
            ACTIVE_PALETTE.extend(Config.COLOR_FAMILIES[k]["colors"])
    elif Config.PALETTE_CHOICE in Config.COLOR_FAMILIES:
        SELECTED_FAMILY = Config.PALETTE_CHOICE
        ACTIVE_PALETTE = Config.COLOR_FAMILIES[SELECTED_FAMILY]["colors"]
    else:
        SELECTED_FAMILY = random.choice(family_keys)
        ACTIVE_PALETTE = Config.COLOR_FAMILIES[SELECTED_FAMILY]["colors"]


# ---------------------------------------------------------------
# Выбор цветов
# ---------------------------------------------------------------
def pick_color_no_adjacent(recent, palette,
                           forbidden_hard=None, forbidden_soft=None):
    hard = set(forbidden_hard or [])
    soft = set(forbidden_soft or [])
    recent_set = set(recent or [])

    available = [
        c for c in palette
        if c["hex"] not in recent_set
        and c["hex"] not in hard
        and c["hex"] not in soft
    ]
    fallback_stage = 0

    if not available:
        available = [
            c for c in palette
            if c["hex"] not in recent_set
            and c["hex"] not in hard
        ]
        fallback_stage = 1

    if not available:
        available = [c for c in palette if c["hex"] not in recent_set]
        fallback_stage = 2

    if not available:
        available = list(palette)
        fallback_stage = 2

    weights = [max(0.0, c.get("weight", 1.0)) for c in available]
    if sum(weights) <= 0:
        chosen = random.choice(available)
    else:
        chosen = random.choices(available, weights=weights, k=1)[0]
    return chosen["hex"], fallback_stage


def advance_history(area_colors):
    global prev_colors, prev2_colors
    prev2_colors = set(prev_colors)
    prev_colors = set(area_colors)


def pick_colors_for(n, forbidden_hard=None, forbidden_soft=None, area_label=""):
    picked = []
    for _ in range(n):
        c, fb_stage = pick_color_no_adjacent(
            recent_colors, ACTIVE_PALETTE,
            forbidden_hard=forbidden_hard,
            forbidden_soft=forbidden_soft,
        )
        if fb_stage == 1:
            _fallback_warnings.append(
                f"область '{area_label}': ослаблен запрет на позапрошлую область"
            )
        elif fb_stage == 2:
            _fallback_warnings.append(
                f"область '{area_label}': ослаблен запрет на предыдущую область"
            )
        picked.append(c)
        recent_colors.append(c)
        if len(recent_colors) > 2:
            recent_colors.pop(0)
    return picked


def colors_count_for_center(style_idx):
    if style_idx in (2, 9):
        return 2
    return 1


def colors_count_for_band(style_idx):
    if style_idx == 4:
        return 3
    if style_idx in (2, 6, 9):
        return 2
    return 1


def colors_count_for_layer(style_idx):
    if style_idx == 2:
        return 2
    if style_idx in (3, 7, 9, 11, 14, 15):
        return 3
    return 2


# ---------------------------------------------------------------
# Выбор стилей
# ---------------------------------------------------------------
def weighted_choice_styles(style_ids, styles_dict):
    if not style_ids:
        raise ValueError("Нет стилей для выбора")
    weights = [max(0.0, styles_dict[s].get("weight", 1.0)) for s in style_ids]
    if sum(weights) <= 0:
        return random.choice(style_ids)
    return random.choices(style_ids, weights=weights, k=1)[0]


def pick_styles_with_rules(num_slots, styles_dict, max_repeat=2):
    style_ids = list(styles_dict.keys())
    usage = {s: 0 for s in style_ids}
    chosen = []
    prev = None
    for _ in range(num_slots):
        candidates = [s for s in style_ids if usage[s] < max_repeat and s != prev]
        if not candidates:
            candidates = [s for s in style_ids if s != prev]
        choice = weighted_choice_styles(candidates, styles_dict)
        chosen.append(choice)
        usage[choice] += 1
        prev = choice
    return chosen