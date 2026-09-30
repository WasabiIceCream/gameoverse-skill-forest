package net.gameoverse.skillforest;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

/** The equipped-book shuttle's rules, with plain objects standing in for item stacks (identity matters, as for stacks). */
class BookShuttleTest {

    static final Object EMPTY = new Object() { public String toString() { return "EMPTY"; } };

    static final class Box implements BookShuttle.Place<Object> {
        Object item = EMPTY;
        boolean accepts = true;
        boolean canTake = true;

        Box(Object item) { this.item = item; }

        public Object get() { return item; }
        public boolean set(Object stack) { item = stack; return true; }
        public boolean accepts(Object stack) { return accepts; }
        public boolean canTake(Object stack) { return canTake; }
    }

    static BookShuttle<Object> shuttle() {
        return new BookShuttle<>(o -> o == EMPTY, EMPTY);
    }

    @Test
    void opensWithTheEquippedBookAndPutsItBackOnClose() {
        Object book = new Object();
        Box trinket = new Box(book), table = new Box(EMPTY);
        BookShuttle<Object> s = shuttle();
        assertTrue(s.pull(trinket, table));
        assertSame(EMPTY, trinket.item);
        assertSame(book, table.item);
        assertTrue(s.restore(table, true));
        assertSame(book, trinket.item);
        assertSame(EMPTY, table.item);
    }

    @Test
    void cooldownKeepsTheBookEquipped() {
        Object book = new Object();
        Box trinket = new Box(book), table = new Box(EMPTY);
        trinket.canTake = false;
        BookShuttle<Object> s = shuttle();
        assertFalse(s.pull(trinket, table));
        assertSame(book, trinket.item);
        assertSame(EMPTY, table.item);
        assertFalse(s.restore(table, true));
        assertSame(book, trinket.item);
    }

    @Test
    void doesNothingWhenTheTableAlreadyHasABookOrRefusesIt() {
        Object book = new Object(), other = new Object();
        Box trinket = new Box(book), table = new Box(other);
        assertFalse(shuttle().pull(trinket, table));
        assertSame(book, trinket.item);
        assertSame(other, table.item);

        Box refusing = new Box(EMPTY);
        refusing.accepts = false;
        assertFalse(shuttle().pull(trinket, refusing));
        assertSame(book, trinket.item);
        assertSame(EMPTY, refusing.item);
    }

    @Test
    void swappedBookUsesTheNormalCloseHandling() {
        Object book = new Object(), inserted = new Object();
        Box trinket = new Box(book), table = new Box(EMPTY);
        BookShuttle<Object> s = shuttle();
        assertTrue(s.pull(trinket, table));
        table.item = inserted; // player took the equipped book out and put another one in
        assertFalse(s.restore(table, true));
        assertSame(EMPTY, trinket.item);
        assertSame(inserted, table.item); // left for the menu to return to the inventory
    }

    @Test
    void takenOutAndPutBackIsANewStackSoItGoesToTheInventory() {
        Object book = new Object(), splitCopy = new Object();
        Box trinket = new Box(book), table = new Box(EMPTY);
        BookShuttle<Object> s = shuttle();
        assertTrue(s.pull(trinket, table));
        table.item = splitCopy; // taking a stack out of a slot splits it into a new stack
        assertFalse(s.restore(table, true));
        assertSame(splitCopy, table.item);
    }

    @Test
    void refilledTrinketSlotOrAbsentPlayerUsesTheNormalCloseHandling() {
        Object book = new Object(), otherEquipped = new Object();
        Box trinket = new Box(book), table = new Box(EMPTY);
        BookShuttle<Object> s = shuttle();
        assertTrue(s.pull(trinket, table));
        trinket.item = otherEquipped;
        assertFalse(s.restore(table, true));
        assertSame(otherEquipped, trinket.item);
        assertSame(book, table.item);

        Box trinket2 = new Box(book), table2 = new Box(EMPTY);
        BookShuttle<Object> s2 = shuttle();
        assertTrue(s2.pull(trinket2, table2));
        assertFalse(s2.restore(table2, false));
        assertSame(book, table2.item);
        assertSame(EMPTY, trinket2.item);
    }

    @Test
    void restoresOnlyOnce() {
        Object book = new Object();
        Box trinket = new Box(book), table = new Box(EMPTY);
        BookShuttle<Object> s = shuttle();
        assertTrue(s.pull(trinket, table));
        assertTrue(s.restore(table, true)); // e.g. on disconnect
        assertFalse(s.holding());
        assertFalse(s.restore(table, true)); // then again from the menu's close handling
        assertSame(book, trinket.item);
        assertSame(EMPTY, table.item);
    }
}
