# -*- coding: utf-8 -*-

# export FLASK_ENV=production|development


class Config(object):
    DEBUG = False
    TESTING = False
    TEMPLATES_AUTO_RELOAD = True


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
