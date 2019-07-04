# -*- coding: utf-8 -*-
import yaml
import re
import requests
import functools
import gevent

from datetime import datetime, timedelta

from disco.types.message import MessageTable, MessageEmbed, MessageEmbedField, MessageEmbedThumbnail
from disco.api.http import APIException
from disco.bot import Bot, Plugin, CommandLevels
from disco.bot.command import CommandEvent
from disco.types.message import MessageEmbed
from disco.types.user import GameType, Status, Game
from disco.types.channel import ChannelType
from disco.util.sanitize import S

from GamesKeeper import NO_EMOJI_ID, YES_EMOJI_ID, NO_EMOJI, YES_EMOJI, bot_config
from GamesKeeper.models.guild import Guild
from GamesKeeper.models.games import Games, Users
from GamesKeeper.games.uno_justin import Uno

class UnoPlugin(Plugin):

    def load(self, ctx):
        super(UnoPlugin, self).load(ctx)
        self.games = {}
        self.game = 'uno'
    
    # @Plugin.command('test', level=-1, group='uno')
    # def cmd_testing(self, event):
    #     Uno(event, [event.author, event.author])

    @Plugin.listen('MessageReactionAdd')
    def on_message_reaction_add(self, event):

        if event.channel_id not in self.games:
            return
        game = self.games.get(event.channel_id, None)
        if game == None:
            return


        def delete_game_channel():
            gevent.sleep(10)
            for x in game.game_channels:
                x.delete()

        is_game_over = game.handle_turn(event)
        if is_game_over and game.winner == 'draw':
            self.games.pop(event.channel_id, None)
            game.start_event.channel.send_message('The game ended in a **draw** in the match of Connect 4 match between <@{}> and <@{}>.'.format(game.players[0], game.players[1]))
            gevent.spawn(delete_game_channel())
            return
        if is_game_over:
            def get_other():
                other = None
                for x in game.players:
                    if x == game.winner:
                        continue
                    else:
                        other = x
                        break
                return other
            self.games.pop(event.channel_id, None)
            game.start_event.channel.send_message('The winner is <@{}> in the match of Connect 4 match against <@{}>!'.format(game.winner, get_other()))
            gevent.spawn(delete_game_channel())
            return

    @Plugin.command('play', group='uno')
    def cmd_play(self, event):
        """
        This command allows you to start a game of uno!
        Usage: `uno play`
        """

        msg = event.channel.send_message("<@{author.id}> has started a game of uno. Click the reaction to join. The game will start in 30 seconds.".format(author=event.author))
        msg.add_reaction(YES_EMOJI)
        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                        e.emoji.id != YES_EMOJI_ID
                )).get(timeout=5)
        except gevent.Timeout:
            reactions = self.client.api.channels_messages_reactions_get(msg.channel.id, msg.id, YES_EMOJI)
            players = [event.author] + list(filter(lambda x: x.id != event.author.id and not x.bot, reactions))
            if len(players) < 1:
                msg.edit("Not enough players. Match canceled.")
                return
            if len(players) > 8:
                msg.edit("Maximum player limit reached. Try again with less players.")
                return
            msg.edit("Game starting. Please wait while we setup the game!")
            game_id = max(x.game_id for x in self.games) + 1 if len(self.games) > 0 else 1
            game = Uno(event, players, game_id, msg)
            for x in game.game_channels:
                self.games[x.id] = game

            # slash_shrug = "**{}** Vs **{}**".format(players[0], players[1])
            # msg.edit(
            #     "Game {lol} has started in channel <#{channel}>! Please enjoy the game, the end results will be shown in this channel once the game is over!".format(
            #         lol=slash_shrug, channel=game.game_channel.id))
            msg.delete_reaction(YES_EMOJI, self.state.me)

            return
    
    @Plugin.command('rules', group='uno')
    def cmd_list_rules(self, event):
        user_obj = Users.with_id(event.author.id)
        enabled_rules = user_obj.get_enabled()
        embed = MessageEmbed()
        embed.title = '{}\'s Uno Rules'.format(event.author)
        embed.description = 'Change a rule by typing `{prefix}uno <enable/disable> <rule #>`.\nExample: `{prefix}uno enable 2`'.format(prefix=event.db_guild.prefix)
        # embed.color = 0x11538982

        embed.add_field(
            name='{}:one: Jump In'.format('<{}>'.format(YES_EMOJI if Users.UnoRules.jump_in in enabled_rules else NO_EMOJI)),
            value='At any time, if you have the same card - color and number - as the card anyone plays, you can \"jump\" in by playing that card, and then the turn goes to the person after you.'
        )

        embed.add_field(
            name='{}:two: Stacking Draws'.format('<{}>'.format(YES_EMOJI if Users.UnoRules.stack_draws in enabled_rules else NO_EMOJI)),
            value='If someone plays a draw 2 on you, you can stack another draw 2 on it instead of drawing your cards and skipping your turn; the next person then has to draw 4 cards unless he or she also stacks. The same is true of Draw 4s - but you cannot mix and match Draw 4 and Draw 2 cards.'
        )

        embed.add_field(
            name='{}:three: 7-Swap'.format('<{}>'.format(YES_EMOJI if Users.UnoRules.seven_swap in enabled_rules else NO_EMOJI)),
            value='When playing a 7, you can choose to trade hands with another player.'
        )

        embed.add_field(
            name='{}:four: 0-Super Swap'.format('<{}>'.format(YES_EMOJI if Users.UnoRules.super_swap in enabled_rules else NO_EMOJI)),
            value='When playing a 0, all players must switch hands with the player a turn ahead of them.'
        )

        embed.add_field(
            name='{}:five: Cancel Skip'.format('<{}>'.format(YES_EMOJI if Users.UnoRules.cancel_skip in enabled_rules else NO_EMOJI)),
            value='If the player before you has plays a Skip, you can play another Skip and will skip the next player\'s turn.'
        )

        embed.add_field(
            name='{}:six: Special Multiplay'.format('<{}>'.format(YES_EMOJI if Users.UnoRules.special_multiplay in enabled_rules else NO_EMOJI)),
            value='You can place multiple Draw 2s, Draw 4s, Skips, and Reverses at one time and the effects will stack. For example, if you place 2 Skips down, it will skip 2 players. If you place 3 Draw 2s down, the next player will draw 6 cards.'
        )

        embed.add_field(
            name='{}:seven: Trains'.format('<{}>'.format(YES_EMOJI if Users.UnoRules.trains in enabled_rules else NO_EMOJI)),
            value='You can place multiple cards down if they are either one up, one down, or the same number as the previous card. For example, if you have the hand `Red1, Green2, Yellow3, Green4` and you place down the Yellow3, you can place down **in order** `Green2, Red1` or `Green4` on the same turn.'
        )

        embed.add_field(
            name='{}:eight: Endless Draw'.format('<{}>'.format(YES_EMOJI if Users.UnoRules.endless_draw in enabled_rules else NO_EMOJI)),
            value='If you are unable to play any cards, you must keep drawing cards until you can play.'
        )

        return event.msg.reply('', embed=embed)
    
    @Plugin.command('enable', '<rule:int>', group='uno', context={'mode': 'enable'})
    @Plugin.command('disable', '<rule:int>', group='uno', context={'mode': 'disable'})
    def cmd_change_rules(self, event, rule, mode):
        """
        This command is used to enable or disable Uno custom rules. 
        Usage: `uno enable/disable RuleNumber`
        """
        if 0 > rule > len(Users.UnoRules.num):
            return event.msg.reply('`Error:` Not a valid rule number.')
        user_obj = Users.with_id(event.author.id)
        if mode == 'enable':
            current_rules = user_obj.uno_rules
            rule_b = user_obj.int_to_type(rule)
            if current_rules & rule_b:
                return event.msg.reply('`Error:` This rule is already enabled.')
            else:
                user_obj.uno_rules = current_rules + rule_b
                user_obj.save()
                return event.msg.reply('Rule **{}** has been enabled!'.format(rule))
        if mode == 'disable':
            current_rules = user_obj.uno_rules
            rule_b = user_obj.int_to_type(rule)
            if not current_rules & rule_b:
                return event.msg.reply('`Error:` This rule is already disabled.')
            else:
                user_obj.uno_rules = current_rules - rule_b
                user_obj.save()
                return event.msg.reply('Rule **{}** has been disabled!'.format(rule))
    
    @Plugin.command('enabled', group='uno')
    def cmd_get_enabled(self, event):
        
        enabled_rules = event.db_user.get_enabled_rules()

        embed = MessageEmbed()
        embed.title = '{}\'s Uno Rules'.format(event.author)
        description = [
            '__Rules Enabled__:'
        ]

        if len(enabled_rules) == 0:
            description.append('`None`')
            return event.msg.reply('', embed=embed)

        for x in enabled_rules:
            description.append('\♦ {}'.format(x))

        embed.description = '\n'.join(description)
        return event.msg.reply('', embed=embed)