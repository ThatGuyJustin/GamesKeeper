from GamesKeeper.db import BaseModel
from GamesKeeper.models.guild import Guild
from peewee import BigIntegerField, IntegerField, TextField, BooleanField, DoesNotExist
from playhouse.postgres_ext import BinaryJSONField, ArrayField
from disco.types.message import MessageEmbed
from datetime import datetime, timedelta

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
        num_str = {
            0: 'Uno',
            1: 'Connect Four',
            2: 'Tic-Tac-Toe',
            3: 'Hangman'
        }

        guild = Guild.using_id(event.guild.id)
        
        game = cls.create(
            guild_id = event.guild.id,
            game_channel = game_channel,
            players = [x.id for x in players],
            type_= game_type,
        )

        if guild.log_channel and guild.logs_enabled:
            embed = MessageEmbed()
            
            player_list = []
            for x in players:
                player_list.append('`*` {x} | `{x.id}`'.format(x=x))
            
            game_info = [
                '**Game**: {}'.format(num_str.get(game_type)),
                '**Channel**: <#{channel}> (`{channel}`)'.format(channel=game.game_channel),
                '**ID**: {}'.format(game.id)
            ]
            embed.add_field(name='Players »', value='\n'.join(player_list))
            embed.add_field(name='Game Info »', value='\n'.join(game_info))
            embed.set_footer(text='Started By {}'.format(event.author), icon_url=event.author.get_avatar_url())
            embed.timestamp = datetime.utcnow().isoformat()

            event.guild.channels.get(guild.log_channel).send_message(embed=embed)

        return
    
    def end_c4(self, data):
        pass
    
    def end_uno(self, data):
        pass
    
    def end_ttt(self, data):
        pass
    
    def end_hm(self, data):
        pass

class UnoRules(object):
    jump_in = 1 << 0 
    stack_draws = 1 << 1
    seven_swap = 1 << 2 
    super_swap = 1 << 3
    cancel_skip = 1 << 4
    special_multiplay = 1 << 5
    trains = 1 << 6
    endless_draw = 1 << 7
    num = {
        1 << 0: 'Jump In',
        1 << 1: 'Stack Draws',
        1 << 2: 'Seven Swap',
        1 << 3: 'Super Swap',
        1 << 4: 'Cancel Skip',
        1 << 5: 'Special Multiplay',
        1 << 6: 'Trains',
        1 << 7: 'Endless Draw',
    }


@BaseModel.register
class Users(BaseModel):
    UnoRules = UnoRules

    id = BigIntegerField(primary_key=True)
    cards_drawn = IntegerField(default=0)
    cards_placed = IntegerField(default=0)
    uno_rules = IntegerField(default=0)
    access_token = TextField(default=None)
    refresh_token = TextField(default=None)
    admin = BooleanField(default=False)

    class Meta:
        db_table = 'users'

    @classmethod
    def with_id(cls, user_id):
        return Users.get(id=user_id)
    
    def get_enabled(self):
        rules = []

        if self.uno_rules == 0:
            return []
        
        for i in range(len(UnoRules.num)):
            if self.uno_rules & 1 << i:
                rules.append(1 << i)
        
        return rules

    def get_enabled_rules(self):
        rules = []

        if self.uno_rules == 0:
            return []
        
        for i in range(len(UnoRules.num)):
            if self.uno_rules & 1 << i:
                rules.append(UnoRules.num[1 << i])
        
        return rules
    
    def int_to_type(self, int_):
        types = {
            1: UnoRules.jump_in,
            2: UnoRules.stack_draws,
            3: UnoRules.seven_swap,
            4: UnoRules.super_swap,
            5: UnoRules.cancel_skip,
            6: UnoRules.special_multiplay,
            7: UnoRules.trains,
            8: UnoRules.endless_draw,
        }
        return types.get(int_, None)