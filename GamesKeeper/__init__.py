# -*- coding: utf-8 -*-
from collections import namedtuple

import yaml
with open("config.yaml", 'r') as config_yml:
    base_config = yaml.safe_load(config_yml)

bot_config = namedtuple("config", base_config.keys())(*base_config.values())

YES_EMOJI = ':yes:593829710941913098' 
NO_EMOJI = ':no:593829710786723850'
YES_EMOJI_ID = 593829710941913098
NO_EMOJI_ID = 593829710786723850