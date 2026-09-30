package net.gameoverse.skillforest;

import com.mojang.brigadier.arguments.StringArgumentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.ItemStack;
import net.spell_engine.api.spell.Spell;
import net.spell_engine.api.spell.registry.SpellRegistry;
import net.spell_engine.item.SpellEngineItems;
import net.spell_engine.item.UniversalSpellBookItem;

/**
 * {@code /gameoverse_forest class_book <spell tag>}: gives the running player the class spell book for that spell pool,
 * built the same way the Spell Binding Table creates one ({@link UniversalSpellBookItem#applyFromTag}). The forest's class
 * starts run it as a Pufferfish command reward, so the start is the class choice.
 */
final class ClassBooks {

    private ClassBooks() {}

    static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registries, env) -> dispatcher.register(
            Commands.literal("gameoverse_forest").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .then(Commands.literal("class_book").then(Commands.argument("pool", StringArgumentType.greedyString())
                    .executes(c -> {
                        ServerPlayer player = c.getSource().getPlayerOrException();
                        Identifier pool = Identifier.parse(StringArgumentType.getString(c, "pool"));
                        ItemStack book = new ItemStack(SpellEngineItems.SPELL_BOOK.get());
                        if (!UniversalSpellBookItem.applyFromTag(book, TagKey.create(SpellRegistry.KEY, pool))) {
                            c.getSource().sendFailure(Component.literal("No spell book for pool " + pool));
                            return 0;
                        }
                        if (!player.getInventory().add(book)) {
                            player.drop(book, false);
                        }
                        return 1;
                    })))));
    }
}
