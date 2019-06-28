# -*- coding: utf-8 -*-
import yaml
import re
import requests
import functools
import pprint
import os
import base64

from datetime import datetime, timedelta

from disco.types.permissions import Permissions
from disco.api.http import APIException
from disco.bot import Bot, Plugin, CommandLevels
from disco.bot.command import CommandEvent
from disco.types.message import MessageEmbed
from disco.types.user import GameType, Status, Game
from disco.types.channel import ChannelType
from disco.util.sanitize import S

from GamesKeeper.db import init_db
from GamesKeeper.models.guild import Guild
from GamesKeeper import bot_config, update_config

PY_CODE_BLOCK = '```py\n{}\n```'

TEMP_BOT_ADMINS = [
    104376018222972928,
    142721776458137600,
    248245568004947969,
    298516367311765505
]

def game_checker(string):
    games = { 
        'ttt': 'ttt',
        'hm': 'hm',
        'c4': 'c4',
        'uno': 'uno',
        '2048': '2048',
        'twentyfourtyeight': '2048',
        'connect 4': 'c4',
        'connect four': 'c4',
        'connectfour': 'c4',
        'connect4': 'c4',
        'hangman': 'hm',
        'hang man': 'hm',
        'tic-tac-toe': 'ttt',
        'tic tac toe': 'ttt',
    }
    name = games.get(string.lower(), None)
    return name

class CorePlugin(Plugin):
    def load(self, ctx):
        init_db()
        # self.bot.add_plugin = self.our_add_plugin
        self.guilds = ctx.get('guilds', {})
        super(CorePlugin, self).load(ctx)

    def cooldown_check(self, user):
        return False

    #Basic command handler
    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):

        if event.message.channel.type == ChannelType.DM:
            return

        event.bot_admin = event.message.author.id in TEMP_BOT_ADMINS
        event.user_level = 0

        has_admin = False

        new_setup = False
        guild = None

        if event.message.guild:
            try:
                guild = Guild.using_id(event.guild.id)
            except Guild.DoesNotExist:
                guild = self.fresh_start(event, event.guild.id)
                new_setup = True
            if len(event.message.member.roles) > 0:
                for x in event.message.member.roles:
                    role = event.message.guild.roles.get(x)
                    if role.permissions.can(Permissions.ADMINISTRATOR):
                        event.user_level = 100
                        has_admin = True
            if guild.referee_role:
                if not has_admin and guild.referee_role in event.message.member.roles:
                    event.user_level = 50

        if event.message.author.bot:
            return

        # Grab the list of commands
        commands = list(self.bot.get_commands_for_message(False, {}, guild.prefix, event.message))

        #Used for cmd cooldowns
        user_ignores_cooldowns = self.cooldown_check(event.message.author.id)

        #Sorry, nothing to see here :C
        if not len(commands):
            return

        for command, match in commands:

            required_level = 0
            cooldown = 0

            if hasattr(command.plugin, 'game'):
                if not guild.check_if_listed(game_checker(command.plugin.game), 'enabled'):
                    return

            if command.level == -1 and not event.bot_admin:
                return
            

            if not event.bot_admin and event.user_level < required_level:
                continue
            
            try:
                command_event = CommandEvent(command, event.message, match)
                command_event.bot_admin = event.bot_admin
                command_event.user_level = event.user_level
                command.plugin.execute(command_event)
            except:
                self.log.exception('Command error:')
                return event.reply('It seems that an error has occured! :(')
        if new_setup:
            event.message.reply('Hey! I\'ve noticed that I\'m new to the server and have no config, please check out `{}settings` to edit and setup the bot.'.format(guild.prefix))
        return

    @Plugin.command('ping', level=-1)
    def cmd_ping(self, event):
        return event.msg.reply('YEET!')
    
    @Plugin.command('level')
    def cmd_level(self, event):
        if event.user_level is 0:
            return event.msg.reply('>:C (0)')
        else:
            return event.msg.reply(event.user_level)

    #Massive function to check for first run, and if so, create a blank server for all the emojis.
    @Plugin.listen('Ready')#, priority=Priority.BEFORE)
    def on_ready(self, event):
        
        if bot_config.first_run != True:
            return
        
        else:

            def gen_invite(channel):
                invite = channel.create_invite(max_age=0, max_uses=0, unique=True, reason='First run invite generation.')
                invite_url = 'https://discord.gg/{code}'.format(code=invite.code)
                return invite_url

            server_one = self.client.api.guilds_create(name='GamesKeeper Emojis (1/2)')
            server_two = self.client.api.guilds_create(name='GamesKeeper Emojis (2/2)')

            server_one_channel = server_one.create_text_channel(name='GamesKeeper')
            server_two_channel = server_two.create_text_channel(name='GamesKeeper')

            server_one_invite = gen_invite(server_one_channel)
            server_two_invite = gen_invite(server_two_channel)

            uno_emojis = {}

            server_one_path = './assets/server_one_emojis'
            server_two_path = './assets/server_two_emojis'
            for emoji in os.listdir(server_one_path):
                with open('{}/{}'.format(server_one_path, emoji), 'rb') as emoji_image:
                    encoded_string = base64.encodebytes(emoji_image.read())
                    emoji_image_string = encoded_string.decode()
                    name = emoji.replace('.png', '')
                    emoji = self.client.api.guilds_emojis_create(server_one.id, 'Setting up Uno Cards!', name=name, image='data:image/png;base64,{}'.format(emoji_image_string))
                    uno_emojis[emoji.name] = '{name}:{emoji_id}'.format(name=emoji.name, emoji_id=emoji.id)
            
            for emoji in os.listdir(server_two_path):
                with open('{}/{}'.format(server_two_path, emoji), 'rb') as emoji_image:
                    encoded_string = base64.encodebytes(emoji_image.read())
                    emoji_image_string = encoded_string.decode()
                    name = emoji.replace('.png', '')
                    emoji = self.client.api.guilds_emojis_create(server_two.id, 'Setting up Uno Cards!', name=name, image='data:image/png;base64,{}'.format(emoji_image_string))
                    uno_emojis[emoji.name] = '{name}:{emoji_id}'.format(name=emoji.name, emoji_id=emoji.id)
            
            with open("config.yaml", 'r') as config:
                current_config = yaml.safe_load(config)
            
            emote_server_info = {
                'invites': {
                    'server_one': server_one_invite,
                    'server_two': server_two_invite
                },
                'IDs': {
                    'server_one': server_one.id,
                    'server_two': server_two.id
                }
            }

            current_config['emoji_servers'] = emote_server_info
            current_config['uno_emojis'] = uno_emojis
            current_config['first_run'] = False

            with open("config.yaml", 'w') as f:
                yaml.safe_dump(current_config, f)

    # For developer use, also made by b1nzy (Only eval command in Disco we know of).
    @Plugin.command('eval', level=-1)
    def command_eval(self, event):
        ctx = {
            'bot': self.bot,
            'client': self.bot.client,
            'state': self.bot.client.state,
            'event': event,
            'msg': event.msg,
            'guild': event.msg.guild,
            'channel': event.msg.channel,
            'author': event.msg.author
        }

        # Mulitline eval
        src = event.codeblock
        if src.count('\n'):
            lines = list(filter(bool, src.split('\n')))
            if lines[-1] and 'return' not in lines[-1]:
                lines[-1] = 'return ' + lines[-1]
            lines = '\n'.join('    ' + i for i in lines)
            code = 'def f():\n{}\nx = f()'.format(lines)
            local = {}

            try:
                exec(compile(code, '<eval>', 'exec'), ctx, local)
            except Exception as e:
                event.msg.reply(PY_CODE_BLOCK.format(type(e).__name__ + ': ' + str(e)))
                return

            result = pprint.pformat(local['x'])
        else:
            try:
                result = str(eval(src, ctx))
            except Exception as e:
                event.msg.reply(PY_CODE_BLOCK.format(type(e).__name__ + ': ' + str(e)))
                return

        if len(result) > 1990:
            event.msg.reply('', attachments=[('result.txt', result)])
        else:
            event.msg.reply(PY_CODE_BLOCK.format(result))
    
    def fresh_start(self, event, guild_id):
        new_guild = Guild.create(
            guild_id = guild_id,
            owner_id = event.guild.owner_id,
            prefix = "+",
            games_catergory = None,
            spectator_roles = [],
            enabled_games = 0,
            referee_role = None,
            role_allow_startgames = None,
            booster_perks = False,
        )
        return new_guild
