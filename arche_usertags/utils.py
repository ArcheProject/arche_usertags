from arche.security import PERM_VIEW
from pyramid.security import Authenticated
from six import string_types
from zope.interface import Interface

from arche_usertags.models import UserTags


def add_usertag(config, name, iface,
                catalog_index = None,
                add_perm = Authenticated,
                view_perm = PERM_VIEW,
                add_perm_callback = None,
                view_perm_callback = None):
    assert isinstance(name, string_types)
    assert issubclass(iface, Interface)
    #Create an adapter class
    class _UserTags(UserTags):
        pass
    _UserTags.name = name
    _UserTags.catalog_index = catalog_index
    _UserTags.add_perm = add_perm
    _UserTags.view_perm = view_perm
    _UserTags.add_perm_callback = add_perm_callback
    _UserTags.view_perm_callback = view_perm_callback
    config.registry.registerAdapter(_UserTags, required = (iface,), name = _UserTags.name)


def includeme(config):
    config.add_directive('add_usertag', add_usertag)
