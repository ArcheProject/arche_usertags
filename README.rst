Arche Usertags README
=====================

Annotation storage to build things like a "Like"-button and similar.
It's built on VoteIT's (www.voteit.se) old Like-functionality, but made modular and pluggable.

The implementation isn't suitable for really large scale
deployments where this data is expected to change very often.
(Like more than every second)
ZODB isn't built for lots of small write-actions.

Include it in your paster.ini configuration with:

.. code::

   arche.includes =
      arche_usertags


After that, it's possible to use the directive ``add_usertag``
to configure a storage and set up views.

name
   Internal ID for this. It's a good idea to use short lowercased strings.

iface
   Context interface to tie function to. Whatever context you wish it to work on.

catalog_index
   Signal repoze.catalog to update the following index.

add_perm
   Permission required for users to add something. (Authentication is always required.)

view_perm
   Permission required to view.

Example:
 
.. code::

   config.add_usertag('like', ILikeable,
                      catalog_index = 'like_userids',
                      add_perm = 'Add Like',
                      view_perm = 'View')

This will expose functionality in any ``ILikable`` context.
