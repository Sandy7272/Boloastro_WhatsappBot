from flask import Blueprint, request, redirect, session, render_template_string

auth_bp = Blueprint("auth", __name__, url_prefix="/admin")

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
<title>Admin Login</title>
<style>
body{font-family:Arial;background:#f4f6f8;padding:50px}
.box{background:white;padding:30px;width:300px;margin:auto;border-radius:8px}
input{width:100%;padding:10px;margin:10px 0}
button{padding:10px;width:100%;background:#007bff;color:white;border:none}
</style>
</head>
<body>
<div class="box">
<h2>Admin Login</h2>
<form method="POST">
<input type="password" name="password" placeholder="Enter Admin Password" required>
<button>Login</button>
</form>
</div>
</body>
</html>
"""


ADMIN_PASSWORD = "boloastro123"   # change later


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/analytics")

    return render_template_string(HTML_LOGIN)


@auth_bp.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin/login")
