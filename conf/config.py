from conf import config_default

__author__ = 'sunshine'


class Dict(dict):
    """
    支持x.y的操作
    """
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


def merge(defaults, override):
    r = dict()
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r


def to_dict(old_d):
    d = Dict()
    for k, v in old_d.items():
        d[k] = to_dict(v) if isinstance(v, dict) else v
    return d

configs = config_default.configs

try:
    from conf import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass

configs = to_dict(configs)