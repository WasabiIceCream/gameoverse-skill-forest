package net.gameoverse.skillforest;

import eu.pb4.trinkets.api.TrinketAttachment;
import eu.pb4.trinkets.api.TrinketInventory;
import eu.pb4.trinkets.api.TrinketSlotAccess;
import eu.pb4.trinkets.api.TrinketSlotUtils;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import eu.pb4.trinkets.api.TrinketsApi;

/**
 * The Spell Binding Table uses the equipped spell book: opening the table moves the book from the Trinkets
 * {@code spell/book} slot into the table's book slot (if the table accepts it and Trinkets lets it be unequipped, which
 * includes Spell Engine's "not while one of its spells is on cooldown" rule), and closing the table puts it back there
 * if it is still the same book and the slot is still free. Otherwise the table's own close handling applies (the book goes
 * to the inventory). Server side only: the table's inventory is a menu-only container, and its contents sync to the
 * client like any menu.
 */
public final class TableBook {

    /** Spell Engine's trinket slot for spell books (group "spell", slot "book"). */
    static final String SLOT_ID = "spell/book";
    /** The Spell Binding Table's book slot: the first slot its menu adds. */
    static final int TABLE_BOOK_SLOT = 0;

    private TableBook() {}

    /** Mixed into the Spell Binding Table's menu. */
    public interface Holder {
        void gameoverse$pullBook(ServerPlayer player);

        void gameoverse$restoreBook(ServerPlayer player, boolean playerPresent);
    }

    static void register() {
        // Disconnecting with the table open: the player's data is saved before the menu is closed (which would drop the
        // book on the ground), so put the book back first. Fabric fires DISCONNECT before the vanilla disconnect handling.
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            if (handler.player.containerMenu instanceof Holder holder) holder.gameoverse$restoreBook(handler.player, true);
        });
    }

    /** Whether the menu's close handling can still give items back to this player (same test as vanilla's). */
    public static boolean present(ServerPlayer player) {
        return !player.hasDisconnected() && (!player.isRemoved() || player.getRemovalReason() == Entity.RemovalReason.CHANGED_DIMENSION);
    }

    /** The first filled {@code spell/book} trinket slot, or null. */
    static BookShuttle.Place<ItemStack> equippedBook(ServerPlayer player) {
        TrinketAttachment attachment = TrinketsApi.getAttachment(player);
        if (attachment == null) return null;
        TrinketInventory inventory = attachment.getInventory(SLOT_ID);
        if (inventory == null) return null;
        for (int i = 0; i < inventory.getContainerSize(); i++) {
            TrinketSlotAccess access = inventory.getSlotAccess(i);
            if (access != null && !access.get().isEmpty()) return trinket(access);
        }
        return null;
    }

    static BookShuttle.Place<ItemStack> trinket(TrinketSlotAccess access) {
        return new BookShuttle.Place<>() {
            public ItemStack get() { return access.get(); }
            public boolean set(ItemStack stack) { return access.set(stack); }
            public boolean accepts(ItemStack stack) { return TrinketSlotUtils.mayPlace(access, stack); }
            public boolean canTake(ItemStack stack) { return TrinketSlotUtils.mayPickup(access, stack); }
        };
    }

    static BookShuttle.Place<ItemStack> table(AbstractContainerMenu menu) {
        Slot slot = menu.getSlot(TABLE_BOOK_SLOT);
        return new BookShuttle.Place<>() {
            public ItemStack get() { return slot.getItem(); }
            public boolean set(ItemStack stack) { slot.set(stack); return true; }
            public boolean accepts(ItemStack stack) { return slot.mayPlace(stack); }
            public boolean canTake(ItemStack stack) { return true; }
        };
    }

    public static void pull(BookShuttle<ItemStack> shuttle, AbstractContainerMenu menu, ServerPlayer player) {
        BookShuttle.Place<ItemStack> from = equippedBook(player);
        if (from != null) shuttle.pull(from, table(menu));
    }

    public static void restore(BookShuttle<ItemStack> shuttle, AbstractContainerMenu menu, boolean playerPresent) {
        if (shuttle.holding()) shuttle.restore(table(menu), playerPresent);
    }
}
