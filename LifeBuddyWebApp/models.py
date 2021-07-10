from LifeBuddyWebApp import db, login_manager
from datetime import datetime, date
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin

from flask_script import Manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    image_file = db.Column(db.Text,nullable=False, default='default.jpg')
    password = db.Column(db.Text, nullable=False)
    user_timezone = db.Column(db.Text)
    permission = db.Column(db.Text)
    theme = db.Column(db.Text)
    time_stamp = db.Column(db.DateTime, default=datetime.now)
    posts = db.relationship('Post', backref='author', lazy=True)
    variable = db.relationship('Variables', backref='users_var', lazy=True)
    # track_inv = db.relationship('Tracking_inv', backref='updator_inv', lazy=True)


    def get_reset_token(self, expires_sec=1800):
        s=Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.id}', email:'{self.email}', permission:'{self.permission}', user_timezone: '{self.user_timezone}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    content = db.Column(db.Text)
    screenshot = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}','{self.date_posted}')"


class Variables(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    var_type = db.Column(db.Text)
    var_date = db.Column(db.Date, nullable=True)
    var_periodicity = db.Column(db.Text)
    var_value = db.Column(db.Text)
    var_unit = db.Column(db.Text)
    time_stamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # km_tracking_id = db.relationship('Tracking_inv', backref='update_inv_record', lazy=True)
    

    def __repr__(self):
        return f"Variables('{self.id}',var_type:'{self.var_type}'," \
        f"'var_date: {self.var_date}', var_value: '{self.var_value}', var_unit: '{self.var_unit}')"
    


