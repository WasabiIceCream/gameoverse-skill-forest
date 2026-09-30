package net.gameoverse.skillforest.mixin;

import java.util.OptionalInt;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.gameoverse.skillforest.TableBook;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.MenuProvider;

/**
 * Once a Spell Binding Table's menu is open (after vanilla has made it the player's menu), move the equipped spell book
 * into it. Hooked here rather than in the menu's constructor so a menu that is built but never opened can't take the book.
 */
@Mixin(ServerPlayer.class)
public class ServerPlayerMixin {

    @Inject(method = "openMenu", at = @At("RETURN"))
    private void gameoverse$pullSpellBook(MenuProvider provider, CallbackInfoReturnable<OptionalInt> cir) {
        ServerPlayer self = (ServerPlayer) (Object) this;
        if (cir.getReturnValue().isPresent() && self.containerMenu instanceof TableBook.Holder holder) holder.gameoverse$pullBook(self);
    }
}
