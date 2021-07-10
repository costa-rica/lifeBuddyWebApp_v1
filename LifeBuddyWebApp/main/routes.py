from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
from LifeBuddyWebApp import db, bcrypt, mail
from LifeBuddyWebApp.models import User, Variables
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from datetime import datetime, date, time
import datetime
from sqlalchemy import func, desc
import pandas as pd

main = Blueprint('main', __name__)

@main.route("/dashboard", methods=["GET","POST"])
@login_required
def dashboard():
    return render_template('dashboard.html')