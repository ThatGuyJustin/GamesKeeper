from GamesKeeper.db import BaseModel
from peewee import BigIntegerField, IntegerField, TextField, BooleanField, DoesNotExist
from playhouse.postgres_ext import BinaryJSONField, ArrayField


@BaseModel.register
class Guild(BaseModel):
    Guild_id = BigIntegerField(primary_key=True)
    Owner_id = BigIntegerField(null=False)
    Prefix = TextField(default="!", null=False)
    GamesCategory = BigIntegerField(null=True)
    Spectators = ArrayField(BigIntegerField, null=True, index=False)
    EnabledGames = IntegerField()
    RefereeRole = BigIntegerField(null=False)
    StartGamesrole = BigIntegerField(null=False)
    BoosterPerks = BooleanField(default=False)

    class Meta:
        db_table = 'guilds'

    @classmethod
    def GetSettings(cls, guildid):
        try:
            return Guild.get(guild_id=guildid)
        except Guild.DoesNotExist:
            return


# Prefix text
# Games Category int(or big int, idk how b1nzy stored it)
# Spectator Roles list(int) ^ ^ ^ ^
# Enabled Games binary number
# Referee Role int Same as above
# CanStartGames Role int Same as above
# boosterPerks boolean(TBD on what exactly that does)
