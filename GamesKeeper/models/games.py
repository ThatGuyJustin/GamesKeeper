from GamesKeeper.db import BaseModel
from peewee import BigIntegerField, IntegerField, TextField, BooleanField, DoesNotExist
from playhouse.postgres_ext import BinaryJSONField, ArrayField

class GamesTypes(object):
    UNO = 0
    CONNECT_FOUR = 1
    TIC_TAC_TOE = 2
    HANGMAN = 3

@BaseModel.register
class Games(BaseModel):
    Types = GamesTypes

    guild_id = BigIntegerField(null=False)
    game_channel = BigIntegerField(null=True, default=None)
    players = ArrayField(BigIntegerField, null=True, index=False)
    type_ = IntegerField(db_column='type')
    turn_count = IntegerField(null=True, default=0)
    ended = BooleanField(default=False)
    winner = BigIntegerField(null=True)
    cards_played = IntegerField(default=0)
    cards_drawn = IntegerField(default=0)
    phrase = TextField(null=True)
    guesses_correct = IntegerField(default=0)
    guesses_incorrect = IntegerField(default=0)
    questions_answered = IntegerField(default=0)
    trivia_category = TextField(null=True)

    class Meta:
        db_table = 'games'
    
    @classmethod
    def with_id(cls, game_id):
        return Games.get(id=game_id)
    
    @classmethod
    def start(cls, event, game_channel, players, game_type):
        return cls.create(
            guild_id = event.guild.id,
            game_channel = game_channel,
            players = [x.id for x in players],
            type_= game_type,
        )

