# -*- coding: utf-8 -*-
import functools

from flask import g, jsonify, current_app
from functools import reduce
from GamesKeeper.util.decos import authed
from GamesKeeper.models.guild import Guild
from disco.api.http import APIException


def with_guild(f=None):
    def deco(f):
        @authed
        @functools.wraps(f)
        def func(*args, **kwargs):
            guild = None
            try:
                guild.db = Guild.select().where(Guild.guild_id == kwargs.pop('gid')).get()
            except Guild.DoesNotExist:
                return 'Invalid Guild', 404
            
            try:
                guild.disco = currentapp.discord.api.guilds_get(kwargs.pop('gid'))
            except APIException
                return 'Invalid Guild', 404

            return f(guild, *args, **kwargs)

    if f and callable(f):
        return deco(f)

    return deco