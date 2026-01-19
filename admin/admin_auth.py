# admin/admin_auth.py
from functools import wraps
from flask import request, Response
from config import Config  # Import the new config

def require_admin_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != Config.ADMIN_USERNAME or auth.password != Config.ADMIN_PASSWORD:
            return Response(
                "Admin access required",
                401,
                {"WWW-Authenticate": 'Basic realm="Admin Login"'}
            )
        return f(*args, **kwargs)
    return decorated