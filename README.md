# Gameoverse Skill Forest

One huge Pufferfish's Skills tab (`gameoverse:forest`, ~1,060 skills) replacing Skill Tree's Class and Weapon tabs.
Design and decisions: `docs/skill-forest-design.md` (server repo). Player-facing: the Guide's Skill Forest page.

- `tools/generate.py` builds `datapack/` (deployed as `world/datapacks/gameoverse_skill_forest/`, replace, don't
  merge): the tab (Skill Tree's class branches in place at the centre as the exclusive starts, a gateway past each tip,
  8 region lattices between the classes with notables, keystones and Skill Tree's weapon clusters, the Craft ring,
  the Endless Rim), its XP (Skill Tree's kill formula, fishing, mature crops, ores; `23 * level + 60` per point), an
  override turning Skill Tree's own tabs off, the Orb of Oblivion recipe, and the World Tier bonus-point functions
  (called from gameoverse_farming_path's tier advancements). It validates everything first: one bad value makes
  Pufferfish's Skills load no tabs at all. Re-run after Skill Tree, Apotheosis, Pufferfish's Attributes or spell mods
  update.
- The Fabric mod (`src/`, server-only) holds the keystones that change rules (Deadeye, Spellblade, Bloodthirst,
  Lifeweaver, Duelist; checked by entity tags the tab grants) and adds the forest to the Orb of Oblivion's resets.
- Skill Tree (All Rights Reserved) stays installed for its reward types, spells and effects; the generator reads its
  data from the installed jar at build time. The generated `datapack/` contains that data, so it isn't tracked here:
  run the generator to build it.

Needs: Pufferfish's Skills, Skill Tree, Apothic Attributes (Fabric port) 3.0.1-fabric.5+, gameoverse-attribute-bridge
1.1.0+, Better Combat, Spell Power, Pufferfish's Attributes. Keep the tab on Dynamic Difficulty's
`puffishSkillsTreeBlacklist`.

MIT licensed (our code and generator).
