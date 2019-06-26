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


# Prefix text
# Games Category int(or big int, idk how b1nzy stored it)
# Spectator Roles list(int) ^ ^ ^ ^
# Enabled Games binary number
# Referee Role int Same as above
# CanStartGames Role int Same as above
# boosterPerks boolean(TBD on what exactly that does)
