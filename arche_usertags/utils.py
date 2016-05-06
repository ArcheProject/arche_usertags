from arche.security import PERM_VIEW
from pyramid.security import Authenticated
from six import string_types
from zope.interface import Interface

from arche_usertags.models import UserTags


def add_usertag(config, name, iface,
                catalog_index = None,
                add_perm = Authenticated,
                view_perm = PERM_VIEW):
    assert isinstance(name, string_types)
    assert issubclass(iface, Interface)
    #assert isinstance(iface, Interface)
    #Create an adapter class
    class _UserTags(UserTags):
        pass
    _UserTags.name = name
    _UserTags.catalog_index = catalog_index
    _UserTags.add_perm = add_perm
    _UserTags.view_perm = view_perm
    config.registry.registerAdapter(_UserTags, required = (iface,), name = _UserTags.name)
    #Create a view
    # class _UserTagsView(UserTagsView):
    #     tag = name
    # config.add_view(_UserTagsView,
    #                 context = iface,
    #                 name = _UserTags.view_name,
    #                 permission = view_perm,
    #                 renderer = 'json')

def includeme(config):
    config.add_directive('add_usertag', add_usertag)
