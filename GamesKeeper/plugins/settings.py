# -*- coding: utf-8 -*-
import yaml
import re
import requests
import functools

from datetime import datetime, timedelta

from disco.types.message import MessageTable, MessageEmbed, MessageEmbedField, MessageEmbedThumbnail
from disco.api.http import APIException
from disco.bot import Bot, Plugin, CommandLevels
from disco.bot.command import CommandEvent
from disco.types.message import MessageEmbed
from disco.types.user import GameType, Status, Game
from disco.types.channel import ChannelType
from disco.util.sanitize import S


class SettingsPlugin(Plugin):
    global_plugin = True

    def load(self, ctx):
        super(SettingsPlugin, self).load(ctx)
    

    @Plugin.command('settings', level=CommandLevels.ADMIN)
    def list_settings(self, event):
        #settings = Guilds.get(event.guild.id).get_settings()
        TMP_SETTINGS = Temp_Settings('!', ['Uno', 'Connect 4', 'Tic-Tac-Toe', 'Trivia', '2048 Rina Edition'], 591431442194497566, [591430764550160394, 592163609296109568])
        games_catergory = event.guild.channels.get(TMP_SETTINGS.game_catergory)
        spectator_roles = []
        if len(TMP_SETTINGS.spectator_roles) > 0:
            for x in TMP_SETTINGS.spectator_roles:
                spectator_roles.append('<@&{}>'.format(x))
        embed = MessageEmbed()
        embed.color = 0xFF0000
        embed.add_field(name='Prefix', value='{}'.format(TMP_SETTINGS.prefix), inline=True)
        embed.add_field(name='Games Catergory', value='{} (`{}`)'.format(games_catergory.name, games_catergory.id), inline=True)
        embed.add_field(name='Spectator Roles', value='{}'.format(', '.join(spectator_roles)))
        embed.add_field(name='Enabled Games', value='`{list}`'.format(list=' `, ` '.join(TMP_SETTINGS.games_enabled)))
        return event.msg.reply('', embed=embed)

class Temp_Settings:
    def __init__(self, prefix, games_enabled, game_catergory, spectator_roles):
        self.prefix = prefix
        self.games_enabled = games_enabled
        self.game_catergory = game_catergory
        self.spectator_roles = spectator_roles
