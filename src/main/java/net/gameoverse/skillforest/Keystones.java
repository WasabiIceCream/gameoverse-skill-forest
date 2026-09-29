package net.gameoverse.skillforest;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;

/**
 * The Skill Forest's rule-changing keystones. Pufferfish's Skills gives the player an entity tag while the keystone is
 * unlocked (a {@code puffish_skills:tag} reward in the datapack); the hooks check it.
 */
public enum Keystones {
    DEADEYE("gameoverse.deadeye"),
    SPELLBLADE("gameoverse.spellblade"),
    BLOODTHIRST("gameoverse.bloodthirst"),
    LIFEWEAVER("gameoverse.lifeweaver"),
    DUELIST("gameoverse.duelist");

    /** Deadeye: every hit deals this much more; it never crits. */
    public static final float DEADEYE_BONUS = 0.35F;
    /** Spellblade: this share of the highest spell power is added to melee hits. */
    public static final float SPELLBLADE_SHARE = 0.25F;
    /** Duelist: off-hand swings deal this much more. */
    public static final float DUELIST_BONUS = 0.35F;

    /**
     * Set while Apothic's life steal (or Lifeweaver's) is healing, so Bloodthirst can halve every other heal.
     * Main-thread only, like attacks.
     */
    public static final ThreadLocal<Boolean> LIFE_STEAL_HEAL = ThreadLocal.withInitial(() -> false);

    private final String tag;

    Keystones(String tag) {
        this.tag = tag;
    }

    public boolean has(Entity entity) {
        return entity instanceof Player player && player.entityTags().contains(this.tag);
    }
}
