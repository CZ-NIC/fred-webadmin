#!/usr/bin/python
# -*- coding: utf-8 -*-

__all__ = ["DummyLogger"]

class DummyLogger(object):
    """
        Dummy SessionLogger. Never logs anything and never
        fails.
        Used to imitate normal logger, when you don't want to log anything (e.g.
        because you don't want to connect via Corba).
    """

    def start_session(self, *args, **kwargs):
        return True

    def set_common_property(self, *args, **kwargs):
        return

    def create_request(self, *args, **kwargs):
        return DummyLogRequest()

    def create_request_login(self, *args, **kwargs):
        return DummyLogRequest()
        
    def close_session(self, *args, **kwargs): 
        return True


class DummyLogRequest(object):
    def update(self, *args, **kwargs):
        return True

    def update_multiple(self, *args, **kwargs):
        return True

    def commit(self, *args, **kwargs):
        return True

