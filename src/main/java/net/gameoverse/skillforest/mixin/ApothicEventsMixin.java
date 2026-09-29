package net.gameoverse.skillforest.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import com.llamalad7.mixinextras.injector.ModifyReturnValue;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;

import net.gameoverse.attributebridge.SpellDamage;
import net.gameoverse.skillforest.Keystones;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.spell_power.api.SpellPower;
import net.spell_power.api.SpellSchool;
import net.spell_power.api.SpellSchools;

/**
 * Keystones hooked into Apothic Attributes' damage handling:
 * <ul>
 * <li>Deadeye: no crit roll, and every hit deals 35% more.</li>
 * <li>Spellblade: a share of the highest magic spell power is added to direct melee hits (not spells).</li>
 * <li>Bloodthirst: life steal heals double (the other half is in {@link LivingEntityMixin}).</li>
 * </ul>
 */
@Mixin(targets = "dev.shadowsoffire.apothic_attributes.impl.AttributeEvents")
public class ApothicEventsMixin {

    @Inject(method = "apothCriticalStrike", at = @At("HEAD"), cancellable = true)
    private static void gameoverse$deadeyeNoCrit(LivingEntity target, DamageSource source, float amount, CallbackInfoReturnable<Float> cir) {
        if (Keystones.DEADEYE.has(source.getEntity())) cir.setReturnValue(amount);
    }

    @ModifyReturnValue(method = "onIncomingDamage", at = @At("RETURN"))
    private static float gameoverse$damageKeystones(float amount, LivingEntity target, DamageSource source, float original) {
        if (amount <= 0 || !(source.getEntity() instanceof Player player) || player == target) return amount;
        if (Keystones.DEADEYE.has(player)) amount *= 1 + Keystones.DEADEYE_BONUS;
        if (Keystones.SPELLBLADE.has(player) && source.getDirectEntity() == player && source.is(DamageTypes.PLAYER_ATTACK) && !SpellDamage.active()) {
            amount += Keystones.SPELLBLADE_SHARE * gameoverse$highestSpellPower(player);
        }
        return amount;
    }

    @Unique
    private static float gameoverse$highestSpellPower(Player player) {
        double best = 0;
        for (SpellSchool school : SpellSchools.all()) {
            if (school.archetype == SpellSchool.Archetype.MAGIC && school != SpellSchools.GENERIC) {
                best = Math.max(best, SpellPower.getSpellPower(school, player).baseValue());
            }
        }
        return (float) best;
    }

    @WrapOperation(method = "lifeStealOverheal", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/LivingEntity;heal(F)V"))
    private static void gameoverse$bloodthirst(LivingEntity attacker, float amount, Operation<Void> original) {
        Keystones.LIFE_STEAL_HEAL.set(true);
        try {
            original.call(attacker, Keystones.BLOODTHIRST.has(attacker) ? amount * 2 : amount);
        }
        finally {
            Keystones.LIFE_STEAL_HEAL.set(false);
        }
    }
}
