# -*- coding: utf-8 -*-
import logging
import os; os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
import yaml

from flask import Flask, g, session, send_from_directory
from holster.flask_ext import Holster
from yaml import load

from GamesKeeper.models.games import Users
from GamesKeeper.db import init_db

from GamesKeeper.views.auth import auth
from GamesKeeper import bot_config, get_client
from GamesKeeper.models.games import Users
# from GamesKeeper.views.dashboard import dashboard
# from GamesKeeper.views.guilds import guilds
from GamesKeeper.views.users import users
# from GamesKeeper.views.donation import donation


GamesKeeper = Holster(Flask(__name__))
# logging.getLogger('peewee').setLevel(logging.DEBUG)


GamesKeeper.app.register_blueprint(auth)
GamesKeeper.app.logger_name = 'Web'
GamesKeeper.app.secret_key = bot_config.web['SECRET_KEY']
GamesKeeper.app.discord = get_client()
# GamesKeeper.app.register_blueprint(dashboard)
GamesKeeper.app.register_blueprint(users)

@GamesKeeper.app.before_first_request
def before_first_request():
    init_db()

    with open('config.yaml', 'r') as f:
        data = load(f, Loader=yaml.UnsafeLoader)

    GamesKeeper.app.config.update(data['web'])
    GamesKeeper.app.secret_key = bot_config.web['SECRET_KEY']
    GamesKeeper.app.config['token'] = data.get('token')

@GamesKeeper.app.before_request
def check_auth():
    g.user = None
    g.data = None

    if 'uid' in session:
        g.user = Users.with_id(session['uid'])
    if 'data' in session:
        g.data = session['data']


@GamesKeeper.app.after_request
def save_auth(response):
    if g.user and 'uid' not in session:
        session['uid'] = g.user.id
    elif not g.user and 'uid' in session:
        del session['uid']
    
    if g.data and 'data' not in session:
        session['data'] = g.data
    elif not g.data and 'data' in session:
        del session['data']

    return response


@GamesKeeper.app.context_processor
def inject_data():
    return dict(
        user=g.user,
    )
