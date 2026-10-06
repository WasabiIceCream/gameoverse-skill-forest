"""Japanese for the Skill Forest's generated text. generate.py emits every text as a translate key with the English as
fallback and asks to_ja() for the Japanese; a string this can't translate fails the build, so new stats, notables or
keystone lines need an entry here. Stat names follow the names the attribute mods' own ja_jp files use."""
import re

STAT_NAMES = {
    "Anvil Repair Cost": "金床の修理コスト",
    "Arcane Spell Power": "秘術の呪文威力",
    "Armor": "防御力",
    "Armor Pierce": "アーマー貫通",
    "Armor Shred": "アーマー破壊",
    "Armor Toughness": "防具強度",
    "Arrow Velocity": "矢の速度",
    "Attack Damage": "攻撃力",
    "Attack Knockback": "ノックバック力",
    "Attack Speed": "攻撃速度",
    "Axe Damage": "斧のダメージ",
    "Axe Speed": "斧の採掘速度",
    "Block Breaking Speed": "ブロック破壊速度",
    "Cold Damage": "低温ダメージ",
    "Cooldown Reduction": "クールダウン短縮",
    "Crit Chance": "クリティカル率",
    "Crit Damage": "クリティカルダメージ",
    "Damage Reflection": "ダメージ反射",
    "Damage Resistance": "ダメージ耐性",
    "Dodge Chance": "回避率",
    "Draw Speed": "引き絞り速度",
    "Experience Gained": "経験値取得倍率",
    "Fire Damage": "火属性ダメージ",
    "Fire Spell Power": "炎の呪文威力",
    "Fortune": "幸運",
    "Frost Spell Power": "氷の呪文威力",
    "Healing Received": "回復効率",
    "Healing Spell Power": "回復の呪文威力",
    "Jump Strength": "跳躍力",
    "Life Steal": "ライフスティール",
    "Luck": "運",
    "Luck (better fishing treasure)": "運 (釣りのお宝が増える)",
    "Mace Damage": "メイスのダメージ",
    "Magic Damage Resistance": "魔法ダメージ耐性",
    "Mana Regeneration": "マナ回復",
    "Max Mana": "最大マナ",
    "Mining Efficiency": "採掘効率",
    "Mount Speed": "騎乗速度",
    "Movement Speed": "移動速度",
    "Overheal": "オーバーヒール",
    "Pet Damage": "ペットのダメージ",
    "Pet Damage Resistance": "ペットのダメージ耐性",
    "Pickaxe Speed": "ツルハシの採掘速度",
    "Projectile Damage": "飛び道具ダメージ",
    "Ranged Damage": "遠距離攻撃力",
    "Safe Fall Distance": "安全落下高度",
    "Shovel Speed": "シャベルの採掘速度",
    "Spell Haste": "呪文加速",
    "Spell Power": "呪文威力",
    "Stealth": "隠密",
    "Sword Damage": "剣のダメージ",
    "Trident Damage": "トライデントのダメージ",
}

# Titles (notables, keystones, regions, the tab) and whole description lines.
PHRASES = {
    "Skill Forest": "スキルの森",
    "Crossroads": "十字路",
    "Endless Rim": "果てなき縁",
    "Angler's Luck": "釣り人の幸運",
    "Arcane Focus": "秘術の集中",
    "Beastmaster": "獣使い",
    "Bloodthirst": "血の渇き",
    "Brute Force": "力任せ",
    "Bulwark": "防壁",
    "Confluence": "合流",
    "Deadeye": "百発百中",
    "Deep Veins": "深い鉱脈",
    "Duelist": "決闘者",
    "Elemental Mastery": "元素の極意",
    "Evasion": "回避",
    "Exposing Strikes": "暴く一撃",
    "Faith": "信仰",
    "Fortune's Favor": "幸運の女神",
    "Glass Cannon": "ガラスの大砲",
    "Iron Skin": "鉄の肌",
    "Iron Will": "鉄の意志",
    "Kindling": "焚きつけ",
    "Leech": "吸血",
    "Lifeweaver": "命を紡ぐ者",
    "Lumberjack": "木こり",
    "Pack Leader": "群れの長",
    "Precision": "精密",
    "Prospector": "探鉱者",
    "Quick Draw": "早撃ち",
    "Quickening": "加速",
    "Ranger's Stride": "レンジャーの歩み",
    "Rime": "霧氷",
    "Sanctuary": "聖域",
    "Second Wind": "再起",
    "Shadow": "影",
    "Sniper": "狙撃手",
    "Spellblade": "魔法剣士",
    "Steady Aim": "照準安定",
    "Thorns": "棘",
    "Tinkerer": "修理職人",
    "Unshakeable": "不動の構え",
    "Warding": "守護",
    "Weapon Master": "武器の達人",
    "25% of your highest spell power adds to your melee hits": "最も高い呪文威力の25%が近接攻撃に加わる",
    "All other healing is halved": "それ以外の回復量は半分になる",
    "Every hit deals 35% more damage": "すべての攻撃のダメージが35%増える",
    "Life Steal heals twice as much": "ライフスティールの回復量が2倍になる",
    "Life Steal works on every kind of damage: arrows, spells, fire": "ライフスティールがすべての種類のダメージに効く: 矢、呪文、炎",
    "Off-hand swings deal 35% more damage": "オフハンドの攻撃のダメージが35%増える",
    "Pets deal 60% more damage and take 30% less": "ペットの与えるダメージが60%増え、受けるダメージが30%減る",
    "You can't be knocked back": "ノックバックされなくなる",
    "You can't block with a shield": "盾で防御できなくなる",
    "You can't dodge": "回避できなくなる",
    "You take 20% more damage": "受けるダメージが20%増える",
    "You take 25% more damage": "受けるダメージが25%増える",
    "Your attacks never crit (spells still use Spell Crit)": "攻撃がクリティカルにならなくなる (呪文は呪文会心のまま)",
    "Needs two connected skills unlocked.": "つながった2つのスキルの習得が必要。",
}

STAT_LINE = re.compile(r"^([+-])([\d.]+)(%?) (.+)$")
NEEDS_SPENT = re.compile(r"^Needs (\d+) points spent in the forest\.$")
KEYSTONE = re.compile(r"^Keystone\. Needs (\d+) points spent in the forest\.(?: Can't be taken together with (.+)\.)?$")


def line_ja(line):
    if line in PHRASES:
        return PHRASES[line]
    m = STAT_LINE.match(line)
    if m and m.group(4) in STAT_NAMES:
        return f"{STAT_NAMES[m.group(4)]} {m.group(1)}{m.group(2)}{m.group(3)}"
    m = NEEDS_SPENT.match(line)
    if m:
        return f"森に{m.group(1)}ポイント使っている必要がある。"
    m = KEYSTONE.match(line)
    if m:
        s = f"キーストーン。森に{m.group(1)}ポイント使っている必要がある。"
        if m.group(2):
            s += f"「{line_ja(m.group(2))}」とは同時に取れない。"
        return s
    if line in STAT_NAMES:
        return STAT_NAMES[line]
    return None


def to_ja(s):
    lines = [line_ja(l) for l in s.split("\n")]
    if any(l is None for l in lines):
        raise SystemExit(f"no Japanese for {s!r}: add it to tools/ja_jp.py")
    return "\n".join(lines)
