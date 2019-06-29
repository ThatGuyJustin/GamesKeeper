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
from GamesKeeper.games.uno import Uno

class UnoPlugin(Plugin):

    def load(self, ctx):
        super(UnoPlugin, self).load(ctx)
        self.games = {}
        self.game = 'uno'
    
    # @Plugin.command('test', level=-1, group='uno')
    # def cmd_testing(self, event):
    #     Uno(event, [event.author, event.author])

    @Plugin.listen('MessageReactionAdd')
    def on_message_reaction_add(self, event):

        if event.channel_id not in self.games:
            return
        game = self.games.get(event.channel_id, None)
        if game == None:
            return


        def delete_game_channel():
            gevent.sleep(10)
            for x in game.game_channels:
                x.delete()

        is_game_over = game.handle_turn(event)
        if is_game_over and game.winner == 'draw':
            self.games.pop(event.channel_id, None)
            game.start_event.channel.send_message('The game ended in a **draw** in the match of Connect 4 match between <@{}> and <@{}>.'.format(game.players[0], game.players[1]))
            gevent.spawn(delete_game_channel())
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
            gevent.spawn(delete_game_channel())
            return

    @Plugin.command('play', group='uno')
    def cmd_play(self, event):
        """
        This command allows you to start a game of uno!
        Usage: `uno play`
        """

        msg = event.channel.send_message("<@{author.id}> has started a game of uno. Click the reaction to join. The game will start in 30 seconds.".format(author=event.author))
        msg.add_reaction(YES_EMOJI)
        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                        e.emoji.id != YES_EMOJI_ID
                )).get(timeout=5)
        except gevent.Timeout:
            reactions = self.client.api.channels_messages_reactions_get(msg.channel.id, msg.id, YES_EMOJI)
            players = [event.author] + list(filter(lambda x: x.id != event.author.id and not x.bot, reactions))
            if len(players) < 1:
                msg.edit("Not enough players. Match canceled.")
                return
            if len(players) > 8:
                msg.edit("Maximum player limit reached. Try again with less players.")
                return
            msg.edit("Game starting. Please wait while we setup the game!")
            game_id = max(x.game_id for x in self.games) + 1 if len(self.games) > 0 else 1
            game = Uno(event, players, game_id, msg)
            for x in game.game_channels:
                self.games[x.id] = game

            # slash_shrug = "**{}** Vs **{}**".format(players[0], players[1])
            # msg.edit(
            #     "Game {lol} has started in channel <#{channel}>! Please enjoy the game, the end results will be shown in this channel once the game is over!".format(
            #         lol=slash_shrug, channel=game.game_channel.id))
            msg.delete_reaction(YES_EMOJI, self.state.me)

            return
        
