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


class SettingsPlugin(Plugin):
    global_plugin = True

    def load(self, ctx):
        super(SettingsPlugin, self).load(ctx)
    

    @Plugin.command('settings', level=CommandLevels.ADMIN)
    def list_settings(self, event):
        settings_msg = """
        __**Prefix**__: {prefix}
        __**Referee Role**__: {rr}
        __**Games Category**__: {gc}
        __**Spectator Roles**__: {sr}
        """
        settings = Guild.using_id(event.guild.id)

        games_category = None
        if settings.games_category:
            games_category = event.guild.channels.get(settings.games_category)
        
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
            sr='{}'.format('`None`' if len(spectator_roles) == 0 else ', '.join(spectator_roles))
        ))
        embed.add_field(name='Enabled Games', value='{}'.format(''.join(settings.enabled_games_emotes())), inline=True)
        embed.add_field(name='Disabled Games', value='{}'.format(''.join(settings.disabled_games_emotes())), inline=True)
        return event.msg.reply('', embed=embed)
    
    @Plugin.command('prefix', '<prefix:str...>', aliases=['setprefix', 'changeprefix'], level=CommandLevels.ADMIN, group='update')
    def change_prefix(self, event, prefix):
        guild = Guild.using_id(event.guild.id)
        if guild.prefix == prefix:
            return event.msg.reply('`Error:` New prefix matches the current prefix.')
        else:
            guild.prefix = prefix
            guild.save()
            return event.msg.reply('Prefix has been updated to `{}`!'.format(guild.prefix))
    
    @Plugin.command('gamescategory', '<channel:channel>', aliases=['setgamescategory', 'changegamescategory', 'setcategory', 'changecategory', 'gc'], level=CommandLevels.ADMIN, group='update')
    def change_catergory(self, event, channel):
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
    
    @Plugin.command('setreferee', '<role:str...>', aliases=['setref', 'ref', 'referee'], level=CommandLevels.ADMIN, group='update')
    def update_referee(self, event, role):
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
    
    @Plugin.command('addspec', '<role:str...>', aliases=['add spec', 'spec add', 'spectators add', 'add spectators', 'add spectator', 'spectator add'], level=CommandLevels.ADMIN, group='update', context={'mode': 'add'})
    @Plugin.command('listspec', aliases=['list spec', 'list add', 'spectators list', 'list spectators', 'list spectator', 'spectator list'], level=CommandLevels.ADMIN, group='update', context={'mode': 'add'})
    @Plugin.command('rvmspec', '<role:str...>', aliases=['rvm spec', 'spec rvm', 'spectators rvm', 'rvm spectators', 'rvm spectator', 'spectator rvm', 'remove spec', 'spec remove', 'spectators remove', 'remove spectators', 'remove spectator', 'spectator remove'], level=CommandLevels.ADMIN, group='update', context={'mode': 'rvm'})
    def update_spectators(self, event, role, mode=None):
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
                    msg.chain(False).\
                        add_reaction('✅').\
                        add_reaction('⛔')

                    try:
                        mra_event = self.wait_for_event(
                            'MessageReactionAdd',
                            message_id = msg.id,
                            conditional = lambda e: (
                                e.emoji.name in ('✅', '⛔') and
                                e.user_id == event.author.id
                            )).get(timeout=10)
                    except gevent.Timeout:
                        return
                    finally:
                        msg.delete()
                    
                    if mra_event.emoji.name != '✅':
                        continue
                    
                    dupes = [x]
                    break
                return dupes[0]
            else:
                return dupes[0]