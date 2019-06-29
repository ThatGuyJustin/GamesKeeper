# -*- coding: utf-8 -*-
import yaml
import re
import requests
import functools
import gevent
import psutil
import os
import json

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

class DevPlugin(Plugin):
    global_plugin = True

    def load(self, ctx):
        super(DevPlugin, self).load(ctx)
    
    @Plugin.command('botstats', aliases=['bs', 'sys'], group='dev', level=-1)
    def cmd_systen_stats(self, event):
        embed = MessageEmbed()
        embed.title = "Bot Stats"
        description = [
            "**Total Servers**: {}".format(str(len(self.client.state.guilds))),
            "**Total Users**: {}".format(str(len(self.client.state.users))),
            "**Total Global Games Played**: {}".format(Games.select(Games).count()),
            "\n",
            "__**System Stats**__",
            "**CPU Usage**: {}".format(str(psutil.cpu_percent(interval=1))),
            "**Ram Usage**: {}".format(str(psutil.virtual_memory().percent))
        ]
        embed.description = '\n'.join(description)
        event.msg.reply('', embed=embed)
    
    @Plugin.command('repopulate', group='dev', level=-1)
    def dev_repopulate(self, event):
        msg = event.msg.reply('Are you sure that you want to repopulate the emoji list in your config?')
        msg.add_reaction(YES_EMOJI)
        msg.add_reaction(NO_EMOJI)

        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id = msg.id,
                conditional = lambda e: (
                    e.emoji.id in (NO_EMOJI_ID, YES_EMOJI_ID) and
                    e.user_id == event.author.id
                )).get(timeout=10)
        except gevent.Timeout:
            return

        if mra_event.emoji.id != YES_EMOJI_ID:
            return msg.edit(':ok_hand: Understood. Action Canceled.')
        else:
            msg.edit('Wonderful! Please hold while I yeet some emojis...')

        c4_names = ['Blank', 'Blue', 'BlueNoBorder', 'Red', 'RedNoBorder']

        hangman_emotes = {}
        c4_emotes = {}
        uno_emotes = {}
        ttt_emotes = {}

        server_one = self.state.guilds.get(bot_config.emoji_servers['IDs']['server_one'])
        server_two = self.state.guilds.get(bot_config.emoji_servers['IDs']['server_two'])

        for emoji in server_one.emojis.values():
            uno_emotes[emoji.name] = '{name}:{emoji_id}'.format(name=emoji.name, emoji_id=emoji.id)
        
        for emoji in server_two.emojis.values():
            name = emoji.name
            if name.startswith('Hangman'):
                hangman_emotes[name.replace('Hangman', '', -1)] = '{name}:{emoji_id}'.format(name=emoji.name, emoji_id=emoji.id)
            elif name.startswith('TicTacToe'):
                ttt_emotes[emoji.name] = '{name}:{emoji_id}'.format(name=emoji.name, emoji_id=emoji.id)
            elif name in c4_names:
                c4_emotes[emoji.name] = '{name}:{emoji_id}'.format(name=emoji.name, emoji_id=emoji.id)
            else:
                uno_emotes[emoji.name] = '{name}:{emoji_id}'.format(name=emoji.name, emoji_id=emoji.id)
        
        with open("config.yaml", 'r') as config:
            current_config = yaml.safe_load(config)
        
        current_config['uno_emojis'] = uno_emotes
        current_config['connect4_emotes'] = c4_emotes
        current_config['hangman_emotes'] = hangman_emotes
        current_config['ttt_emotes'] = ttt_emotes

        with open("config.yaml", 'w') as f:
            yaml.safe_dump(current_config, f)
        
        return msg.edit('Success! Your config has been updated with the latest assets!')

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

