package net.gameoverse.skillforest.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.llamalad7.mixinextras.sugar.Local;

import net.gameoverse.skillforest.BookShuttle;
import net.gameoverse.skillforest.SpellLibrary;
import net.gameoverse.skillforest.TableBook;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.spell_engine.spellbinding.SpellBinding;
import net.spell_engine.spellbinding.SpellBindingScreenHandler;

/**
 * The Spell Binding Table's menu. Two changes, both server side:
 * <ul>
 * <li>Its library is counted like Penchant's enchanting table ({@link SpellLibrary}). Spell Engine counts shelves in the
 * {@code slotsChanged} lambda run through the menu's ContainerLevelAccess (server only; the client's access is a no-op)
 * and syncs the resulting offers (powered or not) to the client in data slots.</li>
 * <li>It uses the equipped spell book ({@link TableBook}): pulled in when the menu opens (see ServerPlayerMixin), put
 * back when it closes.</li>
 * </ul>
 */
@Mixin(SpellBindingScreenHandler.class)
public class SpellBindingScreenHandlerMixin implements TableBook.Holder {

    @Unique
    private final BookShuttle<ItemStack> gameoverse$book = new BookShuttle<>(ItemStack::isEmpty, ItemStack.EMPTY);

    @WrapOperation(method = "lambda$slotsChanged$0", at = @At(value = "INVOKE",
        target = "Lnet/spell_engine/spellbinding/SpellBinding;offersFor(Lnet/minecraft/world/level/Level;ZLnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/item/ItemStack;I)Lnet/spell_engine/spellbinding/SpellBinding$OfferResult;"))
    private SpellBinding.OfferResult gameoverse$penchantLibrary(Level level, boolean creative, ItemStack book, ItemStack lapis,
            int shelves, Operation<SpellBinding.OfferResult> original, @Local(argsOnly = true) BlockPos pos) {
        return original.call(level, creative, book, lapis, SpellLibrary.shelves(level, pos, shelves));
    }

    /** Before the menu's normal close handling returns the table's items to the inventory. */
    @Inject(method = "removed", at = @At("HEAD"))
    private void gameoverse$returnBook(Player player, CallbackInfo ci) {
        if (player instanceof ServerPlayer serverPlayer) gameoverse$restoreBook(serverPlayer, TableBook.present(serverPlayer));
    }

    @Override
    public void gameoverse$pullBook(ServerPlayer player) {
        TableBook.pull(gameoverse$book, (AbstractContainerMenu) (Object) this, player);
    }

    @Override
    public void gameoverse$restoreBook(ServerPlayer player, boolean playerPresent) {
        TableBook.restore(gameoverse$book, (AbstractContainerMenu) (Object) this, playerPresent);
    }
}
