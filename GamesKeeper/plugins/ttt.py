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
from GamesKeeper.games.ttt import *

class TTTPlugin(Plugin):

    def load(self, ctx):
        super(TTTPlugin, self).load(ctx)
        self.games = {}
        self.game = 'ttt'
    
    @Plugin.command('play', '[user:user]', group='ttt')
    @Plugin.command('play', '[user:user]', group='tictactoe')
    def cmd_play(self, event, user=None):
        """
        Allows you to start a game of TTT.
        Usage: `ttt play [User#1234 or UserID]`
        """
        use_ai = False
        if not user:
            use_ai = True
