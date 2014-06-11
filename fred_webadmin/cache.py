import memcache

from fred_webadmin import config

cache = memcache.Client([config.memcached_server])
