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
        settings = Guild.using_id(event.guild.id)

        games_category = None
        if settings.games_category:
            games_category = event.guild.channels.get(settings.games_category)
        
        spectator_roles = []
        if len(settings.spectator_roles) > 0:
            for x in settings.spectator_roles:
                spectator_roles.append('<@&{}>'.format(x))
        embed = MessageEmbed()
        embed.color = 0xFF0000
        embed.add_field(name='Prefix', value='{}'.format(settings.prefix), inline=True)
        embed.add_field(name='Games Category', value='{} (`{}`)'.format(games_category.name, games_category.id) if settings.games_category else '`None`', inline=True)
        embed.add_field(name='Spectator Roles', value='{}'.format('`None`' if len(spectator_roles) == 0 else ', '.join(spectator_roles)), inline=True)
        embed.add_field(name='Referee Role', value='{}'.format('`None`' if settings.referee_role == None else '<@&' + str(settings.referee_role) + '>'), inline=True)
        embed.add_field(name='Enabled Games', value='`{}`'.format(settings.enabled_games_emotes()))
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