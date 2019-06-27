from GamesKeeper.db import BaseModel
from peewee import BigIntegerField, IntegerField, TextField, BooleanField, DoesNotExist
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
            1 << 0: "<:uno:593494134870900736>", #Uno
            1 << 1: "<:connectfour:593494135378542592>", #Connect4
            1 << 2: "<:tictactoe:593494134535225344>", #TicTacToe
            1 << 3: "<:hangman:593494133738438656>", #Hangman
            1 << 4: "<:2048:593494134593945611>", #2048
            1 << 5: "<:trivia:593506394058260480>", #Trivia
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
            1 << 0: "<:uno:593494134870900736>", #Uno
            1 << 1: "<:connectfour:593494135378542592>", #Connect4
            1 << 2: "<:tictactoe:593494134535225344>", #TicTacToe
            1 << 3: "<:hangman:593494133738438656>", #Hangman
            1 << 4: "<:2048:593494134593945611>", #2048
            1 << 5: "<:trivia:593506394058260480>", #Trivia
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
            1 << 4: "2048",
            1 << 5: "Trivia",
        }

        games = []

        for i in range(10):
            if self.enabled_games & 1 << i:
                games.append(game_types[1 << i])
        
        return games
    
    def check_if_listed(self, game, check_type):
        game_types = {
            "uno": 1 << 0, #Uno
            'c4': 1 << 1, #Connect4
            'ttt': 1 << 2, #TicTacToe
            'hm': 1 << 3, #Hangman
            '2048': 1 << 4, #2048
            'trivia': 1 << 5, #Trivia
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

# Prefix text
# Games Category int(or big int, idk how b1nzy stored it)
# Spectator Roles list(int) ^ ^ ^ ^
# Enabled Games binary number
# Referee Role int Same as above
# CanStartGames Role int Same as above
# boosterPerks boolean(TBD on what exactly that does)
