try:
    import memcache
except ImportError as e:
    cache = None
else:
    from fred_webadmin import config
    cache = memcache.Client([config.memcached_server])
