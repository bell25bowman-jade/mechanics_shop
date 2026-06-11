from flask_marshmallow import Marshmallow
from flask_caching import Cache
from flask_limiter import Limiter

limiter = Limiter(key_func=lambda: "global")  # Global rate limit
cache = Cache(config={'CACHE_TYPE': 'simple'})
ma = Marshmallow()