# routes/auth_routes.py

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from services.auth_service import (
    login_user,
    logout_user,
    login_required
)

# =========================================================
# BLUEPRINT
# =========================================================
auth_bp = Blueprint(
    "auth",
    __name__
)


# =========================================================
# LOGIN
# =========================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    # =====================================================
    # SI YA HAY SESIÓN
    # =====================================================
    if "user_id" in session:

        return redirect(
            url_for("root")
        )

    # =====================================================
    # POST LOGIN
    # =====================================================
    if request.method == "POST":

        username = (
            request.form
            .get("username", "")
            .strip()
        )

        password = (
            request.form
            .get("password", "")
            .strip()
        )

        result = login_user(
            username,
            password
        )

        if not result["success"]:

            flash(
                result["message"],
                "danger"
            )

            return render_template(
                "login.html"
            )

        flash(
            f"Bienvenido {result['user']['username']}",
            "success"
        )

        return redirect(
            url_for("root")
        )

    # =====================================================
    # GET
    # =====================================================
    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================
@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Sesión cerrada.",
        "info"
    )

    return redirect(
        url_for("auth.login")
    )