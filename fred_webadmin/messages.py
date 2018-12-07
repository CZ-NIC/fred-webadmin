#
# Copyright (C) 2014-2018  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

'''
Simplified messages from Django messages framework
'''

import cherrypy

from fred_webadmin import config

__all__ = (
    'add_message', 'get_messages',
    'get_level', 'set_level',
    'debug', 'info', 'success', 'warning', 'error',
)

DEBUG = 10
INFO = 20
SUCCESS = 25
WARNING = 30
ERROR = 40

DEFAULT_TAGS = {
    DEBUG: 'debug',
    INFO: 'info',
    SUCCESS: 'success',
    WARNING: 'warning',
    ERROR: 'error',
}

MESSAGES_SESSION_KEY = 'messages_module'


class MessageFailure(Exception):
    pass


class Message(object):
    """
    Represents an actual message that can be stored in any of the supported
    storage classes (typically session- or cookie-based) and rendered in a view
    or template.
    """

    def __init__(self, level, message):
        self.level = int(level)
        self.message = message

    def _get_string_level(self):
        return DEFAULT_TAGS.get(self.level, '')
    string_level = property(_get_string_level)

    def __unicode__(self):
        return self.message


def add_message(level, message):
    """
    Adds a message to the session using the 'messages' app.
    """
    if int(level) < get_level():  # don't record levels under current level
        return
    if cherrypy.session.get(MESSAGES_SESSION_KEY) is None:
        cherrypy.session[MESSAGES_SESSION_KEY] = []
    cherrypy.session[MESSAGES_SESSION_KEY].append(Message(level, message))


def get_messages(delete=True):
    """
    Returns the message list if it exists or emtpy list. Also deletes messages from the session, unless
    delete is set to False
    """
    messages = cherrypy.session.get(MESSAGES_SESSION_KEY)
    if delete:
        cherrypy.session[MESSAGES_SESSION_KEY] = []
    if messages is not None:
        return messages
    else:
        return []


def get_level():
    """
    Returns the minimum level of messages to be recorded.

    The default level is the ``MESSAGE_LEVEL`` setting. If this is not found,
    the ``INFO`` level is used.
    """
    return getattr(config, 'messages_level', None) or INFO


def set_level(level):
    """
    Sets the minimum level of messages to be recorded.

    If set to ``None``, the default level will be used (see the ``get_level``
    method).
    """
    config.messages_level = level


def debug(message):
    """
    Adds a message with the ``DEBUG`` level.
    """
    add_message(DEBUG, message)


def info(message):
    """
    Adds a message with the ``INFO`` level.
    """
    add_message(INFO, message)


def success(message):
    """
    Adds a message with the ``SUCCESS`` level.
    """
    add_message(SUCCESS, message)


def warning(message):
    """
    Adds a message with the ``WARNING`` level.
    """
    add_message(WARNING, message)


def error(message):
    """
    Adds a message with the ``ERROR`` level.
    """
    add_message(ERROR, message)
