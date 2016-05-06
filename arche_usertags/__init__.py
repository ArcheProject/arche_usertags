from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('arche_usertags')


def includeme(config):
    config.include('.utils')
    config.include('.views')
