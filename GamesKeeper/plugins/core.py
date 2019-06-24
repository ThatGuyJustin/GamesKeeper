# -*- coding: utf-8 -*-
import yaml
import re
import requests
import functools
import pprint

from datetime import datetime, timedelta

from disco.types.permissions import Permissions
from disco.api.http import APIException
from disco.bot import Bot, Plugin, CommandLevels
from disco.bot.command import CommandEvent
from disco.types.message import MessageEmbed
from disco.types.user import GameType, Status, Game
from disco.types.channel import ChannelType
from disco.util.sanitize import S

PY_CODE_BLOCK = '```py\n{}\n```'

TEMP_PREFIX = "!"
TEMP_BOT_ADMINS = [
    104376018222972928,
    142721776458137600,
    248245568004947969,
    298516367311765505
]

TEMP_RefereeRole = 592163609296109568 

TEMP_CanStartGames = [
    591430861577256990
]

class CorePlugin(Plugin):
    def load(self, ctx):
        # start_db()
        self.bot.add_plugin = self.our_add_plugin
        self.guilds = ctx.get('guilds', {})
        super(CorePlugin, self).load(ctx)

    # Method by b1nzy#0852 
    # For the bot Rowboat 
    # (Only way to correctly handle permissions and a command hanlder within the library Disco)
    def our_add_plugin(self, cls, *args, **kwargs):
        if getattr(cls, 'global_plugin', False):
            Bot.add_plugin(self.bot, cls, *args, **kwargs)
            return

        inst = cls(self.bot, None)
        inst.register_trigger('command', 'pre', functools.partial(self.on_pre, inst))
        inst.register_trigger('listener', 'pre', functools.partial(self.on_pre, inst))
        Bot.add_plugin(self.bot, inst, *args, **kwargs)

    # Method by b1nzy#0852 
    # For the bot Rowboat 
    # (Only way to correctly handle permissions and a command hanlder within the library Disco)
    def on_pre(self, plugin, func, event, args, kwargs):
        """
        This function handles dynamically dispatching and modifying events based
        on a specific guilds configuration. It is called before any handler of
        either commands or listeners.
        """
        if hasattr(event, 'guild') and event.guild:
            guild_id = event.guild.id
        elif hasattr(event, 'guild_id') and event.guild_id:
            guild_id = event.guild_id
        else:
            guild_id = None

        if guild_id not in self.guilds:
            if isinstance(event, CommandEvent):
                if event.command.metadata.get('global_', False):
                    return event
            elif hasattr(func, 'subscriptions'):
                if func.subscriptions[0].metadata.get('global_', False):
                    return event

            return

        event.base_config = self.guilds[guild_id].get_config()
        if not event.base_config:
            return

        plugin_name = plugin.name.lower().replace('plugin', '')
        if not getattr(event.base_config.plugins, plugin_name, None):
            return

        self._attach_local_event_data(event, plugin_name, guild_id)

        return event

    def get_guild_config(self, guild_id):
        pass

    def cooldown_check(self, user):
        return False

    #Basic command handler
    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):
        event.bot_admin = event.message.author.id in TEMP_BOT_ADMINS
        event.user_level = 0

        has_admin = False

        if event.message.guild:
            if len(event.message.member.roles) > 0:
                for x in event.message.member.roles:
                    role = event.message.guild.roles.get(x)
                    if role.permissions.can(Permissions.ADMINISTRATOR):
                        event.user_level = 100
                        has_admin = True

            if not has_admin and TEMP_RefereeRole in event.message.member.roles:
                event.user_level = 50

        if event.message.author.bot:
            return
        
        # Grab the list of commands
        commands = list(self.bot.get_commands_for_message(False, {}, TEMP_PREFIX, event.message))

        #Used for cmd cooldowns
        user_ignores_cooldowns = self.cooldown_check(event.message.author.id)

        #Sorry, nothing to see here :C
        if not len(commands):
            return
        
        for command, match in commands:

            required_level = 0
            cooldown = 0

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