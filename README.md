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
- The Fabric mod (`src/`, server-only: install in the server's `mods/` only) holds the keystones that change rules (Deadeye, Spellblade, Bloodthirst,
  Lifeweaver, Duelist; checked by entity tags the tab grants) and adds the forest to the Orb of Oblivion's resets.
- The mod also changes the Spell Binding Table (1.2.0, both server side; clients need nothing):
  - **Library like Penchant's enchanting table** (`SpellLibrary`, `SpellBindingScreenHandlerMixin`): Spell Engine counts
    plain bookshelves in the vanilla ring (`EnchantingTableBlock.BOOKSHELF_OFFSETS`/`isValidBookShelf`) inside
    `SpellBindingScreenHandler.lambda$slotsChanged$0`, which only runs on the server (the client menu's
    ContainerLevelAccess is a no-op; offers and their powered flag reach the client in data slots). We wrap its
    `SpellBinding.offersFor(..., int shelves)` call and pass Penchant's `PenchantmentMenu.getBookCount(Level, BlockPos)`
    / 3 (regular bookshelf 3 books, chiseled bookshelf one per book, lectern with a book 1, anywhere in Penchant's
    7x4x7 area when its `bookshelfPlacement` is on). Tier 2/3/4 spells need 20/30/40 power = 7/14/18 shelves = 21/42/54
    books. Without Penchant, Spell Engine's own count stays. Recheck `getBookCount` and the `offersFor` call site with
    javap when Penchant or Spell Engine update.
  - **Uses the worn spell book** (`TableBook`, `BookShuttle`, `ServerPlayerMixin`): after `ServerPlayer.openMenu` opens
    the table, the book in the Trinkets `spell/book` slot moves into the table's book slot (only if the slot is empty,
    the table accepts it and `TrinketSlotUtils.mayPickup` allows it, which includes Spell Engine's no-unequip-on-cooldown
    rule). On close (`removed`, and on disconnect before the player is saved) it goes back to that slot if it is still
    the same stack (identity: taking it out of the slot splits it into a new one) and the slot is still free; anything
    else takes the table's normal return-to-inventory path. The table's container is menu-only, so nothing stays in
    the block. `BookShuttleTest` covers the rules (`./gradlew test`).
- Skill Tree (All Rights Reserved) stays installed for its reward types, spells and effects; the generator reads its
  data from the installed jar at build time. The generated `datapack/` contains that data, so it isn't tracked here:
  run the generator to build it.

Needs: Pufferfish's Skills, Skill Tree, Spell Engine, Trinkets (Updated), optional Penchant, Apothic Attributes (Fabric port) 3.0.1-fabric.5+, gameoverse-attribute-bridge
1.1.0+, Better Combat, Spell Power, Pufferfish's Attributes. Keep the tab on Dynamic Difficulty's
`puffishSkillsTreeBlacklist`.

MIT licensed (our code and generator).

## Icons (2026-10-01)

Stat, notable, keystone, Endless Rim and tab icons are textures (`gameoverse_skill_forest:textures/gui/icons/...`) from
the Gameoverse-Skill-Forest-Icons resource pack, built by the unpublished `mod-dev/gameoverse-skill-forest-icons` (third
party art, not in this repo). The generator checks every icon path against that pack when it's next to this project.
Skill Tree's class and weapon nodes keep Skill Tree's own icons.
