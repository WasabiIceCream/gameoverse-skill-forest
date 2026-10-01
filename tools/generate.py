#!/usr/bin/env python3
"""Build the gameoverse_skill_forest datapack: the Skill Forest, one huge Pufferfish's Skills tab.

See ../README.md and docs/skill-forest-design.md. Writes ../datapack/:
  - data/gameoverse/puffish_skills/: the tab `gameoverse:forest`:
      * the class cores: Skill Tree's 8 class branches (read from its jar, in place, as the exclusive starts),
      * a gateway past each branch tip,
      * 8 regions in the lanes between classes (stat lattices, notables, keystones, 2 weapon clusters each, the
        weapon clusters read from Skill Tree's weapon tab),
      * the Craft ring around the regions, and the Endless Rim around everything.
  - data/skill_tree_rpgs/puffish_skills/config.json: no categories (turns Skill Tree's own two tabs off).
  - The Orb of Oblivion recipe (Diamond Block + 2 Gem Dust) and its unlock.
  - Functions giving World Tier bonus points (called by gameoverse_farming_path's tier advancements).

Everything written is validated first (attribute ids, spell ids, links, reachability): one bad value in any pack makes
Pufferfish's Skills load no tabs at all. Re-run after Skill Tree, Apotheosis or Pufferfish's Attributes updates:
    python3 tools/generate.py
"""
import glob
import json
import math
import os
import shutil
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SERVER = os.path.join(ROOT, "..", "..", "fabric 26.1")
MODS = os.path.join(SERVER, "mods")
OUT = os.path.join(ROOT, "datapack")
CAT_DIR = "data/gameoverse/puffish_skills/categories/forest"
CATEGORY = "gameoverse:forest"

# --- jars -------------------------------------------------------------------------------------------------------------


def jar(pattern):
    found = glob.glob(os.path.join(MODS, pattern))
    if len(found) != 1:
        raise SystemExit(f"expected one jar for {pattern}, found {found}")
    return zipfile.ZipFile(found[0])


def read_json(z, path):
    return json.loads(z.read(path))


# --- attribute ids the validator accepts ------------------------------------------------------------------------------

VANILLA_ATTRIBUTES = {
    "armor", "armor_toughness", "attack_damage", "attack_knockback", "attack_speed", "block_break_speed",
    "block_interaction_range", "entity_interaction_range", "fall_damage_multiplier", "jump_strength",
    "knockback_resistance", "luck", "max_health", "mining_efficiency", "movement_speed", "safe_fall_distance",
    "sneaking_speed", "submerged_mining_speed", "sweeping_damage_ratio", "water_movement_efficiency",
}


def known_attributes():
    ids = {"minecraft:" + a for a in VANILLA_ATTRIBUTES}
    with jar("apothic-attributes-fabric-*.jar") as z:
        src = [n for n in z.namelist() if n.endswith("en_us.json") and "apothic_attributes" in n]
        for key in read_json(z, src[0]):
            if key.startswith("apothic_attributes:") and "." not in key:
                ids.add(key)
    with jar("puffish_attributes-*.jar") as z:
        for v in read_json(z, "data/puffish_attributes/tags/attribute/dynamic.json")["values"]:
            ids.add(v)
    for pattern in ("spell_power-*.jar", "ranged_weapon_api-*.jar", "critical_strike-*.jar", "spell_engine-*.jar",
                    "enderscape-*.jar", "artifacts-*.jar"):
        with jar(pattern) as z:
            for n in z.namelist():
                if n.endswith("lang/en_us.json"):
                    for key in read_json(z, n):
                        for prefix in ("attribute.name.", "attribute."):
                            if key.startswith(prefix):
                                rest = key[len(prefix):]
                                ns, _, path = rest.partition(".")
                                if path and not path.endswith(("desc", "description", "tooltip")):
                                    ids.add(f"{ns}:{path}")
                                break
    # Mana Attributes registers under "manaattributes:" but its lang keys carry no namespace (attribute.name.max_mana).
    with jar("mana-attributes-*.jar") as z:
        for n in z.namelist():
            if n.endswith("lang/en_us.json"):
                for key in read_json(z, n):
                    if key.startswith("attribute.name.") and key.count(".") == 2:
                        ids.add("manaattributes:" + key.split(".")[2])
    return ids


# --- stats ------------------------------------------------------------------------------------------------------------
# (attribute, operation, small value, notable value, display format, name, icon item)
# display: "pct" shows value*100 as %, "flat" shows the number. Operations use Pufferfish's names.

ADD, MB, MT = "addition", "multiply_base", "multiply_total"

STATS = {
    "crit_chance": ("apothic_attributes:crit_chance", ADD, 0.01, 0.04, "pct", "Crit Chance", "minecraft:flint"),
    "crit_damage": ("apothic_attributes:crit_damage", ADD, 0.03, 0.10, "pct", "Crit Damage", "minecraft:quartz"),
    "dodge": ("apothic_attributes:dodge_chance", ADD, 0.005, 0.02, "pct", "Dodge Chance", "minecraft:phantom_membrane"),
    "attack_speed": ("minecraft:attack_speed", MB, 0.01, 0.04, "pct", "Attack Speed", "minecraft:feather"),
    "move_speed": ("minecraft:movement_speed", MB, 0.01, 0.03, "pct", "Movement Speed", "minecraft:sugar"),
    "armor_pierce": ("apothic_attributes:armor_pierce", ADD, 0.5, 2, "flat", "Armor Pierce", "minecraft:iron_nugget"),
    "armor_shred": ("apothic_attributes:armor_shred", ADD, 0.01, 0.04, "pct", "Armor Shred", "minecraft:shears"),
    "projectile_damage": ("apothic_attributes:projectile_damage", ADD, 0.02, 0.06, "pct", "Projectile Damage", "minecraft:arrow"),
    "ranged_damage": ("ranged_weapon:damage", MB, 0.02, 0.06, "pct", "Ranged Damage", "minecraft:bow"),
    "draw_speed": ("apothic_attributes:draw_speed", ADD, 0.02, 0.06, "pct", "Draw Speed", "minecraft:string"),
    "arrow_velocity": ("apothic_attributes:arrow_velocity", ADD, 0.02, 0.06, "pct", "Arrow Velocity", "minecraft:spectral_arrow"),
    "tamed_damage": ("puffish_attributes:tamed_damage", MB, 0.03, 0.10, "pct", "Pet Damage", "minecraft:bone"),
    "tamed_resistance": ("puffish_attributes:tamed_resistance", MB, 0.02, 0.06, "pct", "Pet Damage Resistance", "minecraft:lead"),
    "mount_speed": ("artifacts:mount_speed", ADD, 0.02, 0.06, "pct", "Mount Speed", "minecraft:saddle"),
    "stealth": ("enderscape:stealth", ADD, 0.02, 0.06, "pct", "Stealth", "minecraft:black_dye"),
    "fall_safety": ("minecraft:safe_fall_distance", ADD, 0.5, 2, "flat", "Safe Fall Distance", "minecraft:hay_block"),
    "jump": ("minecraft:jump_strength", MB, 0.02, 0.06, "pct", "Jump Strength", "minecraft:rabbit_foot"),
    "spell_arcane": ("spell_power:arcane", MB, 0.02, 0.06, "pct", "Arcane Spell Power", "minecraft:amethyst_shard"),
    "spell_fire": ("spell_power:fire", MB, 0.02, 0.06, "pct", "Fire Spell Power", "minecraft:blaze_powder"),
    "spell_frost": ("spell_power:frost", MB, 0.02, 0.06, "pct", "Frost Spell Power", "minecraft:snowball"),
    "spell_all": ("spell_power:generic", MB, 0.01, 0.03, "pct", "Spell Power", "minecraft:lapis_lazuli"),
    "spell_haste": ("spell_power:haste", MB, 0.01, 0.04, "pct", "Spell Haste", "minecraft:glowstone_dust"),
    "max_mana": ("manaattributes:max_mana", ADD, 5, 20, "flat", "Max Mana", "minecraft:prismarine_crystals"),
    "mana_regen": ("manaattributes:mana_regeneration", ADD, 0.25, 1, "flat", "Mana Regeneration", "minecraft:glow_ink_sac"),
    "cooldown": ("apothic_attributes:cooldown_reduction", ADD, 0.01, 0.04, "pct", "Cooldown Reduction", "minecraft:clock"),
    "magic_resistance": ("puffish_attributes:magic_resistance", MB, 0.02, 0.06, "pct", "Magic Damage Resistance", "minecraft:purple_dye"),
    "fire_damage": ("apothic_attributes:fire_damage", ADD, 0.5, 2, "flat", "Fire Damage", "minecraft:fire_charge"),
    "cold_damage": ("apothic_attributes:cold_damage", ADD, 0.5, 2, "flat", "Cold Damage", "minecraft:blue_ice"),
    "life_steal": ("apothic_attributes:life_steal", ADD, 0.005, 0.02, "pct", "Life Steal", "minecraft:red_dye"),
    "overheal": ("apothic_attributes:overheal", ADD, 0.01, 0.04, "pct", "Overheal", "minecraft:golden_apple"),
    "reflection": ("puffish_attributes:damage_reflection", MB, 0.01, 0.04, "pct", "Damage Reflection", "minecraft:cactus"),
    "resistance": ("puffish_attributes:resistance", MB, 0.005, 0.02, "pct", "Damage Resistance", "minecraft:iron_ingot"),
    "healing_power": ("spell_power:healing", MB, 0.02, 0.06, "pct", "Healing Spell Power", "minecraft:glistering_melon_slice"),
    "healing_received": ("apothic_attributes:healing_received", ADD, 0.02, 0.06, "pct", "Healing Received", "minecraft:honey_bottle"),
    "armor": ("minecraft:armor", ADD, 0.5, 2, "flat", "Armor", "minecraft:iron_chestplate"),
    "toughness": ("minecraft:armor_toughness", ADD, 0.25, 1, "flat", "Armor Toughness", "minecraft:diamond_chestplate"),
    "attack_damage": ("minecraft:attack_damage", MB, 0.015, 0.05, "pct", "Attack Damage", "minecraft:iron_sword"),
    "knockback": ("minecraft:attack_knockback", ADD, 0.05, 0.2, "flat", "Attack Knockback", "minecraft:piston"),
    "sword_damage": ("puffish_attributes:sword_damage", MB, 0.02, 0.06, "pct", "Sword Damage", "minecraft:stone_sword"),
    "axe_damage": ("puffish_attributes:axe_damage", MB, 0.02, 0.06, "pct", "Axe Damage", "minecraft:stone_axe"),
    "mace_damage": ("puffish_attributes:mace_damage", MB, 0.02, 0.06, "pct", "Mace Damage", "minecraft:mace"),
    "trident_damage": ("puffish_attributes:trident_damage", MB, 0.02, 0.06, "pct", "Trident Damage", "minecraft:trident"),
    "fortune": ("puffish_attributes:fortune", ADD, 0.05, 0.2, "flat", "Fortune", "minecraft:emerald"),
    "pickaxe_speed": ("puffish_attributes:pickaxe_speed", MB, 0.03, 0.10, "pct", "Pickaxe Speed", "minecraft:iron_pickaxe"),
    "axe_speed": ("puffish_attributes:axe_speed", MB, 0.03, 0.10, "pct", "Axe Speed", "minecraft:iron_axe"),
    "shovel_speed": ("puffish_attributes:shovel_speed", MB, 0.03, 0.10, "pct", "Shovel Speed", "minecraft:iron_shovel"),
    "mining_efficiency": ("minecraft:mining_efficiency", ADD, 1, 3, "flat", "Mining Efficiency", "minecraft:golden_pickaxe"),
    "repair_cost": ("puffish_attributes:repair_cost", MB, -0.02, -0.06, "pct", "Anvil Repair Cost", "minecraft:anvil"),
    "xp_gained": ("apothic_attributes:experience_gained", ADD, 0.02, 0.06, "pct", "Experience Gained", "minecraft:experience_bottle"),
    "luck": ("minecraft:luck", ADD, 0.1, 0.5, "flat", "Luck", "minecraft:rabbit_hide"),
}

# --- classes and regions ----------------------------------------------------------------------------------------------
# Class order is Skill Tree's layout, clockwise from the top (screen y points down). Angles in degrees.

CLASSES = ["fire", "frost", "priest", "paladin", "warrior", "rogue", "archer", "arcane"]

# Region between CLASSES[i] and CLASSES[i+1]:
# name, small stats (cycled over the lattice), notables [(title, [stats])], keystones, weapon roots
REGIONS = [
    ("Elements", ["spell_fire", "spell_frost", "fire_damage", "cold_damage", "spell_all", "max_mana"],
     [("Kindling", ["spell_fire", "fire_damage"]), ("Rime", ["spell_frost", "cold_damage"]),
      ("Elemental Mastery", ["spell_fire", "spell_frost", "mana_regen"])],
     ["glass_cannon"], ["weapon_fire_root", "weapon_frost_root"]),
    ("Vitality", ["life_steal", "overheal", "reflection", "resistance", "healing_received"],
     [("Leech", ["life_steal", "overheal"]), ("Thorns", ["reflection", "resistance"]),
      ("Second Wind", ["healing_received", "overheal"])],
     ["bloodthirst", "lifeweaver"], ["weapon_axe_root", "weapon_double_axe_root"]),
    ("Devotion", ["healing_power", "healing_received", "resistance", "armor", "spell_all", "mana_regen"],
     [("Sanctuary", ["healing_power", "healing_received"]), ("Bulwark", ["resistance", "armor"]),
      ("Faith", ["healing_power", "spell_all", "max_mana"])],
     ["unshakeable"], ["weapon_holy_root", "weapon_mace_root"]),
    ("Might", ["attack_damage", "armor", "toughness", "knockback", "sword_damage", "axe_damage", "mace_damage"],
     [("Brute Force", ["attack_damage", "knockback"]), ("Iron Skin", ["armor", "toughness"]),
      ("Weapon Master", ["sword_damage", "axe_damage", "mace_damage"])],
     ["iron_will"], ["weapon_claymore_root", "weapon_hammer_root"]),
    ("Finesse", ["crit_chance", "crit_damage", "dodge", "attack_speed", "move_speed", "armor_pierce", "armor_shred"],
     [("Precision", ["crit_chance", "crit_damage"]), ("Evasion", ["dodge", "move_speed"]),
      ("Exposing Strikes", ["armor_pierce", "armor_shred", "attack_speed"])],
     ["duelist"], ["weapon_sword_root", "weapon_dagger_root"]),
    ("Marksman", ["projectile_damage", "ranged_damage", "draw_speed", "arrow_velocity", "crit_chance"],
     [("Steady Aim", ["projectile_damage", "arrow_velocity"]), ("Quick Draw", ["draw_speed", "ranged_damage"]),
      ("Sniper", ["projectile_damage", "crit_damage"])],
     ["deadeye"], ["weapon_bow_root", "weapon_crossbow_root"]),
    ("Wilds", ["tamed_damage", "tamed_resistance", "mount_speed", "stealth", "fall_safety", "jump", "trident_damage"],
     [("Beastmaster", ["tamed_damage", "tamed_resistance"]), ("Ranger's Stride", ["mount_speed", "jump", "fall_safety"]),
      ("Shadow", ["stealth", "move_speed"])],
     ["pack_leader"], ["weapon_spear_root", "weapon_sickle_root"]),
    ("Arcana", ["spell_arcane", "spell_haste", "cooldown", "magic_resistance", "spell_all", "max_mana", "mana_regen"],
     [("Arcane Focus", ["spell_arcane", "spell_all"]), ("Quickening", ["spell_haste", "cooldown", "mana_regen"]),
      ("Warding", ["magic_resistance", "max_mana"])],
     ["spellblade"], ["weapon_arcane_root", "weapon_glaive_root"]),
]

# Max mana added to each "_boost" skill of these class branches (gameoverse-mana, 2026-09-30).
CLASS_BOOST_MANA = {"fire": 10, "frost": 10, "arcane": 10, "priest": 10, "paladin": 5}

CRAFT_STATS = ["fortune", "pickaxe_speed", "axe_speed", "shovel_speed", "mining_efficiency", "repair_cost",
               "xp_gained", "luck"]
CRAFT_NOTABLES = [("Deep Veins", ["fortune", "pickaxe_speed"]), ("Lumberjack", ["axe_speed", "mining_efficiency"]),
                  ("Tinkerer", ["repair_cost", "xp_gained"]), ("Fortune's Favor", ["luck", "fortune"])]
RIM_STATS = ["attack_damage", "spell_all", "armor", "crit_chance", "resistance", "projectile_damage"]


def rewards_for(stats, notable=False):
    out = []
    for s in stats:
        attr, op, small, big, _, _, _ = STATS[s]
        out.append(attribute(attr, big if notable else small, op))
    return out


def attribute(attr, value, op):
    return {"type": "puffish_skills:attribute", "data": {"attribute": attr, "value": round(value, 6), "operation": op}}


def fmt(stat, notable=False, value=None):
    attr, op, small, big, disp, name, _ = STATS[stat]
    v = value if value is not None else (big if notable else small)
    sign = "+" if v >= 0 else "-"
    if disp == "pct":
        num = abs(v) * 100
        return f"{sign}{num:g}% {name}"
    return f"{sign}{abs(v):g} {name}"


# --- keystones --------------------------------------------------------------------------------------------------------
# id: (title, description lines, rewards, icon)

def tag(name):
    return {"type": "puffish_skills:tag", "data": {"tag": "gameoverse." + name}}


KEYSTONES = {
    "glass_cannon": ("Glass Cannon", ["+40% Attack Damage", "+40% Spell Power", "You take 25% more damage"],
                     [attribute("minecraft:attack_damage", 0.4, MB), attribute("spell_power:generic", 0.4, MB),
                      attribute("puffish_attributes:resistance", -0.25, MB)], "minecraft:tnt"),
    "unshakeable": ("Unshakeable", ["You can't dodge", "+25% Armor", "+15% Damage Resistance"],
                    [attribute("apothic_attributes:dodge_chance", -1, ADD), attribute("minecraft:armor", 0.25, MB),
                     attribute("puffish_attributes:resistance", 0.15, MB)], "minecraft:obsidian"),
    "deadeye": ("Deadeye", ["Your attacks never crit (spells still use Spell Crit)", "Every hit deals 35% more damage"], [tag("deadeye")],
                "minecraft:target"),
    "bloodthirst": ("Bloodthirst", ["Life Steal heals twice as much", "All other healing is halved"],
                    [tag("bloodthirst")], "minecraft:redstone_block"),
    "lifeweaver": ("Lifeweaver", ["Life Steal works on every kind of damage: arrows, spells, fire", "You take 20% more damage"],
                   [tag("lifeweaver"), attribute("puffish_attributes:resistance", -0.2, MB)], "minecraft:crimson_roots"),
    "iron_will": ("Iron Will", ["You can't be knocked back", "-15% Movement Speed"],
                  [attribute("minecraft:knockback_resistance", 1, ADD), attribute("minecraft:movement_speed", -0.15, MB)],
                  "minecraft:anvil"),
    "pack_leader": ("Pack Leader", ["Pets deal 60% more damage and take 30% less", "-15% Attack Damage"],
                    [attribute("puffish_attributes:tamed_damage", 0.6, MB),
                     attribute("puffish_attributes:tamed_resistance", 0.3, MB),
                     attribute("minecraft:attack_damage", -0.15, MB)], "minecraft:wolf_armor"),
    "prospector": ("Prospector", ["+1 Fortune", "+50% Block Breaking Speed", "-20% Attack Damage"],
                   [attribute("puffish_attributes:fortune", 1, ADD), attribute("minecraft:block_break_speed", 0.5, ADD),
                    attribute("minecraft:attack_damage", -0.2, MB)], "minecraft:diamond_pickaxe"),
    "anglers_luck": ("Angler's Luck", ["+3 Luck (better fishing treasure)", "-15% Attack Damage"],
                     [attribute("minecraft:luck", 3, ADD), attribute("minecraft:attack_damage", -0.15, MB)],
                     "minecraft:fishing_rod"),
    "spellblade": ("Spellblade", ["25% of your highest spell power adds to your melee hits"], [tag("spellblade")],
                   "minecraft:enchanted_book"),
    "duelist": ("Duelist", ["Off-hand swings deal 35% more damage", "You can't block with a shield"], [tag("duelist")],
                "minecraft:shield"),
}
KEYSTONE_RIVALS = [("glass_cannon", "unshakeable"), ("bloodthirst", "lifeweaver"), ("deadeye", "spellblade"),
                   ("prospector", "anglers_luck")]
KEYSTONE_SPENT = 40
RIM_SPENT = 80

# --- XP and points ----------------------------------------------------------------------------------------------------

CURVE = "23 * level + 60"
FISH_XP, CROP_XP, ORE_XP = "4", "0.5", "2"
TIER_POINTS = {"ascent": 3, "summit": 5, "pinnacle": 8}

# --- graph ------------------------------------------------------------------------------------------------------------


class Tree:
    def __init__(self):
        self.defs = {}
        self.skills = {}
        self.normal = set()
        self.exclusive = set()

    def define(self, did, d):
        if did in self.defs and self.defs[did] != d:
            raise SystemExit(f"definition {did} defined twice differently")
        self.defs[did] = d

    def add(self, sid, x, y, did, root=False):
        if sid in self.skills:
            raise SystemExit(f"skill {sid} added twice")
        self.skills[sid] = {"x": int(round(x)), "y": int(round(y)), "definition": did}
        if root:
            self.skills[sid]["root"] = True
        return sid

    def link(self, a, b, exclusive=False):
        if a == b:
            return
        (self.exclusive if exclusive else self.normal).add(tuple(sorted((a, b))))


def polar(r, deg):
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)


def text(s):
    return {"text": s}


# Icons: textures from the Gameoverse-Skill-Forest-Icons resource pack (built by the unpublished
# mod-dev/gameoverse-skill-forest-icons, art by Quintino Pixels); the last STATS field is only a fallback note.
ICON_DIR = "gameoverse_skill_forest:textures/gui/icons/"


def tex(name):
    return {"type": "texture", "data": {"texture": f"{ICON_DIR}{name}.png"}}


def small_def(tree, stat):
    did = "s_" + stat
    name = STATS[stat][5]
    tree.define(did, {
        "title": text(name),
        "description": text(fmt(stat)),
        "icon": tex(stat),
        "frame": "task",
        "rewards": rewards_for([stat]),
    })
    return did


def notable_def(tree, key, title, stats, icon=None):
    did = "n_" + key
    tree.define(did, {
        "title": text(title),
        "description": text("\n".join(fmt(s, True) for s in stats)),
        "icon": {"type": "item", "data": {"item": icon}} if icon else tex(stats[0]),
        "frame": "goal",
        "size": 1.25,
        "rewards": rewards_for(stats, True),
    })
    return did


def keystone_def(tree, key):
    title, lines, rewards, icon = KEYSTONES[key]
    did = "k_" + key
    rivals = [b if a == key else a for a, b in KEYSTONE_RIVALS if key in (a, b)]
    extra = [f"Keystone. Needs {KEYSTONE_SPENT} points spent in the forest."]
    if rivals:
        extra.append("Can't be taken together with " + ", ".join(KEYSTONES[r][0] for r in rivals) + ".")
    tree.define(did, {
        "title": text(title),
        "description": text("\n".join(lines)),
        "extra_description": text(" ".join(extra)),
        "icon": tex("keystone_" + key),
        "frame": "challenge",
        "size": 1.6,
        "required_spent_points": KEYSTONE_SPENT,
        "rewards": rewards,
    })
    return did


def with_resolvable_type(d):
    """Skill Tree writes its live descriptions as {"skill_definition_id": id} with no "type", which the text codec
    reads as an empty component: the descriptions never showed. With the type they resolve on the client."""
    desc = d.get("description")
    if isinstance(desc, dict) and "skill_definition_id" in desc and "type" not in desc:
        d = dict(d)
        d["description"] = {"type": "skill_tree_rpgs:resolvable", **desc}
    return d


# The class's spell pool tag; its book (a spell_engine:spell_book built from the tag, as the Spell Binding Table does, by
# the mod's /gameoverse_forest class_book command) is given once when its start is unlocked (the forest start is the class choice; the Spell Binding
# Table stays the place to bind spells into it). Pufferfish's plain "command" runs only on a real unlock action, never on
# login or reload; an Orb reset doesn't take the book back (books cost 1 level at the table anyway).
CLASS_BOOKS = {
    "fire": "wizards:spell_book/fire", "frost": "wizards:spell_book/frost", "arcane": "wizards:spell_book/arcane",
    "priest": "paladins:spell_book/priest", "paladin": "paladins:spell_book/paladin",
    "warrior": "rogues:spell_book/warrior", "rogue": "rogues:spell_book/rogue", "archer": "archers:spell_book/archer",
}


def book_pool_exists(pool):
    """The class's spell tag, which the Spell Binding Table (and our command) turns into its book."""
    ns, path = pool.split(":", 1)
    with jar(ns + "-fabric-*.jar") as z:
        return ("data/%s/tags/spell/%s.json" % (ns, path)) in z.namelist()


def class_book_reward(root_definition):
    cls = root_definition.split("_")[0]
    if cls not in CLASS_BOOKS:
        raise SystemExit(f"No spell book for class root {root_definition}")
    return {"type": "puffish_skills:command", "data": {"command": "gameoverse_forest class_book " + CLASS_BOOKS[cls]}}


def class_cores(tree):
    """Skill Tree's class tab, carried over in place. Returns {class: outermost spine skill id}."""
    with jar("skill_tree-fabric-*.jar") as z:
        base = "data/skill_tree_rpgs/puffish_skills/categories/class_skills/"
        skills, defs, conns = (read_json(z, base + f) for f in ("skills.json", "definitions.json", "connections.json"))
    roots = {s["definition"] for s in skills.values() if s.get("root")}
    for did, d in defs.items():
        d = {k: v for k, v in d.items() if k != "metadata"}
        mana = CLASS_BOOST_MANA.get(did.split("_")[0]) if did.endswith("_boost") else None
        if mana:
            d = dict(d, rewards=list(d.get("rewards", [])) + [attribute("manaattributes:max_mana", mana, ADD)])
        if did in roots:
            d = dict(d, rewards=list(d.get("rewards", [])) + [class_book_reward(did)])
        tree.define("c_" + did, with_resolvable_type(d))
    angles = {}
    for sid, s in skills.items():
        tree.add("c_" + sid, s["x"], s["y"], "c_" + s["definition"], root=s.get("root", False))
        if s.get("root"):
            angles[s["definition"].split("_")[0]] = math.degrees(math.atan2(s["y"], s["x"]))
    for kind in ("normal", "exclusive"):
        for a, b in conns[kind].get("bidirectional", []):
            tree.link("c_" + a, "c_" + b, kind == "exclusive")
        if conns[kind].get("unidirectional"):
            raise SystemExit("Skill Tree class tab has unidirectional links; handle them")
    tips = {}
    for cls, ang in angles.items():
        best = None
        for sid, s in skills.items():
            if not s["definition"].startswith(cls + "_") or not (s["definition"].endswith("_boost") or s.get("root")):
                continue
            r = math.hypot(s["x"], s["y"])
            if best is None or r > best[0]:
                best = (r, "c_" + sid)
        tips[cls] = best[1]
    if sorted(angles) != sorted(CLASSES):
        raise SystemExit(f"Skill Tree classes changed: {sorted(angles)}")
    return angles, tips


def weapon_parts():
    """Skill Tree's weapon tab: {root definition: (root def, [child defs], exclusive child pairs)} plus all defs."""
    with jar("skill_tree-fabric-*.jar") as z:
        base = "data/skill_tree_rpgs/puffish_skills/categories/weapon_skills/"
        skills, defs, conns = (read_json(z, base + f) for f in ("skills.json", "definitions.json", "connections.json"))
    by_def = {s["definition"]: sid for sid, s in skills.items()}
    adj = {}
    for a, b in conns["normal"].get("bidirectional", []):
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    parts = {}
    for sid, s in skills.items():
        if s.get("root"):
            children = [skills[c]["definition"] for c in adj.get(sid, [])]
            parts[s["definition"]] = children
    excl = {tuple(sorted((skills[a]["definition"], skills[b]["definition"])))
            for a, b in conns["exclusive"].get("bidirectional", [])}
    return parts, excl, defs, by_def


def build():
    tree = Tree()
    angles, tips = class_cores(tree)
    wparts, wexcl, wdefs, _ = weapon_parts()
    used_weapons = set()

    # Gateways: one past each branch tip, leading to both neighbouring regions.
    gateways = {}
    gate_def = notable_def(tree, "gateway", "Crossroads", ["attack_damage", "spell_all"], "minecraft:lodestone")
    for cls in CLASSES:
        x, y = polar(650, angles[cls])
        gateways[cls] = tree.add("g_" + cls, x, y, gate_def)
        tree.link(tips[cls], gateways[cls])

    ring_r = [720 + 64 * k for k in range(10)]
    region_edges = {}  # region index -> {"first": [...], "last": [...], "outer": [...]}
    keystone_nodes = {}
    for i, (name, stats, notables, keystones, weapons) in enumerate(REGIONS):
        left, right = CLASSES[i], CLASSES[(i + 1) % len(CLASSES)]
        a0 = angles[left]
        a1 = angles[right]
        if a1 < a0:
            a1 += 360
        mid = (a0 + a1) / 2
        half = 12.0
        small = [small_def(tree, s) for s in stats]
        ndefs = [notable_def(tree, f"{name.lower()}_{j}", t, ss) for j, (t, ss) in enumerate(notables)]
        rings = []
        counter = 0
        for k, r in enumerate(ring_r):
            n = max(3, round(r * math.radians(2 * half) / 80) + 1)
            row = []
            for j in range(n):
                ang = mid - half + 2 * half * j / (n - 1)
                x, y = polar(r, ang)
                did = small[counter % len(small)]
                counter += 1
                if k == 3 and j == n // 2:
                    did = ndefs[0]
                elif k == 6 and j in (1, n - 2):
                    did = ndefs[1] if j == 1 else ndefs[2]
                elif k == 9 and j == n // 2:
                    did = ndefs[0]
                row.append((tree.add(f"r{i}_{k}_{j}", x, y, did), ang))
            rings.append(row)
        # radial links: every node to the nearest on the next ring, and every next-ring node to its nearest inward
        for k in range(len(rings) - 1):
            for sid, ang in rings[k]:
                nxt = min(rings[k + 1], key=lambda t: abs(t[1] - ang))
                tree.link(sid, nxt[0])
            for sid, ang in rings[k + 1]:
                prv = min(rings[k], key=lambda t: abs(t[1] - ang))
                tree.link(sid, prv[0])
        # lateral links on some rings
        for k in (0, 2, 5, 8):
            for j in range(len(rings[k]) - 1):
                tree.link(rings[k][j][0], rings[k][j + 1][0])
        tree.link(gateways[left], rings[0][0][0])
        tree.link(gateways[right], rings[0][-1][0])
        # keystones past the outer ring
        for q, key in enumerate(keystones):
            ang = mid if len(keystones) == 1 else mid + (-5 if q == 0 else 5)
            x, y = polar(ring_r[-1] + 72, ang)
            ks = tree.add("k_" + key, x, y, keystone_def(tree, key))
            nearest = min(rings[-1], key=lambda t: abs(t[1] - ang))
            tree.link(ks, nearest[0])
            keystone_nodes[key] = ks
        # weapon clusters in the inner lane
        for q, wroot in enumerate(weapons):
            if wroot not in wparts:
                raise SystemExit(f"Skill Tree weapon tab has no {wroot}")
            used_weapons.add(wroot)
            side = -1 if q == 0 else 1
            tree.define("w_" + wroot, with_resolvable_type({k: v for k, v in wdefs[wroot].items() if k != "metadata"}))
            rx, ry = polar(600, mid + side * 6)
            wr = tree.add("w_" + wroot, rx, ry, "w_" + wroot)
            inner = min(rings[0], key=lambda t: abs(t[1] - (mid + side * 6)))
            tree.link(wr, inner[0])
            kids = []
            for c, child in enumerate(sorted(wparts[wroot])):
                tree.define("w_" + child, with_resolvable_type({k: v for k, v in wdefs[child].items() if k != "metadata"}))
                cx, cy = polar(525, mid + side * (3 + 6 * c))
                kids.append(tree.add("w_" + child, cx, cy, "w_" + child))
                tree.link(wr, kids[-1])
            for a, b in wexcl:
                if a in wparts[wroot] and b in wparts[wroot]:
                    tree.link("w_" + a, "w_" + b, exclusive=True)
        region_edges[i] = {"first": rings, "mid": mid}

    # convergence notables where neighbouring regions meet, on each class line at ring 6
    conv_def = notable_def(tree, "convergence", "Confluence", ["attack_damage", "spell_all", "resistance"], "minecraft:beacon")
    tree.defs[conv_def]["required_skills"] = 2
    tree.defs[conv_def]["extra_description"] = text("Needs two connected skills unlocked.")
    for i in range(len(REGIONS)):
        cls = CLASSES[(i + 1) % len(CLASSES)]
        x, y = polar(ring_r[6], angles[cls])
        cv = tree.add("cv_" + cls, x, y, conv_def)
        tree.link(cv, region_edges[i]["first"][6][-1][0])
        tree.link(cv, region_edges[(i + 1) % len(REGIONS)]["first"][6][0][0])

    # Craft: two full rings
    craft_small = [small_def(tree, s) for s in CRAFT_STATS]
    craft_notables = [notable_def(tree, f"craft_{j}", t, ss) for j, (t, ss) in enumerate(CRAFT_NOTABLES)]
    craft = []
    counter = 0
    for q, r in enumerate((1440, 1510)):
        row = []
        for j in range(72):
            ang = -90 + 5 * j + (2.5 if q else 0)
            did = craft_small[counter % len(craft_small)]
            counter += 1
            if q == 1 and j % 6 == 3:
                did = craft_notables[(j // 6) % len(craft_notables)]
            x, y = polar(r, ang)
            row.append((tree.add(f"cr{q}_{j}", x, y, did), ang))
        craft.append(row)
    for row in craft:
        for j in range(len(row)):
            tree.link(row[j][0], row[(j + 1) % len(row)][0])
    for j in range(0, 72, 3):
        tree.link(craft[0][j][0], craft[1][j][0])

    def nearest_on(row, ang):
        return min(row, key=lambda t: abs((t[1] - ang + 180) % 360 - 180))[0]

    for i in range(len(REGIONS)):
        rows = region_edges[i]["first"]
        for sid, ang in (rows[-1][0], rows[-1][-1]):
            tree.link(sid, nearest_on(craft[0], ang))
    for key, ang in (("prospector", -45), ("anglers_luck", 135)):
        x, y = polar(1590, ang)
        ks = tree.add("k_" + key, x, y, keystone_def(tree, key))
        tree.link(ks, nearest_on(craft[1], ang))
        keystone_nodes[key] = ks
    for a, b in KEYSTONE_RIVALS:
        tree.link(keystone_nodes[a], keystone_nodes[b], exclusive=True)

    # Endless Rim
    rim_defs = []
    for s in RIM_STATS:
        did = "rim_" + s
        tree.define(did, {
            "title": text("Endless Rim"),
            "description": text(fmt(s)),
            "extra_description": text(f"Needs {RIM_SPENT} points spent in the forest."),
            "icon": tex(s),
            "frame": "task",
            "required_spent_points": RIM_SPENT,
            "rewards": rewards_for([s]),
        })
        rim_defs.append(did)
    rim = []
    for j in range(120):
        ang = -90 + 3 * j
        x, y = polar(1680, ang)
        rim.append((tree.add(f"rim_{j}", x, y, rim_defs[j % len(rim_defs)]), ang))
    for j in range(len(rim)):
        tree.link(rim[j][0], rim[(j + 1) % len(rim)][0])
    for ang in range(-90 + 22, 270, 45):
        tree.link(nearest_on(rim, ang), nearest_on(craft[1], ang))

    missing = set(wparts) - used_weapons
    if missing:
        raise SystemExit(f"weapon clusters not placed: {sorted(missing)}")
    return tree


# --- validation -------------------------------------------------------------------------------------------------------


def validate(tree, attrs, spells):
    for sid, s in tree.skills.items():
        if s["definition"] not in tree.defs:
            raise SystemExit(f"{sid}: unknown definition {s['definition']}")
    for a, b in tree.normal | tree.exclusive:
        if a not in tree.skills or b not in tree.skills:
            raise SystemExit(f"link to a missing skill: {a} - {b}")
    icons = os.path.join(ROOT, "..", "gameoverse-skill-forest-icons", "resourcepack")
    if not os.path.isdir(icons):
        print("note: gameoverse-skill-forest-icons not built here, icon textures not checked")
    for did, d in tree.defs.items():
        for key in ("title", "icon"):
            if key not in d:
                raise SystemExit(f"{did}: no {key}")
        t = d["icon"]["data"].get("texture", "")
        if t.startswith(ICON_DIR) and os.path.isdir(icons):
            ns, path = t.split(":", 1)
            if not os.path.isfile(os.path.join(icons, "assets", ns, path)):
                raise SystemExit(f"{did}: icon {t} is not in the icons resource pack")
        for rw in d.get("rewards", []):
            t, data = rw["type"], rw.get("data", {})
            if t in ("puffish_skills:attribute", "skill_tree_rpgs:conditional_attribute"):
                if data["attribute"] not in attrs:
                    raise SystemExit(f"{did}: unknown attribute {data['attribute']}")
                if data["operation"] not in (ADD, MB, MT):
                    raise SystemExit(f"{did}: bad operation {data['operation']}")
            elif t == "skill_tree_rpgs:spell":
                for c in data["containers"]:
                    for sp in c["spell_ids"]:
                        if sp not in spells:
                            raise SystemExit(f"{did}: unknown spell {sp}")
            elif t == "puffish_skills:command":
                cmd = data.get("command", "")
                if not cmd.startswith("gameoverse_forest class_book ") or not book_pool_exists(cmd.split()[-1]):
                    raise SystemExit(f"{did}: bad command reward {cmd!r}")
            elif t not in ("puffish_skills:tag",):
                raise SystemExit(f"{did}: unexpected reward type {t}")
    # every skill reachable from a root through normal links
    adj = {}
    for a, b in tree.normal:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    seen = {sid for sid, s in tree.skills.items() if s.get("root")}
    todo = list(seen)
    while todo:
        n = todo.pop()
        for m in adj.get(n, ()):
            if m not in seen:
                seen.add(m)
                todo.append(m)
    unreached = set(tree.skills) - seen
    if unreached:
        raise SystemExit(f"{len(unreached)} skills unreachable, e.g. {sorted(unreached)[:5]}")
    unused = set(tree.defs) - {s["definition"] for s in tree.skills.values()}
    for did in unused:
        del tree.defs[did]


def spell_ids():
    """Every Spell Engine spell in the installed jars (data/<ns>/spell/**.json)."""
    ids = set()
    for path in glob.glob(os.path.join(MODS, "*.jar")):
        try:
            z = zipfile.ZipFile(path)
        except zipfile.BadZipFile:
            continue
        with z:
            for n in z.namelist():
                parts = n.split("/")
                if len(parts) >= 4 and parts[0] == "data" and parts[2] == "spell" and n.endswith(".json"):
                    ids.add(parts[1] + ":" + "/".join(parts[3:])[:-5])
    return ids


# --- output -----------------------------------------------------------------------------------------------------------


def write(path, obj):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, indent=1)
            f.write("\n")


def experience():
    with jar("skill_tree-fabric-*.jar") as z:
        exp = read_json(z, "data/skill_tree_rpgs/puffish_skills/categories/class_skills/experience.json")
    kills = [s for s in exp["sources"] if s["type"] == "puffish_skills:kill_entity"]
    if len(kills) != 1:
        raise SystemExit("Skill Tree's kill XP source changed")

    def mine(test, xp, state=None):
        data = {"block": test}
        if state:
            data["state"] = state
        return {
            "type": "puffish_skills:mine_block",
            "data": {
                "variables": {"match": {"operations": [{"type": "get_mined_block_state"},
                                                       {"type": "puffish_skills:test", "data": data}]}},
                "experience": [{"condition": "match", "expression": xp}],
            },
        }

    return {
        "experience_per_level": {"type": "expression", "data": {"expression": CURVE}},
        "sources": [kills[0],
                    {"type": "puffish_skills:fish_item", "data": {"experience": FISH_XP}},
                    mine("#minecraft:crops", CROP_XP, {"age": "7"}),
                    mine("#c:ores", ORE_XP)],
    }


def points_table():
    total, rows = 0, []
    for level in range(0, 400):
        total += 23 * level + 60
        if level + 1 in (10, 25, 50, 100, 150, 200, 300, 400):
            rows.append((level + 1, round(total)))
    return rows


def main():
    tree = build()
    validate(tree, known_attributes(), spell_ids())
    shutil.rmtree(OUT, ignore_errors=True)
    write("pack.mcmeta", {"pack": {
        "description": "Gameoverse Skill Forest: one huge skill tree replacing Skill Tree's class and weapon tabs.",
        "pack_format": 101, "min_format": [101, 0], "max_format": [101, 1]}})
    write("data/gameoverse/puffish_skills/config.json", {"version": 3, "categories": ["forest"]})
    write("data/skill_tree_rpgs/puffish_skills/config.json", {"version": 3, "categories": []})
    write(CAT_DIR + "/category.json", {
        "title": text("Skill Forest"),
        "icon": tex("tab"),
        "background": {"texture": "skill_tree_rpgs:textures/gui/background_6_b.png", "width": 768, "height": 463,
                       "position": "fill"},
        "unlocked_by_default": True,
        "exclusive_root": True,
    })
    write(CAT_DIR + "/definitions.json", tree.defs)
    write(CAT_DIR + "/skills.json", tree.skills)
    write(CAT_DIR + "/connections.json", {
        "normal": {"bidirectional": sorted(list(p) for p in tree.normal)},
        "exclusive": {"bidirectional": sorted(list(p) for p in tree.exclusive)},
    })
    write(CAT_DIR + "/experience.json", experience())
    # Orb of Oblivion: a mid-game recipe
    write("data/skill_tree_rpgs/recipe/orb_of_oblivion.json", {
        "type": "minecraft:crafting_shaped", "category": "equipment",
        "key": {"C": "minecraft:diamond_block", "G": "apotheosis:gem_dust", "X": "minecraft:experience_bottle"},
        "pattern": ["GXG", "XCX", " X "],
        "result": {"id": "skill_tree_rpgs:orb_of_oblivion"},
    })
    # World Tier bonus points, one source per tier so a repeat can't stack
    for tier, pts in TIER_POINTS.items():
        write(f"data/gameoverse/function/forest/world_tier/{tier}.mcfunction",
              f"puffish_skills points set @s {CATEGORY} {pts} gameoverse:world_tier_{tier}\n")
    kinds = {}
    for s in tree.skills.values():
        d = s["definition"]
        k = d.split("_")[0]
        kinds[k] = kinds.get(k, 0) + 1
    print(f"wrote {len(tree.skills)} skills, {len(tree.defs)} definitions, "
          f"{len(tree.normal)} links, {len(tree.exclusive)} exclusive links")
    print("by kind:", kinds)
    print("cumulative XP to reach N points:", points_table())


if __name__ == "__main__":
    main()
