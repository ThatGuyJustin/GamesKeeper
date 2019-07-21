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
            "**CPU Usage**: {}%".format(str(psutil.cpu_percent(interval=1))),
            "**Ram Usage**: {}%".format(str(psutil.virtual_memory().percent))
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
    
    @Plugin.command('assets-reupload', group='dev', level=-1)
    def cmd_emojis(self, event):
        msg = event.msg.reply('Are you sure that you want to upload the assets list in the servers?')
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
        
        return event.msg.reply('Not finished yet!')
    
    @Plugin.command('getadmin', '<server:int>', group='dev', level=-1)
    def server_give_admin(self, event, server):
        server_one = self.state.guilds.get(bot_config.emoji_servers['IDs']['server_one'])
        server_two = self.state.guilds.get(bot_config.emoji_servers['IDs']['server_two'])

        if server == 1:
            try:
                server_one.get_member(event.author.id).add_role(bot_config.emoji_servers['admin_roles']['server_one'])
                return event.msg.add_reaction(YES_EMOJI)
            except:
                return event.msg.reply('I couldn\'t add the role to you. Please make sure you are in Server One.')
        elif server == 2:
            try:
                server_two.get_member(event.author.id).add_role(bot_config.emoji_servers['admin_roles']['server_two'])
                return event.msg.add_reaction(YES_EMOJI)
            except:
                return event.msg.reply('I couldn\'t add the role to you. Please make sure you are in Server Two.')
    
    @Plugin.command('testing', level=-1)
    def test_cmd(self, event):
        pass
        # EventListener.emit('EndC4', event)