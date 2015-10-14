from arche.views.base import BaseView
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPFound

from arche_usertags.interfaces import IUserTags


class UserTagsView(BaseView):
    tag = None
    actions = {'+': 'add',
               '-': 'remove',
               'list': 'list'}

    @reify
    def adapter(self):
        return self.request.registry.getAdapter(self.context, IUserTags, name = self.tag)

    def __call__(self):
        action_callable = self.get_action()
        return action_callable()

    def get_action(self):
        try:
            tag = self.request.subpath[0]
            action = self.request.subpath[1]
        except IndexError:
            raise HTTPNotFound("No such subpath")
        if not self.tag or self.tag != tag:
            raise HTTPNotFound("No such tag: %r" % tag)
        try:
            action_name = self.actions[action]
        except KeyError:
            raise HTTPNotFound("No such action")
        #Check userid
        if self.request.authenticated_userid is None:
            raise HTTPForbidden("Must be authenticated")
        return getattr(self, action_name)

    def add(self):
        if self.adapter.add_perm and not self.request.has_permission(self.adapter.add_perm, self.context):
            raise HTTPForbidden("Not allowed")
        self.adapter.add(self.request.authenticated_userid)
        return self._return_success()

    def remove(self):
        self.adapter.remove(self.request.authenticated_userid)
        return self._return_success()

    def list(self):
        return {'items': tuple(self.adapter)}

    def _return_success(self):
        if self.request.is_xhr:
            user_in = self.request.authenticated_userid in self.adapter
            return {'status': 'success',
                    'user_in': user_in,
                    'total': len(self.adapter),
                    'toggle_url': user_in and self.adapter.remove_url(self.request) or self.adapter.add_url(self.request)}
        return HTTPFound(location = self.request.resource_url(self.context))
