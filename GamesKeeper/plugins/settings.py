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

from GamesKeeper import NO_EMOJI_ID, YES_EMOJI_ID, NO_EMOJI, YES_EMOJI
from GamesKeeper.models.guild import Guild

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

class SettingsPlugin(Plugin):

    def load(self, ctx):
        super(SettingsPlugin, self).load(ctx)
    

    @Plugin.command('settings', level=CommandLevels.ADMIN)
    def list_settings(self, event):
        settings_msg = """
        __**Prefix**__: {prefix}
        __**Referee Role**__: {rr}
        __**Games Category**__: {gc}
        __**Spectator Roles**__: {sr}
        __**Game Logs**__: {gl}
        """
        settings = Guild.using_id(event.guild.id)

        games_category = None
        if settings.games_category:
            games_category = event.guild.channels.get(settings.games_category)
        
        log_channel = None
        if settings.log_channel:
            log_channel = event.guild.channels.get(settings.log_channel)
        
        spectator_roles = []
        if len(settings.spectator_roles) > 0:
            for x in settings.spectator_roles:
                spectator_roles.append('<@&{}>'.format(x))
        embed = MessageEmbed()
        # embed.color = 0xFF0000
        embed.add_field(name='General Settings', value=settings_msg.format(
            prefix=settings.prefix, 
            rr='{}'.format('`None`' if settings.referee_role == None else '<@&' + str(settings.referee_role) + '>'), 
            gc='{} (`{}`)'.format(games_category.name, games_category.id) if settings.games_category else '`None`',
            sr='{}'.format('`None`' if len(spectator_roles) == 0 else ', '.join(spectator_roles)),
            gl='({}) {channel}'.format('<{}>'.format(YES_EMOJI if settings.logs_enabled else NO_EMOJI), channel='{} (`{}`)'.format(log_channel.name, log_channel.id) if settings.log_channel else '`None`')
        ))
        embed.add_field(name='Enabled Games', value='{}'.format(''.join(settings.enabled_games_emotes())), inline=True)
        embed.add_field(name='Disabled Games', value='{}'.format(''.join(settings.disabled_games_emotes())), inline=True)
        embed.set_footer(text='Go get help with settings, do {}help settings'.format(settings.prefix), icon=self.state.me.get_avatar_url())
        embed.set_thumbnail(url=event.guild.get_icon_url('png'))
        return event.msg.reply('', embed=embed)

    @Plugin.command('logs enable', context={'mode': 'enable'}, group='settings', level=CommandLevels.ADMIN)
    @Plugin.command('logs disable', context={'mode': 'disable'}, group='settings', level=CommandLevels.ADMIN)
    @Plugin.command('logs channel', '<channel:channel>', context={'mode': 'setchannel'}, group='settings', level=CommandLevels.ADMIN)
    def logs(self, event, channel=None, mode=None):
        """
        This command is used to change the Game Logs settings.
        Usage: `update logs enable/disable/channel [ChannelID, Mention, Name]`
        """
        guild = Guild.using_id(event.guild.id)
        if mode == 'enable':
            guild.logs_enabled = True
            guild.save()
            return event.msg.reply('<{}> Logs have been enabled!'.format(YES_EMOJI))
        
        if mode == 'disable':
            guild.logs_enabled = False
            guild.save()
            return event.msg.reply('<{}> Logs have been disabled!'.format(YES_EMOJI))
        
        if mode == 'setchannel':
            if isinstance(channel, int):
                if guild.log_channel == channel:
                    return event.msg.reply('`Error:` New logs channel matches the current logs channel.')
                else:
                    guild.log_channel = channel
                    guild.save()
                    new_channel = event.guild.channels[channel]
                    return event.msg.reply('Updated the logs channel to **{name}** (`{id}`)'.format(name=new_channel.name, id=new_channel.id))
            else:
                if guild.log_channel == channel.id:
                    return event.msg.reply('`Error:` New logs channel matches the current logs channel.')
                else:
                    guild.log_channel = channel.id
                    guild.save()
                    return event.msg.reply('Updated the logs channel to **{name}** (`{id}`)'.format(name=channel.name, id=channel.id))
    
    @Plugin.command('prefix', '<prefix:str...>', aliases=['setprefix', 'changeprefix'], level=CommandLevels.ADMIN, group='settings')
    def change_prefix(self, event, prefix):
        """
        This command is used to change the bot's prefix.
        Usage: `update prefix *insert prefix here*`
        Example: `update prefix !`
        """
        guild = Guild.using_id(event.guild.id)
        if guild.prefix == prefix:
            return event.msg.reply('`Error:` New prefix matches the current prefix.')
        else:
            guild.prefix = prefix
            guild.save()
            return event.msg.reply('Prefix has been updated to `{}`!'.format(guild.prefix))
    
    @Plugin.command('gamescategory', '<channel:channel>', aliases=['setgamescategory', 'changegamescategory', 'setcategory', 'changecategory', 'gc'], level=CommandLevels.ADMIN, group='settings')
    def change_catergory(self, event, channel):
        """
        This command is used to change the games cetegory.
        Usage: `update gc [ChannelID]`
        """
        guild = Guild.using_id(event.guild.id)
        if isinstance(channel, int):
            if guild.games_category == channel:
                return event.msg.reply('`Error:` New games category matches the current games category.')
            else:
                guild.games_category = channel
                guild.save()
                new_channel = event.guild.channels[channel]
                return event.msg.reply('Updated the games category to **{name}** (`{id}`)'.format(name=new_channel.name, id=new_channel.id))
        else:
            if guild.games_category == channel.id:
                return event.msg.reply('`Error:` New games category matches the current games category.')
            else:
                guild.games_category = channel.id
                guild.save()
                return event.msg.reply('Updated the games category to **{name}** (`{id}`)'.format(name=channel.name, id=channel.id))
    
    @Plugin.command('setreferee', '<role:str...>', aliases=['setref', 'ref', 'referee'], level=CommandLevels.ADMIN, group='settings')
    def update_referee(self, event, role):
        """
        This command is used to change the referee role.
        Usage: `update ref [Role Name or Role ID]`
        """
        if role.isdigit():
            role = int(role)
        new_role = self.get_role(event, role)
        if not new_role:
            return event.msg.reply('`Error:` Role not found, please check ID/Name and try again.')
        guild = Guild.using_id(event.guild.id)
        if guild.referee_role == new_role.id:
            return event.msg.reply('`Error:` New referee role matches the current referee role.')
        else:
            guild.referee_role = new_role.id
            guild.save()
            return event.msg.reply('Updated the referee role to **{name}** (`{id}`)'.format(name=new_role.name, id=new_role.id))
    
    @Plugin.command('enable', '<game:str...>', context={'mode': 'enable'}, group='games', level=CommandLevels.ADMIN)
    @Plugin.command('disable', '<game:str...>', context={'mode': 'disable'}, group='games', level=CommandLevels.ADMIN)
    def update_games(self, event, game, mode=None):
        """
        This command is used to enable/disable games.
        Usage: `games enable/disable [Game]`
        Current Games: **Connect 4**, **Uno**, **TicTacToe**, **HangMan**
        """
        game_types = {
            "uno": 1 << 0, #Uno
            'c4': 1 << 1, #Connect4
            'ttt': 1 << 2, #TicTacToe
            'hm': 1 << 3, #Hangman
            # '2048': 1 << 4, #2048
            # 'trivia': 1 << 5, #Trivia
        }
        game_name = game_checker(game)
        if game_name == None:
            return event.msg.reply('`Error`: Game not found.')
        
        guild = Guild.using_id(event.guild.id)
        if mode == 'enable':
            listed = guild.check_if_listed(game_name, 'enabled')
            if listed:
                return event.msg.reply('`Error`: Game is already enabled.')
            else:
                guild.enabled_games = guild.enabled_games + game_types[game_name]
                guild.save()
                return event.msg.reply('Game has been enabled!')
        if mode == 'disable':
            listed = guild.check_if_listed(game_name, 'disabled')
            if listed:
                return event.msg.reply('`Error`: Game is already disabled.')
            else:
                guild.enabled_games = guild.enabled_games - game_types[game_name]
                guild.save()
                return event.msg.reply('Game has been disabled!')

    @Plugin.command('addspec', '<role:str...>', aliases=['add spec', 'spec add', 'spectators add', 'add spectators', 'add spectator', 'spectator add'], level=CommandLevels.ADMIN, group='settings', context={'mode': 'add'})
    @Plugin.command('listspec', aliases=['list spec', 'list add', 'spectators list', 'list spectators', 'list spectator', 'spectator list'], level=CommandLevels.ADMIN, group='settings', context={'mode': 'list'})
    @Plugin.command('rvmspec', '<role:str...>', aliases=['rvm spec', 'spec rvm', 'spectators rvm', 'rvm spectators', 'rvm spectator', 'spectator rvm', 'remove spec', 'spec remove', 'spectators remove', 'remove spectators', 'remove spectator', 'spectator remove'], level=CommandLevels.ADMIN, group='settings', context={'mode': 'rvm'})
    def update_spectators(self, event, role, mode=None):
        """
        This command is used to update the spectator roles.
        Usage: `change addspec/rvmspec [Role Name or Role ID]`
        """
        if role.isdigit():
            role = int(role)
        arg_role = self.get_role(event, role)
        if not arg_role:
            return event.msg.reply('`Error:` Role not found, please check ID/Name and try again.')
        guild = Guild.using_id(event.guild.id)
        if arg_role.id in guild.spectator_roles and mode == 'add':
            return event.msg.reply('`Error:` That role is already labled as a spectator.')
        if arg_role.id not in guild.spectator_roles and mode == 'rvm':
            return event.msg.reply('`Error:` That role is not labled as a spectator.')
        
        if mode == 'add':
            guild.spectator_roles.append(arg_role.id)
            guild.save()
            return event.msg.reply('Added role **{name}** (`{id}`) as a spectator.'.format(name=arg_role.name, id=arg_role.id))
        if mode == 'rvm':
            guild.spectator_roles.remove(arg_role.id)
            guild.save()
            return event.msg.reply('Removed role **{name}** (`{id}`) as a spectator.'.format(name=arg_role.name, id=arg_role.id))


    def get_role(self, event, role):
        if isinstance(role, int):
            new_role = None
            try:
                new_role = event.guild.roles.get(role)
            except:
                return None
            return new_role
        elif isinstance(role, str):
            correct_role = None
            dupes = []
            for x in event.guild.roles:
                current = event.guild.roles[x]
                if current.name.lower() == role.lower():
                    dupes.append(current)
            if len(dupes) > 1:
                for x in dupes:
                    embed = MessageEmbed()
                    embed.description = 'Is this role correct? <@&{}>'.format(str(x.id))
                    embed.add_field(name='ID', value=str(x.id), inline=True)
                    embed.add_field(name='Position', value=str(x.position), inline=True)
                    embed.add_field(name='Mentionable', value='{}'.format('Yes' if x.mentionable else 'No'), inline=True)
                    if x.color:
                        embed.color = x.color
                    msg = event.msg.reply('', embed=embed)
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
                    finally:
                        msg.delete()
                    
                    if mra_event.emoji.id == YES_EMOJI_ID:
                        correct_role = x
                        break

                return correct_role

            else:

                return correct_role