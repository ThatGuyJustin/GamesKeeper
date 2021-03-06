# -*- coding: utf-8 -*-
import yaml
# import re
# import requests
# import functools
import pprint
import os
import base64
import psycopg2
import time
import contextlib
from ast import literal_eval

from datetime import datetime  # , timedelta

from disco.types.permissions import Permissions
from disco.api.http import APIException
from disco.bot import Plugin  # , Bot, CommandLevels
from disco.bot.command import CommandEvent
from disco.types.message import MessageEmbed, MessageTable
from disco.types.user import GameType, Status, Game
from disco.types.channel import ChannelType
from disco.util.sanitize import S

from GamesKeeper.db import init_db, database
from GamesKeeper.models.guild import Guild
from GamesKeeper.models.games import Games, Users
from GamesKeeper import bot_config  # , update_config

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

    # Basic command handler
    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):

        if event.message.channel.type == ChannelType.DM:
            return

        if event.message.author.bot:
            return

        user_obj, created = Users.get_or_create(id=event.message.author.id)

        perms = event.message.channel.get_permissions(self.state.me)

        if not perms.can(Permissions.SEND_MESSAGES):
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

        if not event.message.content.startswith(guild.prefix) and event.message.mentions and self.state.me.id in event.message.mentions:
            content = event.message.without_mentions
            content = content.replace(' ', '', -1)
            if 'prefix' in content.lower():
                return event.channel.send_message('Prefix: `{}`'.format(
                    guild.prefix
                ))
            else:
                pass

        # Grab the list of commands
        commands = list(self.bot.get_commands_for_message(
            False, {}, guild.prefix, event.message
        ))

        # Used for cmd cooldowns
        user_ignores_cooldowns = self.cooldown_check(event.message.author.id)

        # Sorry, nothing to see here :C
        if not len(commands):
            return

        for command, match in commands:

            if command.name == 'settings' and len(commands) > 1:
                continue

            needed_level = 0
            if command.level:
                needed_level = command.level

            cooldown = 0

            if hasattr(command.plugin, 'game'):
                if not guild.check_if_listed(game_checker(command.plugin.game), 'enabled'):
                    return

            if command.level == -1 and not event.bot_admin:
                return

            if not event.bot_admin and event.user_level < needed_level:
                continue

            try:
                command_event = CommandEvent(command, event.message, match)
                command_event.bot_admin = event.bot_admin
                command_event.user_level = event.user_level
                command_event.db_user = user_obj
                command_event.db_guild = guild
                if command.args:
                    if len(command_event.args) < command.args.required_length:
                        self.dis_cmd_help(command, command_event, event, guild)
                        return
                command.plugin.execute(command_event)
            except:
                self.log.exception('Command error:')
                return event.reply('It seems that an error has occured! :(')
        if new_setup:
            event.message.reply('Hey! I\'ve noticed that I\'m new to the server and have no config, please check out `{}settings` to edit and setup the bot.'.format(guild.prefix))
        return

    def dis_cmd_help(self, command, command_event, event, guild_obj):
        embed = MessageEmbed()
        embed.title = 'Command: {}{}'.format(
            '{} '.format(command.group) if hasattr(command, 'group') and command.group != None else '', command.name
        )
        helpstr = command.get_docstring()
        embed.description = helpstr
        event.message.channel.send_message('', embed=embed)

    @Plugin.command('help', '[command:str...]')
    def cmd_help(self, event, command=None):
        """
        This is the help command! Use this command to help you get info some certain commands.
        Usage: `help [Command Name]`
        To get general info, just type `help`
        """
        if command is None:
            embed = MessageEmbed()
            embed.title = 'GamesKeeper Help'
            embed.description = '**To get help with a certain command please use `{prefix}help Command`**\n** **\nFor help with settings please type `{prefix}help settings`'.format(prefix=event.db_guild.prefix)
            return event.msg.reply('', embed=embed)
        elif command == 'settings' and (event.user_level == 100 or event.bot_admin):
            embed = MessageEmbed()
            embed.title = 'GamesKeeper Settings Help'
            description = [
                'To change most settings, the command group is `update`',
                '\♦ To change **Prefix**, use `{}settings prefix`'.format(event.db_guild.prefix),
                '\♦ To change **Games Category**, use `{}settings gc`'.format(event.db_guild.prefix),
                '\♦ To change the **Referee** role, use `{}settings ref`'.format(event.db_guild.prefix),
                '\♦ To update **Spectator** roles, use `{}settings addspec/rvmspec`'.format(event.db_guild.prefix),
                '\♦ To **Enable/Disable Games**, use `{}games enable/disable`'.format(event.db_guild.prefix),
            ]
            embed.description = '\n'.join(description)
            return event.msg.reply('', embed=embed)
        elif command == 'settings' and (event.user_level != 100 or not event.bot_admin):
            return event.msg.reply('`Error:` Command Not Found')
        else:
            commands = list(self.bot.commands)
            for cmd in commands:
                if cmd.name != command:
                    continue
                elif cmd.level == -1 and not event.bot_admin:
                    continue
                else:
                    embed = MessageEmbed()
                    embed.title = 'Command: {}{}'.format(
                        '{} '.format(cmd.group) if hasattr(cmd, 'group') and
                        cmd.group is not None else '', cmd.name
                    )
                    helpstr = cmd.get_docstring()
                    embed.description = helpstr
                    return event.msg.reply('', embed=embed)
            return event.msg.reply('`Error:` Command Not Found')

    @Plugin.command('ping', level=-1)
    def cmd_ping(self, event):
        """
        Returns the current latencey between the bot and Discord's API in Milliseconds.
        """
        return event.msg.reply("Current Ping: **{}** ms".format(round(self.client.gw.latency * 1000, 2)))

    # @Plugin.schedule(60, init=False)
    # def update_servers(self):
    #     l = self.state.me.presence.game.name
    #     l.split(' ')

    @contextlib.contextmanager
    def send_control_message(self):
        embed = MessageEmbed()
        embed.set_footer(text='GamesKeeper Log')
        embed.timestamp = datetime.utcnow().isoformat()
        embed.color = 0x779ecb
        try:
            yield embed
            self.bot.client.api.channels_messages_create(
                bot_config.logging_channel,
                embed=embed
            )
        except:
            self.log.exception('Failed to send control message:')
            return

    @Plugin.listen('Resumed')
    def on_resumed(self, event):
        self.client.update_presence(Status.ONLINE, Game(
            name='on {} Servers.'.format(len(self.state.guilds)),
            type=GameType.DEFAULT
        ))
        trace_event = literal_eval(event.trace[0])

        with self.send_control_message() as embed:
            embed.title = 'Resumed'
            embed.color = 0xffb347
            embed.add_field(name='Gateway Server', value=trace_event[0],
                            inline=False)
            embed.add_field(name='Session Server', value=trace_event[1]['calls'][0], inline=False)
            embed.add_field(name='Replayed Events',
                            value=str(self.client.gw.replayed_events))

    # Massive function to check for first run, and if so, create a blank
    # server for all the emojis.
    @Plugin.listen('Ready')  # , priority=Priority.BEFORE)
    def on_ready(self, event):
        self.client.update_presence(
            Status.ONLINE, Game(name='on {} Servers'.format(
                len(event.guilds)),
                type=GameType.DEFAULT
            )
        )
        trace_event = literal_eval(event.trace[0])
        reconnects = self.client.gw.reconnects

        self.log.info('Started session {}'.format(event.session_id))
        with self.send_control_message() as embed:
            if reconnects:
                embed.title = 'Reconnected'
                embed.color = 0xffb347
            else:
                embed.title = 'Connected'
                embed.color = 0x77dd77

            embed.add_field(name='Gateway Server', value=trace_event[0],
                            inline=False)
            embed.add_field(name='Session Server',
                            value=trace_event[1]['calls'][0], inline=False)

        if bot_config.first_run is not True:
            return

        else:

            def gen_invite(channel):
                invite = channel.create_invite(
                    max_age=0,
                    max_uses=0,
                    unique=True,
                    reason='First run invite generation.'
                )
                invite_url = 'https://discord.gg/{code}'.format(
                    code=invite.code
                )
                return invite_url

            server_one = self.client.api.guilds_create(
                name='GamesKeeper Emojis (1/2)')
            server_two = self.client.api.guilds_create(
                name='GamesKeeper Emojis (2/2)')

            server_one_channel = server_one.create_text_channel(
                name='GamesKeeper')
            server_two_channel = server_two.create_text_channel(
                name='GamesKeeper')

            server_one_admin = server_one.create_role(
                name='Admin', permissions=9)
            server_two_admin = server_two.create_role(
                name='Admin', permissions=9)

            server_one_invite = gen_invite(server_one_channel)
            server_two_invite = gen_invite(server_two_channel)

            c4_names = ['Blank', 'Blue', 'BlueNoBorder', 'Red', 'RedNoBorder']
            hangman_emotes = {}
            connect4_emotes = {}
            uno_emojis = {}
            ttt_emojis = {}

            server_one_path = './assets/server_one_emojis'
            server_two_path = './assets/server_two_emojis'
            for emoji in os.listdir(server_one_path):
                with open('{}/{}'.format(server_one_path, emoji), 'rb') as emoji_image:
                    encoded_string = base64.encodebytes(emoji_image.read())
                    emoji_image_string = encoded_string.decode()
                    name = emoji.replace('.png', '')
                    emoji = self.client.api.guilds_emojis_create(
                        server_one.id, 'Setting up Uno Cards!',
                        name=name, image='data:image/png;base64,{}'
                            .format(emoji_image_string))
                    uno_emojis[emoji.name] = '{name}:{emoji_id}'.format(
                        name=emoji.name, emoji_id=emoji.id)

            for emoji in os.listdir(server_two_path):
                with open('{}/{}'.format(server_two_path, emoji), 'rb') as emoji_image:
                    encoded_string = base64.encodebytes(emoji_image.read())
                    emoji_image_string = encoded_string.decode()
                    name = emoji.replace('.png', '')
                    emoji = self.client.api.guilds_emojis_create(server_two.id, 'Setting up Uno Cards!', name=name, image='data:image/png;base64,{}'.format(emoji_image_string))

                    if name.startswith('Hangman'):
                        hangman_emotes[name.replace('Hangman', '', -1)] = '{name}:{emoji_id}'.format(name=emoji.name, emoji_id=emoji.id)
                    elif name.startswith('TicTacToe'):
                        ttt_emojis[emoji.name] = '{name}:{emoji_id}'.format(
                            name=emoji.name, emoji_id=emoji.id)
                    elif name in c4_names:
                        connect4_emotes[emoji.name] = '{name}:{emoji_id}'.format(
                            name=emoji.name, emoji_id=emoji.id)
                    else:
                        uno_emojis[emoji.name] = '{name}:{emoji_id}'.format(
                            name=emoji.name, emoji_id=emoji.id)

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
                },
                'admin_roles': {
                    'server_one': server_one_admin.id,
                    'server_two': server_two_admin.id
                }
            }

            current_config['emoji_servers'] = emote_server_info
            current_config['uno_emojis'] = uno_emojis
            current_config['connect4_emotes'] = connect4_emotes
            current_config['hangman_emotes'] = hangman_emotes
            current_config['ttt_emotes'] = ttt_emojis
            # current_config['other_emotes'] = other_emotes
            current_config['first_run'] = False

            with open("config.yaml", 'w') as f:
                yaml.safe_dump(current_config, f)

        if not bot_config.first_run and not hasattr(bot_config, 'uno_emojis'):

            c4_names = ['Blank', 'Blue', 'BlueNoBorder', 'Red', 'RedNoBorder']

            hangman_emotes = {}
            c4_emotes = {}
            uno_emotes = {}
            ttt_emotes = {}

            server_one = self.state.guilds.get(bot_config.emoji_servers['IDs']['server_one'])
            server_two = self.state.guilds.get(bot_config.emoji_servers['IDs']['server_two'])

            for emoji in server_one.emojis.values():
                uno_emotes[emoji.name] = '{name}:{emoji_id}'.format(
                    name=emoji.name, emoji_id=emoji.id)

            for emoji in server_two.emojis.values():
                name = emoji.name
                if name.startswith('Hangman'):
                    hangman_emotes[name.replace('Hangman', '', -1)] = '{name}:{emoji_id}'.format(name=emoji.name, emoji_id=emoji.id)
                elif name.startswith('TicTacToe'):
                    ttt_emotes[emoji.name] = '{name}:{emoji_id}'.format(
                        name=emoji.name, emoji_id=emoji.id)
                elif name in c4_names:
                    c4_emotes[emoji.name] = '{name}:{emoji_id}'.format(
                        name=emoji.name, emoji_id=emoji.id)
                else:
                    uno_emotes[emoji.name] = '{name}:{emoji_id}'.format(
                        name=emoji.name, emoji_id=emoji.id)

            with open("config.yaml", 'r') as config:
                current_config = yaml.safe_load(config)

            current_config['uno_emojis'] = uno_emotes
            current_config['connect4_emotes'] = c4_emotes
            current_config['hangman_emotes'] = hangman_emotes
            current_config['ttt_emotes'] = ttt_emotes

            with open("config.yaml", 'w') as f:
                yaml.safe_dump(current_config, f)

    # For developer use, also made by b1nzy (Only eval command in Disco we know of).
    @Plugin.command('eval', level=-1)
    def command_eval(self, event):
        """
        This a Developer command which allows us to run code without having to restart the bot.
        """
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

    @Plugin.command('sql', level=-1)
    def command_sql(self, event):
        """
        This a Developer command which allows us to run Database commands without having to interact with the actual database directly.
        """
        conn = database.obj.get_conn()

        try:
            tbl = MessageTable(codeblock=False)

            with conn.cursor() as cur:
                start = time.time()
                cur.execute(event.codeblock.format(e=event))
                dur = time.time() - start
                if not cur.description:
                    return event.msg.reply('_took {}ms - no result_'.format(
                        int(dur * 1000)))
                tbl.set_header(*[desc[0] for desc in cur.description])

                for row in cur.fetchall():
                    tbl.add(*row)

                result = tbl.compile()
                if len(result) > 1900:
                    return event.msg.reply(
                        '_took {}ms_'.format(int(dur * 1000)),
                        attachments=[('result.txt', result)])

                event.msg.reply('```' + result + '```\n_took {}ms_\n'.format(
                    int(dur * 1000)))
        except psycopg2.Error as e:
            event.msg.reply('```{}```'.format(e.pgerror))

    def fresh_start(self, event, guild_id):
        new_guild = Guild.create(
            guild_id=guild_id,
            owner_id=event.guild.owner_id,
            prefix="+",
            games_catergory=None,
            spectator_roles=[],
            enabled_games=0,
            referee_role=None,
            role_allow_startgames=None,
            booster_perks=False,
        )
        return new_guild
