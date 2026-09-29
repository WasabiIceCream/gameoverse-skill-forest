package net.gameoverse.skillforest.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyVariable;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.gameoverse.skillforest.Keystones;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;

@Mixin(LivingEntity.class)
public class LivingEntityMixin {

    /**
     * Bloodthirst: every heal but life steal is halved.
     */
    @ModifyVariable(method = "heal", at = @At("HEAD"), argsOnly = true)
    private float gameoverse$bloodthirstHalves(float amount) {
        LivingEntity self = (LivingEntity) (Object) this;
        return Keystones.BLOODTHIRST.has(self) && !Keystones.LIFE_STEAL_HEAL.get() ? amount * 0.5F : amount;
    }

    /**
     * Duelist: no shield blocking.
     */
    @Inject(method = "getItemBlockingWith", at = @At("HEAD"), cancellable = true)
    private void gameoverse$duelistCantBlock(CallbackInfoReturnable<ItemStack> cir) {
        if (Keystones.DUELIST.has((LivingEntity) (Object) this)) cir.setReturnValue(null);
    }
}
