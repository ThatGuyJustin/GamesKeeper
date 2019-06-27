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

from GamesKeeper.models.guild import Guild

class StatsPlugin(Plugin):
    global_plugin = True

    def load(self, ctx):
        super(StatsPlugin, self).load(ctx)
    
    @Plugin.command('stats', '[user:user]', aliases=['userstats', 'mystats'])
    def cmd_stats(self, user=None):
        pass