import os
import logging
from urllib.parse import urlparse, urljoin

from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from jinja2 import TemplateNotFound
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)

app = Flask(__name__)   
app.config['SECRET_KEY'] = 'your_unique_and_secret_key_here'
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"

from passlib.hash import bcrypt

import database_manager as db


def is_safe_url(target):
    ref_url = urlparse(request.host_url)    
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "log_in"


class User(UserMixin):
    def __init__(self, row):
        self.id = row["User_ID"]
        self.username = row.get("Username")
        self.email = row.get("Email")



@login_manager.user_loader
def load_user(user_id):
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None
    row = db.get_user_by_id(uid)
    if not row:
        return None
    return User(row)


def hash_password(plain):
    return bcrypt.using(rounds=12).hash(plain)


def verify_password(plain, hashed):
    if not hashed:
        return False
    try:
        return (plain == hashed)
        #return bcrypt.verify(plain, hashed)
    except Exception:
        return False


@app.route("/index.html", methods=["GET"])
@app.route("/", methods=["GET", "POST"])
def index():
    attractions = db.get_listing_by_category(1)
    restaurants = db.get_listing_by_category(2)
    accommodations = db.get_listing_by_category(3)
    return render_template(
        "index.html",
        attractions=attractions,
        restaurants=restaurants,
        accommodations=accommodations,
    )


@app.route("/register", methods=["GET", "POST"])
@app.route("/register.html", methods=["GET", "POST"])
def register():
    ...
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not username or not email or not password:
            flash("Please fill all required fields", "danger")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for("register"))

        hashed = hash_password(password)
        user_id = db.create_user(username=username, email=email, password_hash=hashed)

        if not user_id:
            logger.info(
                "Registration failed: username=%s email=%s (duplicate?)",
                username,
                email,
            )
            flash("Username or email already in use", "danger")
            return redirect(url_for("register"))

        logger.info("Registered new user id=%s username=%s", user_id, username)
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("log_in"))

    return render_template("register.html")


@app.route("/log_in.html", methods=["GET", "POST"])
def log_in():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        if not username or not password:
            flash("Provide username and password", "danger")
            return redirect(url_for("log_in"))

        row = db.get_user_by_username(username)
        if not row:
            flash("Invalid credentials", "danger")
            return redirect(url_for("log_in"))

        # prefer password_hash only
        stored_hash = row.get("Password")
        if not stored_hash:
            logger.info(
                "Login attempt for user=%s but account missing password_hash", username
            )
            flash(
                "Account requires password reset. Please use password reset flow.",
                "danger",
            )
            return redirect(url_for("log_in"))

        if not verify_password(password, stored_hash):
            logger.info("Failed login for username=%s", username)
            flash("Invalid credentials", "danger")
            return redirect(url_for("log_in"))

        user = User(row)
        login_user(user, remember=remember)
        flash("Logged in successfully", "success")

        next_page = request.args.get("next")
        if not next_page or not is_safe_url(next_page):
            next_page = url_for("index")
        return redirect(next_page)

    return render_template("log_in.html")


@app.route("/log_out")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("index"))


@app.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    listing = db.get_listing_by_id(listing_id)
    images = db.get_images_for_listing(listing_id)
    posts = db.get_post_by_listing(listing_id)

    return render_template("listing.html", listing=listing, images=images, posts=posts)


from flask import render_template, abort
import os
from jinja2 import TemplateNotFound


@app.route("/register.html")
def register_html_redirect():
    return redirect(url_for("register"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
