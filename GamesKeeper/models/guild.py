from GamesKeeper.db import BaseModel
from peewee import (BigIntegerField, IntegerField, TextField, BooleanField,
                    DoesNotExist)
from playhouse.postgres_ext import BinaryJSONField, ArrayField


@BaseModel.register
class Guild(BaseModel):
    guild_id = BigIntegerField(primary_key=True)
    owner_id = BigIntegerField(null=False)
    prefix = TextField(default="+", null=False)
    games_category = BigIntegerField(null=True)
    spectator_roles = ArrayField(BigIntegerField, null=True, index=False)
    enabled_games = IntegerField()
    referee_role = BigIntegerField(null=True)
    role_allow_startgames = BigIntegerField(null=True)
    booster_perks = BooleanField(default=False)
    commands_disabled_channels = ArrayField(
        BigIntegerField, null=True, index=False
    )
    logs_enabled = BooleanField(default=True)
    log_channel = BigIntegerField(null=True)

    class Meta:
        db_table = 'guilds'

    @classmethod
    def get_settings(cls, guild_id):
        try:
            return Guild.get(guild_id=guild_id)
        except Guild.DoesNotExist:
            return

    @classmethod
    def using_id(cls, guild_id):
        return Guild.get(guild_id=guild_id)

    def enabled_games_emotes(self):
        game_types = {
            1 << 0: "<:uno:594231154098438153>",  # Uno
            1 << 1: "<:connectfour:594231155172179985>",  # Connect4
            1 << 2: "<:tictactoe:594231153830133761>",  # TicTacToe
            1 << 3: "<:hangman:594231153914019840>",  # Hangman
            # 1 << 4: "2048", #2048
            # 1 << 5: "<:trivia:594231155012665354>", #Trivia
        }

        if self.enabled_games == 0:
            return ['`None`']

        games = []

        for i in range(10):
            if self.enabled_games & 1 << i:
                games.append(game_types[1 << i])

        return games

    def disabled_games_emotes(self):
        game_types = {
            1 << 0: "<:uno:594231154098438153>",  # Uno
            1 << 1: "<:connectfour:594231155172179985>",  # Connect4
            1 << 2: "<:tictactoe:594231153830133761>",  # TicTacToe
            1 << 3: "<:hangman:594231153914019840>",  # Hangman
            # 1 << 4: "2048", #2048
            # 1 << 5: "<:trivia:594231155012665354>", #Trivia
        }

        games = []

        for i in range(len(game_types)):
            if not self.enabled_games & 1 << i:
                games.append(game_types[1 << i])

        return games

    def enabled_games_strings(self):
        game_types = {
            1 << 0: "Uno",
            1 << 1: "Connect4",
            1 << 2: "TicTacToe",
            1 << 3: "HangMan",
            # 1 << 4: "2048",
            # 1 << 5: "Trivia",
        }

        games = []

        for i in range(10):
            if self.enabled_games & 1 << i:
                games.append(game_types[1 << i])

        return games

    def check_if_listed(self, game, check_type):
        game_types = {
            "uno": 1 << 0,  # Uno
            'c4': 1 << 1,  # Connect4
            'ttt': 1 << 2,  # TicTacToe
            'hm': 1 << 3,  # Hangman
            # '2048': 1 << 4, #2048
            # 'trivia': 1 << 5, #Trivia
        }
        if check_type == 'enabled':
            if self.enabled_games & game_types[game]:
                return True
            else:
                return False
        if check_type == 'disabled':
            if not self.enabled_games & game_types[game]:
                return True
            else:
                return False
