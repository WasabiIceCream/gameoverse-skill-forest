package net.gameoverse.skillforest;

import java.util.function.Predicate;

/**
 * Moves one item from an equipment slot into a table slot when a menu opens, and back when it closes if it is still the
 * same item there and the equipment slot is still free. Free of Minecraft types so the rules can be unit-tested; the
 * Spell Binding Table wiring is in {@link TableBook}.
 *
 * <p>Nothing is ever in two places: the item leaves the equipment slot before it enters the table, and leaves the table
 * before it goes back. "The same item" is object identity: taking the item out of the table slot splits it into a new
 * stack, so a book the player took out (or swapped for another) is no longer "the same" and gets the menu's normal
 * return-to-inventory handling.
 */
public final class BookShuttle<S> {

    /** One slot the shuttle reads and writes. */
    public interface Place<S> {
        S get();

        /** Puts {@code stack} (or the empty value) in the slot; false if the slot refused. */
        boolean set(S stack);

        /** Whether this slot would take {@code stack}. */
        boolean accepts(S stack);

        /** Whether {@code stack} may leave this slot now (for a spell book: not while one of its spells is on cooldown). */
        boolean canTake(S stack);
    }

    private final Predicate<S> isEmpty;
    private final S empty;
    private S moved;
    private Place<S> from;

    public BookShuttle(Predicate<S> isEmpty, S empty) {
        this.isEmpty = isEmpty;
        this.empty = empty;
    }

    /** Moves the item from {@code from} into {@code table} if the table slot is empty and both slots allow it. */
    public boolean pull(Place<S> from, Place<S> table) {
        if (moved != null || !isEmpty.test(table.get())) return false;
        S stack = from.get();
        if (stack == null || isEmpty.test(stack) || !table.accepts(stack) || !from.canTake(stack)) return false;
        if (!from.set(empty)) return false;
        if (!table.set(stack)) {
            from.set(stack);
            return false;
        }
        this.moved = stack;
        this.from = from;
        return true;
    }

    /**
     * On close: puts the pulled item back where it came from if it is still the same item in {@code table} and its old
     * slot is free and takes it. Returns false when the caller should use its normal handling for whatever is in the
     * table. {@code playerPresent} is false when the player is gone (disconnected after their data was saved).
     */
    public boolean restore(Place<S> table, boolean playerPresent) {
        S stack = moved;
        Place<S> target = from;
        moved = null;
        from = null;
        if (stack == null || !playerPresent) return false;
        S current = table.get();
        if (current != stack || isEmpty.test(current)) return false;
        if (!isEmpty.test(target.get()) || !target.accepts(current)) return false;
        if (!table.set(empty)) return false;
        if (!target.set(current)) {
            table.set(current);
            return false;
        }
        return true;
    }

    /** Whether an item pulled from equipment is waiting to go back. */
    public boolean holding() {
        return moved != null;
    }
}
