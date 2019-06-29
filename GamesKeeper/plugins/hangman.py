from disco.bot import Bot, Plugin, CommandLevels
from disco.bot.command import CommandEvent
from GamesKeeper.games.hangman import hangman

class HangManPlugin(Plugin):

    def load(self, ctx):
        super(HangManPlugin, self).load(ctx)
        self.games = {}
        self.game = 'hangman'

    @Plugin.command('play', group='hangman')
    def hangman_play(self, event):
        #dont care if use wants to play or not just push them to a game lol for now
        game = hangman(event)
        self.games[game.game_channel.id] = game

    @Plugin.command('guess', '<letter:str...>')
    def hangman_guess(self, event, letter):
        #send guess
        if event.channel.id not in self.games:
            return
        game = self.games.get(event.channel.id, None)
        game.on_guess(event, letter)
