import requests

from flask import Blueprint, g, jsonify, request, current_app
from GamesKeeper.models.guild import Guild
from GamesKeeper.models.games import Users
from GamesKeeper.util.decos import authed
from yaml import load

users = Blueprint('users', __name__, url_prefix='/api/users')

banned_users = [158722762951753728]

def refresh_token():
    data = {
        'client_id': current_app.config['discord']['CLIENT_ID'],
        'client_secret': current_app.config['discord']['CLIENT_SECRET'],
        'grant_type': g.user.refresh_token,
        'refresh_token': g.user.refresh_token,
        'redirect_uri': current_app.config['discord']['REDIRECT_URI'],
        'scope': 'identify guilds'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('https://discordapp.com/api/v7/oauth2/token', data=data, headers=headers)
    r.raise_for_status()
    return r.json()

def serialize_user():
    g.data['uno_rules'] = g.user.get_enabled_rules()
    g.data['admin'] = g.user.admin
    return g.data

def get_guilds():
    guilds = current_app.discord.api.users_guilds_get(g.user.access_token)
    for x in range(len(guilds)):
        guilds[x]['permissions'] = serialize_permissions(guilds[x]['permissions'])
    return guilds

@users.route('/@me')
@authed
def users_me():

    if g.user.id in banned_users:
        return 'Banned User', 403

    # return jsonify(dir(g))
    return jsonify(serialize_user())

@users.route('/@me/guilds')
@authed
def users_me_guilds():
    return jsonify(get_guilds())
    # if g.user.admin:
    #     guilds = list(Guild.select())
    # else:
    #     guilds = list(Guild.select(
    #         Guild,
    #         Guild.config['web'][str(g.user.user_id)].alias('role')
    #     ).where(
    #         (~(Guild.config['web'][str(g.user.user_id)] >> None))
    #     ))

    # return jsonify([
    #     guild.serialize() for guild in guilds
    # ])


def serialize_permissions(permissions_value):
    perms = {
        0: 'CREATE_INSTANT_INVITE',
        1: 'KICK_MEMBERS',
        2: 'BAN_MEMBERS',
        3: 'ADMINISTRATOR',
        4: 'MANAGE_CHANNELS',
        5: 'MANAGE_GUILD',
        6: 'ADD_REACTIONS',
        7: 'VIEW_AUDIT_LOG',
        8: 'VIEW_CHANNEL',
        9: 'SEND_MESSAGES',
        10: 'SEND_TTS_MESSAGES',
        11: 'MANAGE_MESSAGES',
        12: 'EMBED_LINKS',
        13: 'ATTACH_FILES',
        14: 'READ_MESSAGE_HISTORY',
        15: 'MENTION_EVERYONE',
        16: 'USE_EXTERNAL_EMOJIS',
        17: 'CONNECT',
        18: 'SPEAK',
        19: 'MUTE_MEMBERS',
        20: 'DEAFEN_MEMBERS',
        21: 'MOVE_MEMBERS',
        22: 'USE_VAD',
        23: 'PRIORITY_SPEAKER',
        24: 'CHANGE_NICKNAME',
        25: 'MANAGE_NICKNAMES',
        26: 'MANAGE_ROLES',
        27: 'MANAGE_WEBHOOKS',
        28: 'MANAGE_EMOJIS',
    }
    permissions = []
    for x in range(len(perms)):
        if permissions_value & 1 << x:
            permissions.append(perms.get(x))
    
    return permissions