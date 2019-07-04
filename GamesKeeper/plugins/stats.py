# -*- coding: utf-8 -*-
import yaml
import re
import requests
import functools
import gevent

from datetime import datetime, timedelta
from peewee import fn

from disco.types.message import MessageTable, MessageEmbed, MessageEmbedField, MessageEmbedThumbnail
from disco.api.http import APIException
from disco.bot import Bot, Plugin, CommandLevels
from disco.bot.command import CommandEvent
from disco.types.message import MessageEmbed
from disco.types.user import GameType, Status, Game
from disco.types.channel import ChannelType
from disco.util.sanitize import S

from GamesKeeper.models.guild import Guild
from GamesKeeper.models.games import Games

PLAYER_STATS = """
**__Overall Stats__**:
**Total Games Played**: {games_played}
**Total Wins**: {games_won}
**Total Losses**: {games_lost}
**W/L Ratio**: {wl_ratio}

__**Games Stats**__:
"""

UNO_STR = """
\♦ Wins: {UNO_STATS.wins}
\♦ W/L Ratio: {UNO_STATS.wl}
\♦ Total Games: {UNO_STATS.games}
\♦ Cards Drawn: {UNO_STATS.cards_drawn}
\♦ Cards Played: {UNO_STATS.cards_played}
"""

C4_STR = """
\♦ Wins: {C4_STATS.wins}
\♦ W/L Ratio: {C4_STATS.wl}
\♦ Total Games: {C4_STATS.games}
"""

HM_STR = """
\♦ Wins: {HM_STATS.wins}
\♦ W/L Ratio: {HM_STATS.wl}
\♦ Total Games: {HM_STATS.games}
\♦ Total Guesses: {HM_STATS.total_guesses}
\♦ Total Correct Guesses: {HM_STATS.total_guesses_c}
\♦ Total Incorrect Guesses: {HM_STATS.total_guesses_i}
"""

TTT_STR = """
\♦ Wins: {TTT_STATS.wins}
\♦ W/L Ratio: {TTT_STATS.wl}
\♦ Total Games: {TTT_STATS.games}
"""
class StatsPlugin(Plugin):
    global_plugin = True

    def load(self, ctx):
        super(StatsPlugin, self).load(ctx)
    
    @Plugin.command('stats', '[user:user] [game:str]', aliases=['userstats', 'mystats'])
    def cmd_stats(self, event, user=None, game=None):
        """
        This command allows you to view either your stats, or stats of another user!
        Usage: `stats`
        Other User's Stats: `stats [@User#1234 or UserID]`
        """
        
        embed = MessageEmbed()

        class UNO_STATS(object):
            games = 0
            wins = 0
            cards_drawn = 0
            cards_played = 0
            wl = 0.0
        class C4_STATS(object):
            wins = 0
            wl = 0
            games = 0
        class HANGMAN_STATS(object):
            wins = 0
            wl = 0
            games = 0
            total_guesses_i = 0
            total_guesses_c = 0
            total_guesses = 0
        class TTT_STATS(object):
            wins = 0
            wl = 0
            games = 0

        def calc_uno(games, user):
            UNO_STATS.games = games.count()
            UNO_STATS.wins = games.where(Games.winner == user.id).count()
            UNO_STATS.cards_drawn = 0
            UNO_STATS.cards_played = 0
            # UNO_STATS.cards_drawn = games.select(fn.Sum(Games.cards_drawn)).execute().next().cards_drawn
            # UNO_STATS.cards_played = games.select(fn.Sum(Games.cards_played)).execute().next().cards_played
            UNO_STATS.wl = str(round(UNO_STATS.wins / (UNO_STATS.games - UNO_STATS.wins), 3)) if UNO_STATS.games > 0 else '0'
        
        def calc_hangman(games, user):
            HANGMAN_STATS.games = games.count()
            HANGMAN_STATS.wins = games.where(Games.winner == user.id).count()
            HANGMAN_STATS.total_guesses = games.select(fn.Sum(Games.guesses_correct + Games.guesses_incorrect).alias('total')).execute().next().total or '0'
            HANGMAN_STATS.total_guesses_c = games.select(fn.Sum(Games.guesses_correct)).execute().next().guesses_correct or '0'
            HANGMAN_STATS.total_guesses_i = games.select(fn.Sum(Games.guesses_incorrect)).execute().next().guesses_incorrect or '0'
            HANGMAN_STATS.wl = str(round(HANGMAN_STATS.wins / (HANGMAN_STATS.games - HANGMAN_STATS.wins), 3)) if HANGMAN_STATS.games > 0 else '0'
        
        def calc_c4(games, user):
            C4_STATS.games = games.count()
            C4_STATS.wins = games.where(Games.winner == user.id).count()
            C4_STATS.wl = str(round(C4_STATS.wins / (C4_STATS.games - C4_STATS.wins), 3)) if C4_STATS.games > 0 else '0'
        
        def calc_ttt(games, user):
            TTT_STATS.games = games.count()
            TTT_STATS.wins = games.where(Games.winner == user.id).count()
            TTT_STATS.wl = str(round(TTT_STATS.wins / (TTT_STATS.games - TTT_STATS.wins), 3)) if TTT_STATS.games > 0 else '0'

        def compile_stats(user):
            games = Games.select().where((Games.ended == True) & (Games.players.contains(user.id)))
            games_c4 = games.where(Games.type_ == Games.Types.CONNECT_FOUR)
            games_hangman = games.where(Games.type_ == Games.Types.HANGMAN)
            games_ttt = games.where(Games.type_ == Games.Types.TIC_TAC_TOE)
            games_uno = games.where(Games.type_ == Games.Types.UNO)
            
            gp = games.count()
            gw = games.where(Games.winner == user.id).count()
            gl = gp - gw
            wl = str(round(gw/gl, 3)) if gp > 0 else '0'

            calc_uno(games_uno, user)
            calc_hangman(games_hangman, user)
            calc_c4(games_c4, user)
            calc_ttt(games_ttt, user)
            embed.set_author(icon_url=user.get_avatar_url(), name='Stats for {}'.format(str(user)))
            embed.description = PLAYER_STATS.format(
                games_won=gw,
                games_played=gp,
                wl_ratio=wl,
                games_lost=gl,
            )
            embed.add_field(name='<:{}>'.format('hangman:594231153914019840'), value=HM_STR.format(HM_STATS=HANGMAN_STATS), inline=True)
            embed.add_field(name='<:{}>'.format('uno:594231154098438153'), value=UNO_STR.format(UNO_STATS=UNO_STATS), inline=True)
            embed.add_field(name='<:{}>'.format('connectfour:594231155172179985'), value=C4_STR.format(C4_STATS=C4_STATS), inline=True)
            embed.add_field(name='<:{}>'.format('tictactoe:594231153830133761'), value=TTT_STR.format(TTT_STATS=TTT_STATS), inline=True)
            event.msg.reply('', embed=embed)

        if user == None and game == None:
            user = event.author
            return compile_stats(user)
        
        if user != None:
            if isinstance(user, int):
                try:
                    user = self.state.users.get(user)
                except:
                    return event.msg.reply('`Error:` User not found.')

                return compile_stats(user)
            else:
                return compile_stats(user)
            