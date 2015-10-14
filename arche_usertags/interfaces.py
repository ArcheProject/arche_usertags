from pyramid.interfaces import IDict
from zope.interface import Attribute


class IUserTags(IDict):
    """ Adapter for things that can have usertags.
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
