from flask import Flask, render_template, url_for, request, session, redirect, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from mp3_tagger import MP3File
from datetime import date
import os
import random
import hashlib
import re

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["UPLOAD_FOLDER"] = "static/uploads/"
app.config["SECRET_KEY"] = os.urandom(24)
db = SQLAlchemy(app)
ALLOWED_EXTENSIONS = set(['mp3', 'wav','ogg'])

def matched(pattern, string):
    num = 0
    pattern = pattern.lower().split(" ")
    string = string.lower().split(" ")
    for i in pattern:
        if i in string:
            num += 1
    if num >= 1:
        return True
    return False
    
    
    
def todays_date():
    month = ""
    date_now = date.today()
    if date_now.month == 1:
        month = "January"
    elif date_now.month == 2:
        month = "February"
    elif date_now.month == 3:
        month = "March"
    elif date_now.month == 4:
        month = "April"
    elif date_now.month == 5:
        month = "May"
    elif date_now.month == 6:
        month = "June"
    elif date_now.month == 7:
        month = "July"
    elif date_now.month == 8:
        month = "August"
    elif date_now.month == 9:
        month = "September"
    elif date_now.month == 10:
        month = "October"
    elif date_now.month == 11:
        month = "November"
    elif date_now.month == 12:
        month = "December"
    return f"{month} {date_now.day}, {date_now.year}"
    
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class Song(db.Model):
    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    artist_name = db.Column(db.Text, nullable=False)
    file_name = db.Column(db.Text, nullable=False)
    song_title = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.String(30), nullable=False, default=todays_date())
    comments = db.Column(db.Text, nullable=False)
    audio_type = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"id:{self.id}, artist:{self.artist_name}, song:{self.song_title}"

class User(db.Model):
    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    songs = db.relationship('Song', backref='user', lazy=True)

    def __repr__(self):
        return f"{self.fullname}"
        
@app.route('/home')      
@app.route("/")
def index():
    audios = Song.query.all()
    new_audios = audios
    if len(audios) != 0 and audios != None:
        random.shuffle(audios)
    return render_template("index.html",  new_audios=new_audios,audios = audios)

@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

    
@app.route("/upload", methods=["GET", "POST"])
def upload():
    message = None
    new_audios = Song.query.all()
    if g.user:
        if request.method == "POST":
            file = request.files["song_file"]
            if file and allowed_file(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) 
                    song = MP3File(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                    song.song = request.form['song_title']
                    song.artist = request.form['artist_name']
                    comments = request.form['comments']
                    audio_type = request.form['type'].lower()
                    user = User.query.filter_by(username=session['user']).first()
                    db_song = Song(user_id=user.id,audio_type=audio_type,comments=comments,artist_name=song.artist, file_name=filename, song_title=song.song)
                    db.session.add(db_song)
                    db.session.commit()
                    return render_template("upload.html", new_audios=new_audios, message=file.filename)
                except:
                    return render_template("upload.html",  new_audios=new_audios)

        return render_template("upload.html", message=None, new_audios=new_audios)
    return redirect(url_for('sign_in'))


@app.route('/signin', methods=["GET", "POST"])
def sign_in():
    if not g.user:
        if request.method == "POST":
            session.pop('user', None)
            username = request.form["username"]
            password = request.form["password"]
            user = User.query.filter_by(username=username).first()
            if(user != None):
                if hashlib.md5(password.encode("utf-8")).hexdigest() == user.password:
                    session['user'] = request.form['username']
                    return redirect(url_for('index'))
                else:
                    return render_template('signin.html', message="Invalid password. Try again")
            else:
                return render_template('signin.html', message="Account does not Exist.")
        return render_template('signin.html', message=None)
    return redirect(url_for('index'))


@app.route('/signup', methods=["GET", "POST"])
def sign_up():
    if not g.user:
        if request.method == "POST":
            fullname = request.form['fullname']
            username = request.form['username']
            password = hashlib.md5(request.form['password'].encode("utf-8")).hexdigest()
            user = User.query.filter_by(username=username).first()
            if(user == None):
                db_user = User(fullname=fullname, username=username, password=password)
                db.session.add(db_user)
                db.session.commit()
                session['user'] = username
                return redirect(url_for('index'))
            return render_template('signup.html', message="Username already exists. Try another.")
        return render_template('signup.html')
    return redirect(url_for('index'))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("sign_in"))

@app.route("/songs", methods=["POST", "GET"])
def search():
    lat_audios = Song.query.all()
    if request.method == "POST":
        s_search = []
        s_name = request.form["s_name"]
        songs = Song.query.all()
        for song in songs:
            if(matched(s_name, song.song_title)):
                s_search.append(song)
        return render_template("songs.html",lat_audios=lat_audios,songs=s_search)
    return render_template("songs.html", songs=[], lat_audios=lat_audios)

@app.route("/view/<string:song_id>")
def view(song_id):
    song_id = int(song_id)
    lat_songs = Song.query.all()
    usr = Song.query.filter_by(id=song_id).first()
    usr = usr.user.username
    others = User.query.filter_by(username=usr).first()
    if(len(others.songs) > 0):
        random.shuffle(others.songs)
        others = others.songs  
    song = Song.query.filter_by(id=song_id).first()
    return render_template("view.html",lat_songs=lat_songs,others=others,song=song)

@app.route('/about')
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
