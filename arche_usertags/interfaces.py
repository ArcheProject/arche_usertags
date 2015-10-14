from pyramid.interfaces import IDict
from zope.interface import Attribute
from zope.interface import Interface


class IUserTags(Interface):
    """ Adapter for things that can have usertags.
        Behaves like a set with some extra functions that views might need
        to interact with tags.
    """
    name = Attribute("Name of the tag - same as adapter name")

    def add(userid, notify = True):
        """ """

    def remove(userid, notify = True):
        """ """

    def add_url(request):
        """ """

    def remove_url(request):
        """ """

    def action_url(request, action):
        """ """
