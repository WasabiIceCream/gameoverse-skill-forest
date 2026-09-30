package net.gameoverse.skillforest;

import dev.shadowsoffire.apothic_attributes.api.ALObjects;
import dev.shadowsoffire.apothic_attributes.util.AttributesUtil;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.skill_tree_rpgs.utils.SkillHelper;

public class SkillForest implements ModInitializer {

    public static final Identifier CATEGORY = Identifier.fromNamespaceAndPath("gameoverse", "forest");

    @Override
    public void onInitialize() {
        // The Orb of Oblivion resets these categories (Skill Tree's own two are turned off by the datapack).
        SkillHelper.RESET_CATEGORIES.add(CATEGORY);
        ServerLivingEntityEvents.AFTER_DAMAGE.register(SkillForest::lifeweaver);
        ClassBooks.register();
    }

    /**
     * Lifeweaver: Life Steal also heals from the damage Apothic's life steal skips (anything but direct physical hits).
     */
    private static void lifeweaver(LivingEntity target, DamageSource source, float baseDamage, float damageTaken, boolean blocked) {
        if (blocked || damageTaken <= 0 || !(source.getEntity() instanceof ServerPlayer player) || player == target) return;
        if (!Keystones.LIFEWEAVER.has(player)) return;
        if (source.getDirectEntity() instanceof LivingEntity && AttributesUtil.isPhysicalDamage(source)) return; // Apothic's own
        double lifeSteal = player.getAttributeValue(ALObjects.Attributes.LIFE_STEAL);
        if (lifeSteal <= 0.001) return;
        Keystones.LIFE_STEAL_HEAL.set(true);
        try {
            player.heal((float) (damageTaken * lifeSteal));
        }
        finally {
            Keystones.LIFE_STEAL_HEAL.set(false);
        }
    }
}
