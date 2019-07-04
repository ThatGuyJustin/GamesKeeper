#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import click
import copy
import gevent
import logging
import os
import signal
import subprocess
import yaml

from gevent import monkey; monkey.patch_all()
from gevent import pywsgi
from werkzeug.serving import run_with_reloader
from yaml import load

from GamesKeeper.db import init_db
from GamesKeeper.web import GamesKeeper


@click.group()
def cli():
    logging.getLogger().setLevel(logging.INFO)

@cli.command()
@click.option('--reloader/--no-reloader', '-r', default=False)
def serve(reloader):
    def run():
        pywsgi.WSGIServer(('0.0.0.0', 8686), GamesKeeper.app).serve_forever()

    if reloader:
        run_with_reloader(run)
    else:
        run()

if __name__ == '__main__':
    cli()