package net.gameoverse.skillforest;

import archives.tater.penchant.menu.PenchantmentMenu;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;

/**
 * The Spell Binding Table's "library" measured the way Penchant measures the enchanting table's: Penchant's book count
 * around the table ({@link PenchantmentMenu#getBookCount(Level, BlockPos)}: regular bookshelves 3 books, chiseled
 * bookshelves one per book, lecterns holding a book 1, anywhere in Penchant's lenient 7x4x7 area when its
 * {@code bookshelfPlacement} is on), divided by 3 so Spell Engine's plain-shelf thresholds (7/14/18) become 21/42/54 books.
 * Recheck that method (javap) when Penchant updates. Without Penchant, Spell Engine's own count stays.
 */
public final class SpellLibrary {

    public static final boolean PENCHANT = FabricLoader.getInstance().isModLoaded("penchant");
    public static final int BOOKS_PER_SHELF = 3;

    private SpellLibrary() {}

    /** Spell Engine's shelf count for the table at {@code pos}, or {@code fallback} (its own count) without Penchant. */
    public static int shelves(Level level, BlockPos pos, int fallback) {
        return PENCHANT ? Penchant.books(level, pos) / BOOKS_PER_SHELF : fallback;
    }

    /** Separate class so Penchant's classes are only loaded when Penchant is installed. */
    private static final class Penchant {
        static int books(Level level, BlockPos pos) {
            return PenchantmentMenu.getBookCount(level, pos);
        }
    }
}
