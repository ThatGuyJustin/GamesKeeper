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
from GamesKeeper.games.connectfour import Connect4

class ConnectFourPlugin(Plugin):
    global_plugin = True

    def load(self, ctx):
        super(ConnectFourPlugin, self).load(ctx)
        self.games = {}
    
    # @Plugin.command('test', level=-1, group='c4')
    # def cmd_testing(self, event):
    #     Connect4(event, [event.author, event.author])

    @Plugin.listen('MessageReactionAdd')
    def on_message_reaction_add(self, event):

        if event.channel_id not in self.games:
            return
        game = self.games.get(event.channel_id, None)
        if game == None:
            return

        def yeet_game_channel():
            gevent.sleep(10)
            game.game_channel.delete()

        is_game_over = game.handle_turn(event)
        if is_game_over and game.winner == 'draw':
            self.games.pop(event.channel_id, None)
            game.start_event.channel.send_message('The game ended in a **draw** in the match of Connect 4 match between <@{}> and <@{}>.'.format(game.players[0], game.players[1]))
            gevent.spawn(yeet_game_channel())
            return
        if is_game_over:
            def get_other():
                other = None
                for x in game.players:
                    if x == game.winner:
                        continue
                    else:
                        other = x
                        break
                return other
            self.games.pop(event.channel_id, None)
            game.start_event.channel.send_message('The winner is <@{}> in the match of Connect 4 match against <@{}>!'.format(game.winner, get_other()))
            gevent.spawn(yeet_game_channel())
            return
    
    @Plugin.command('play', '<user:user>', group='c4')
    def cmd_play(self, event, user):
        if isinstance(user, int):
            user = self.state.users.get(user)
        
        msg = event.channel.send_message("<@{user.id}>, do you accept the match against player **{author}**? You have 10 seconds to select.".format(user=user, author=event.author))
        msg.chain(False).\
            add_reaction('✅').\
            add_reaction('⛔')
        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                        e.emoji.name in ('✅', '⛔') and
                        e.user_id == user.id
                )).get(timeout=10)
        except gevent.Timeout:
            msg.edit("**{user}** did not respond in time. Match canceled.".format(user=user))
            msg.delete_reaction('✅', self.state.me)
            msg.delete_reaction('⛔', self.state.me)
            return
        
        if mra_event.emoji.name != '✅':
            msg.edit("**{user}** Denied your request. Match canceled.".format(user=user))
            return
        
        msg.edit("**{user}** accepted your matchmaking request. Please wait while we setup the game!".format(user=user))
        players = [event.author, user]
        game = Connect4(event, players)
        self.games[game.game_channel.id] = game

        slash_shrug = "**{}** Vs **{}**".format(players[0], players[1])
        msg.edit("Game {lol} has started in channel <#{channel}>! Please enjoy the game, the end results will be shown in this channel once the game is over!".format(lol=slash_shrug, channel=game.game_channel.id))