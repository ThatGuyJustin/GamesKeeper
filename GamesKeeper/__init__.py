# -*- coding: utf-8 -*-
from collections import namedtuple

import yaml
with open("config.yaml", 'r') as config_yml:
    base_config = yaml.safe_load(config_yml)

bot_config = namedtuple("config", base_config.keys())(*base_config.values())