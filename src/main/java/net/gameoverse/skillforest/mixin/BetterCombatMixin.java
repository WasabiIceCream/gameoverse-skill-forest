package net.gameoverse.skillforest.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;

import com.llamalad7.mixinextras.injector.ModifyReturnValue;

import net.bettercombat.api.AttackHand;
import net.bettercombat.logic.PlayerAttackHelper;
import net.gameoverse.skillforest.Keystones;
import net.minecraft.world.entity.player.Player;

/**
 * Duelist: off-hand swings deal more damage (Better Combat's dual-wielding damage multiplier for that hand).
 */
@Mixin(PlayerAttackHelper.class)
public class BetterCombatMixin {

    @ModifyReturnValue(method = "getDualWieldingAttackDamageMultiplier", at = @At("RETURN"))
    private static float gameoverse$duelist(float multiplier, Player player, AttackHand hand) {
        return hand.isOffHand() && Keystones.DUELIST.has(player) ? multiplier * (1 + Keystones.DUELIST_BONUS) : multiplier;
    }
}
