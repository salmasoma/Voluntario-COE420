from ast import Not
from cmath import log
from email.policy import default
from logging.handlers import RotatingFileHandler
from multiprocessing import Event
from operator import contains
from unicodedata import category
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.oracle import BLOB
import hashlib
import datetime
from datetime import date
from flask import jsonify
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from base64 import b64encode
import json
import base64
import smtplib 
import dateutil.parser
from zmq import EVENT_ACCEPT_FAILED
import numpy as np


app = Flask(__name__)
db = SQLAlchemy(app)


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///COE420db"
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

class User_roles(db.Model):
    user_role_id = db.Column(db.Integer, primary_key = True)
    role_name = db.Column(db.String(50))
    users = db.relationship('Users', backref='User_roles', lazy=True)

class Users (db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(25))
    location = db.Column(db.String(255))
    bio = db.Column(db.String(255))
    user_role = db.Column(db.Integer, db.ForeignKey('user_roles.user_role_id'), nullable=False)
    password = db.Column(db.String(255))
    profile_image = db.Column(BLOB)
    rating = db.Column(db.Integer)
    organizers = db.relationship('Organizer', backref='Users', lazy=True)
    volunteers = db.relationship('Volunteer', backref='Users', lazy=True)
    to_reviews = db.relationship('Reviews', foreign_keys='Reviews.to_user_id')
    from_reviews = db.relationship('Reviews', foreign_keys='Reviews.from_user_id')
    user_events = db.relationship('User_event', backref='Users', lazy=True)

    def get_id(self):
        return self.user_id

    def isOrg(self):
        return self.user_role

class Organizer (db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key = True)
    website = db.Column(db.String(255))
    contact_name = db.Column(db.String(75))
    total_events = db.Column(db.Integer)
    Organizer_category = db.relationship('Organizer_category', backref='Organizer', lazy=True)


class Volunteer (db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key = True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    emirates_id = db.Column(BLOB)
    birthdate = db.Column(db.Date)
    total_hours = db.Column(db.Integer)
    hours = db.relationship('Hours_category', backref='Volunteer', lazy=True)
    mailing = db.relationship('Mailing_list', backref='Volunteer', lazy=True)
    languages = db.relationship('Volunteer_language', backref='Volunteer', lazy=True)
    bookmarked = db.relationship('Bookmarked_events', backref='Volunteer', lazy=True)
    RegisteredVolunteers = db.relationship('Registered_volunteers', backref='Volunteer', lazy=True)


class Category (db.Model):
    category_id = db.Column(db.Integer, primary_key = True)
    category_name = db.Column(db.String(50))
    hours = db.relationship('Hours_category', backref='Category', lazy=True)
    mailing = db.relationship('Mailing_list', backref='Category', lazy=True)
    events = db.relationship('Events', backref='Category', lazy=True)
    Organizer_category = db.relationship('Organizer_category', backref='Category', lazy=True)

class Hours_category (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    volunteer_user_id = db.Column(db.Integer, db.ForeignKey('volunteer.user_id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'))
    hours = db.Column(db.Integer)

class Mailing_list (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    volunteer_user_id = db.Column(db.Integer, db.ForeignKey('volunteer.user_id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'))

class Language (db.Model):
    language_id = db.Column(db.Integer, primary_key = True)
    language_name = db.Column(db.String(50))
    languages = db.relationship('Volunteer_language', backref='Language', lazy=True)
    LanguageRequirements = db.relationship('Language_requirements', backref='Language', lazy=True)

class Volunteer_language (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    volunteer_user_id = db.Column(db.Integer, db.ForeignKey('volunteer.user_id'))
    language_id = db.Column(db.Integer, db.ForeignKey('language.language_id'))

class Event_status (db.Model):
    status_id = db.Column(db.Integer, primary_key = True)
    status_name = db.Column(db.String(50))
    events = db.relationship('Events', backref='Event_status', lazy=True)

class Events (db.Model):
    event_id = db.Column(db.Integer, primary_key = True)
    event_name = db.Column(db.String(50))
    event_description = db.Column(db.String(255))
    creation_date = db.Column(db.DateTime)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    location = db.Column(db.String(50))
    capacity = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'))
    events_status_id = db.Column(db.Integer, db.ForeignKey('event_status.status_id'))
    event_poster = db.Column(BLOB)
    hours = db.Column(db.Integer)
    lat = db.Column(db.Float)
    long = db.Column(db.Float)
    user_events = db.relationship('User_event', backref='Events', lazy=True)
    EventRequirement = db.relationship('Event_requirement', backref='Events', lazy=True)
    announcements = db.relationship('Announcements', backref='Events', lazy=True)
    bookmarked = db.relationship('Bookmarked_events', backref='Events', lazy=True)
    RegisteredVolunteers = db.relationship('Registered_volunteers', backref='Events', lazy=True)
    reviews = db.relationship('Reviews', backref='Events', lazy=True)

    def hashable(self):
        return {
            'event_id' : self.event_id,
            'event_name' : self.event_name,
            'event_description' : self.event_description,
            'creation_date' : self.creation_date,
            'start_date' : self.start_date,
            'end_date' : self.end_date,
            'location' : self.location,
            'capacity' : self.capacity,
            'category_id' : self.category_id,
            'events_status_id' : self.events_status_id,
            'event_poster' : self.event_poster,
            'hours' : self.hours,
            'lat' : self.lat,
            'long' : self.long,
        }


class Reviews (db.Model):
    review_id = db.Column(db.Integer, primary_key = True)
    from_user_id= db.Column(db.Integer, db.ForeignKey('users.user_id'))
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'))
    description = db.Column(db.Text)
    rating = db.Column(db.Integer)

class User_event (db.Model):
    user_event_id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'))

class Event_requirement (db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'), primary_key = True)
    age_limit = db.Column(db.Integer)
    location = db.Column(db.String(50))
    min_hours = db.Column(db.Integer)

class Announcements (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.DateTime)

class Language_requirements (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'))
    language_id = db.Column(db.Integer, db.ForeignKey('language.language_id'))

class Bookmarked_events (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    volunteer_user_id = db.Column(db.Integer, db.ForeignKey('volunteer.user_id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'))

class Volunteer_status (db.Model):
    status_id = db.Column(db.Integer, primary_key = True)
    status_name = db.Column(db.String(50))
    RegisteredVolunteers = db.relationship('Registered_volunteers', backref='Volunteer_status', lazy=True)

class Registered_volunteers (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    volunteer_user_id = db.Column(db.Integer, db.ForeignKey('volunteer.user_id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'))
    volunteer_status_id = db.Column(db.Integer, db.ForeignKey('volunteer_status.status_id'))

class Organizer_category (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    organizer_user_id = db.Column(db.Integer, db.ForeignKey('organizer.user_id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'))

admin = Admin(app, name='microblog', template_mode='bootstrap3')
admin.add_view(ModelView(Users, db.session))
admin.add_view(ModelView(User_roles, db.session))
admin.add_view(ModelView(Organizer, db.session))
admin.add_view(ModelView(Volunteer, db.session))
admin.add_view(ModelView(Reviews, db.session))
admin.add_view(ModelView(Category, db.session))
admin.add_view(ModelView(Hours_category, db.session))
admin.add_view(ModelView(Mailing_list, db.session))
admin.add_view(ModelView(Language, db.session))
admin.add_view(ModelView(Volunteer_language, db.session))
admin.add_view(ModelView(Event_status, db.session))
admin.add_view(ModelView(Events, db.session))
admin.add_view(ModelView(User_event, db.session))
admin.add_view(ModelView(Event_requirement, db.session))
admin.add_view(ModelView(Announcements, db.session))
admin.add_view(ModelView(Language_requirements, db.session))
admin.add_view(ModelView(Bookmarked_events, db.session))
admin.add_view(ModelView(Volunteer_status, db.session))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == "POST":
        #retrieve email and password feild
        email = request.form['email']
        password = hashlib.sha256(request.form['pass'].encode('utf-8')).hexdigest()
        #search for email
        user = Users.query.filter_by(email = email).first()
        #check if user exists
        if(user is None):
            error_msg = "Email does not exist, please sign up first!"
            return render_template("login.html", error_msg = error_msg)
        #verify password
        if(user.password == password):
            session["user_id"] = user.user_id
            print("///////",session['user_id'])
            #check user type
            login_user(user) #flask-login to save current user
            print("////logged in",current_user)
            print(session)
            if(user.user_role == 1):
                return redirect(url_for("dashboardVol",tab="dashboard"))
            else:
                return redirect(url_for("dashboardOrg",tab="dashboard"))
        else:
            error_msg = "Incorrect password!"
            return render_template("login.html", error_msg = error_msg)
    else:
        return render_template("login.html", error_msg = None)

@app.route("/registervolunteer",methods=['POST','GET'])
def registervolunteer():
    if request.method == "POST":
        email = request.form['email']
        #check if user email is already registered
        u = Users.query.filter_by(email = email).first()
        if(u is None):
            password = hashlib.sha256(request.form['password'].encode('utf-8')).hexdigest()
            first_name = request.form['fname']
            last_name = request.form['lname']
            phone = request.form['phone']
            date = datetime.datetime.strptime(request.form['birthdate'],'%Y-%m-%d')
            if(date.year+18 > date.today().year):
                return render_template("signupvolunteer.html", error_msg = "Sorry you must be 18 or older to sign up!")
            location = request.form['location']
            emiratesID = request.files['emiratesID']
            user = Users(email=email,phone=phone,location=location,user_role=1,password=password,rating=0)
            db.session.add(user)
            db.session.commit()
            volunteer = Volunteer(user_id = user.user_id, first_name=first_name, last_name=last_name,birthdate=date,emirates_id=emiratesID.read(),total_hours=0)
            db.session.add(volunteer)
            db.session.commit()
            session["user_id"] = user.user_id
            session["name"] = first_name + " " + last_name
            return redirect(url_for("profileVolunteer"))            
        else:
            return render_template("signupvolunteer.html", error_msg = "Email is already registered! Please sign in instead!")
    else:
        return render_template("signupvolunteer.html", error_msg = None)

@app.route("/volunteerprofile",methods=['POST','GET'])
def profileVolunteer():
    if request.method == "POST":
        if "user_id" in session:
            user_id = session["user_id"]
            user = Users.query.filter_by(user_id = user_id).first()
            user.bio = request.form['bio']
            user.profile_image = request.files['profileimg'].read()
            db.session.add(user)
            db.session.commit()
            langs = request.form.getlist('language')
            for l in langs:
                vol = Volunteer_language(volunteer_user_id=user_id,language_id = l)
                db.session.add(vol)
            db.session.commit()
            return render_template("login.html", error_msg = "Please sign in into your new account")
        else:
            return redirect(url_for("registervolunteer"))
    else:
        languages = Language.query.all()
        return render_template("createvolunteerprofile.html", name = session["name"], languages = languages)

@app.route("/registerorganizer",methods=['POST','GET'])
def registerorganizer():
    if request.method == "POST":
        email = request.form['email']
        #check if user email is already registered
        u = Users.query.filter_by(email = email).first()
        if(u is None):
            password = hashlib.sha256(request.form['password'].encode('utf-8')).hexdigest()
            contact_name = request.form['name']
            website = request.form['website']
            phone = request.form['phone']
            location = request.form['location']
            user = Users(email=email,phone=phone,location=location,user_role=2,password=password,rating=0)
            db.session.add(user)
            db.session.commit()
            organizer = Organizer(user_id = user.user_id, contact_name=contact_name, website=website,total_events=0)
            db.session.add(organizer)
            db.session.commit()
            session["user_id"] = user.user_id
            session["name"] = organizer.contact_name
            return redirect(url_for("profileOrganizer"))            
        else:
            return render_template("signuporganizer.html", error_msg = "Email is already registered! Please sign in instead!")
    else:
        return render_template("signuporganizer.html", error_msg = None)

@app.route("/organizerprofile",methods=['POST','GET'])
def profileOrganizer():
    if request.method == "POST":
        if "user_id" in session:
            user_id = session["user_id"]
            user = Users.query.filter_by(user_id = user_id).first()
            user.bio = request.form['bio']
            user.profile_image = request.files['profileimg'].read()
            db.session.add(user)
            db.session.commit()
            cat = request.form.getlist('category')
            for c in cat:
                org = Organizer_category(organizer_user_id=user_id,category_id = c)
                db.session.add(org)
            db.session.commit()
            return render_template("login.html", error_msg = "Please sign in into your new account")
        else:
            return redirect(url_for("registerorganizer"))
    else:
        categories = Category.query.all()
        return render_template("createorganizerprofile.html", name = session["name"], categories = categories)

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/contact',methods=['POST','GET'])
def contact():
    if request.method == "POST":
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']
        msg = {"fname": fname, "lname": lname, "email": email,"phone":phone,"msg": message}
        gmail_user = 'hamadspam1@gmail.com'
        gmail_password = 'hamad1234'
        sent_from = gmail_user
        to = ['salmasoma@gmail.com']
        subject = 'Application Message Request'
        body = msg['msg']

        email_text = """\
        From: %s
        To: %s
        Subject: %s

        %s
        """ % (sent_from, ", ".join(to), subject, body)
        try:
            smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            smtp_server.ehlo()
            smtp_server.login(gmail_user, gmail_password)
            smtp_server.sendmail(sent_from, to, email_text)
            smtp_server.close()
            flash ("Email sent successfully!")
            return render_template('contact.html')
        except Exception as ex:
            print ("Something went wrong….",ex)

        return render_template('contact.html')

    else:
        return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')



@app.route('/dashboardvol/<tab>',methods=['POST','GET'])
@login_required
def dashboardVol(tab):
    user = Users.query.filter_by(user_id = session['user_id']).first() #or current_user, but fine
    volunteer = Volunteer.query.filter_by(user_id = session['user_id']).first()
    events = Registered_volunteers.query.filter_by(volunteer_user_id = session['user_id']).all()
    events_details = []
    status = []
    month = [0,0,0,0,0,0,0,0,0,0,0,0]
    todays_date = date.today()
    year = todays_date.year
    announcements = []
    inprogress = []
    for e in events:
        event = Events.query.filter_by(event_id = e.event_id).first()
        if not(event.events_status_id == 2):
            inprogress.append(event)
        events_details.append(event)
        d = event.start_date
        if(d.year == year):
            month[d.month-1] += event.hours
        stat = Volunteer_status.query.filter_by(status_id = e.volunteer_status_id).first()
        status.append(stat.status_name)
        a = Announcements.query.filter_by(event_id = e.event_id).all()
        if(not (a == None)):
            for an in a:
                announcements.append(an)
    reviews = Reviews.query.filter_by(to_user_id = session['user_id']).all()
    total_reviews = len(reviews)
    category = Hours_category.query.filter_by(volunteer_user_id = session['user_id']).all()
    hours_category = [0,0,0,0,0,0,0]
    for c in category:
        ind = c.category_id-1
        hours_category[ind]=(c.hours)
    if user.profile_image:
        image = b64encode(user.profile_image).decode("utf-8")
    else:
        with open("static/img/avatar.png", "rb") as image_file:
            image = b64encode(image_file.read()).decode("utf-8")
    languages = Language.query.all()
    categories = Category.query.all()
    l = Volunteer_language.query.filter_by(volunteer_user_id = session['user_id']).all()
    c = Mailing_list.query.filter_by(volunteer_user_id = session['user_id']).all()
    user_lang = []
    user_cat = []
    for la in l:
        user_lang.append(la.language_id)
    for ca in c:
        user_cat.append(ca.category_id)
    
    registered = Registered_volunteers.query.filter_by(volunteer_user_id = session['user_id']).all()
    orgs = []
    review_img = []
    review_ev = []
    #for each registration
    for re in registered:
        #check if there is a review
        rev = Reviews.query.filter_by(event_id = re.event_id, from_user_id = session['user_id']).first()
        #if there is no review
        if (rev == None):
            #get event
            ev = Events.query.filter_by(event_id = re.event_id).first()
            #if event is completed
            if(ev.events_status_id == 2):
                review_ev.append(ev)
                #get associated organization
                user_Event = User_event.query.filter_by(event_id = re.event_id).first()
                o = Organizer.query.filter_by(user_id = user_Event.user_id).first()
                orgs.append(o)
                user_org = Users.query.filter_by(user_id = user_Event.user_id).first()
                if user_org.profile_image:
                    ig = b64encode(user_org.profile_image).decode("utf-8")
                else:
                    with open("static/img/avatar.png", "rb") as image_file:
                        ig = b64encode(image_file.read()).decode("utf-8")
                review_img.append(ig)

    datelimit = datetime.datetime.now()- datetime.timedelta(days=1)
    bookmark = []
    bo = Bookmarked_events.query.filter_by(volunteer_user_id=session['user_id']).all()
    for b in bo:
        e = Events.query.filter_by(event_id = b.event_id).first()
        if (datelimit > e.start_date):
            db.session.delete(b)
        else:
            bookmark.append(e)

    return render_template('dashboardvolunteer.html', inprogress = inprogress, tab=tab, user=user, volunteer=volunteer, events=events, total_reviews = total_reviews, hours_category=hours_category, events_details = events_details, status = status, month=month, image =image, announcements=announcements,languages=languages,user_lang=user_lang, categories = categories,user_cat=user_cat, orgs = orgs,review_img=review_img,review_ev=review_ev,bookmark=bookmark)

@app.route('/updatevol',methods=['POST','GET'])
@login_required
def updatevol():
    if (request.method == "POST"):
        user = Users.query.filter_by(user_id = session['user_id']).first()
        volunteer = Volunteer.query.filter_by(user_id = session['user_id']).first()
        update = False
        email = request.form.get("email")
        print(email)
        if(email != ""):
            user.email = email
            update = True
        phone = request.form.get("phone")
        print(phone)
        if(phone != ""):
            user.phone = phone 
            update = True            
        fname = request.form.get("fname")
        print(fname)
        if(fname != ""):
            volunteer.first_name = fname
            update = True
        lname = request.form.get("lname")
        print(lname)
        if(lname != ""):
            volunteer.last_name = lname 
            update = True
        location = request.form.get("location")
        print(location)
        if(location != "Select an Emirate"):
            user.location = location
            update = True
        password = request.form.get("password")
        print(password)
        if(password != "xxxx"):
            user.password = hashlib.sha256(request.form.get("password").encode('utf-8')).hexdigest()
            update = True
        image = request.files["file"]
        i = image.read()
        if(len(i) > 5):
            user.profile_image = i
            update = True

        if(update):
            db.session.commit()

    return "success"

@app.route('/postReview/<id>/<event>',methods=['POST','GET'])
@login_required
def postReview(id,event):
    if (request.method == "POST"):
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        r = Reviews(from_user_id = session['user_id'],to_user_id =id, event_id = event, rating=rating,description=comment)
        db.session.add(r)
        db.session.commit()

        #Compute rating
        rev = Reviews.query.filter_by(to_user_id =id).all()
        ratings = []
        for re in rev:
            ratings.append(re.rating)
        
        user = Users.query.filter_by(user_id = id).first()
        user.rating = np.mean(ratings)

        db.session.commit()

        return redirect(url_for("dashboardVol", tab= "rate"))

@app.route('/updatelang',methods=['POST','GET'])
@login_required
def updatelang():
    if (request.method == "POST"):
        checked = request.form.getlist('checked')
        new_lang = checked[0].split('|')
        new_lang.remove('')
        langs = Volunteer_language.query.filter_by(volunteer_user_id = session['user_id']).all()
        for l in langs:
            if l in new_lang:
                new_lang.remove(l)
            else:
                db.session.delete(l)
                db.session.commit()

        if(len(new_lang) > 0):
            for l in new_lang:
                vl = Volunteer_language(volunteer_user_id = session['user_id'], language_id = l)
                db.session.add(vl)
                db.session.commit()
    return "success"

@app.route('/updatemailing',methods=['POST','GET'])
@login_required
def updatemailing():
    if (request.method == "POST"):
        checked = request.form.getlist('checked')
        new_cat = checked[0].split('|')
        new_cat.remove('')
        cat = Mailing_list.query.filter_by(volunteer_user_id = session['user_id']).all()
        for c in cat:
            if c in new_cat:
                new_cat.remove(c)
            else:
                db.session.delete(c)
                db.session.commit()

        if(len(new_cat) > 0):
            for c in new_cat:
                ml = Mailing_list(volunteer_user_id = session['user_id'], category_id = c)
                db.session.add(ml)
                db.session.commit()
    return "success"

@app.route('/updatecat',methods=['POST','GET'])
@login_required
def updatecat():
    if (request.method == "POST"):
        checked = request.form.getlist('checked')
        new_cat = checked[0].split('|')
        new_cat.remove('')
        cat = Organizer_category.query.filter_by(organizer_user_id = session['user_id']).all()
        for c in cat:
            if c in new_cat:
                new_cat.remove(c)
            else:
                db.session.delete(c)
                db.session.commit()

        if(len(new_cat) > 0):
            for c in new_cat:
                oc = Organizer_category(organizer_user_id = session['user_id'], category_id = c)
                db.session.add(oc)
                db.session.commit()
    return "success"

@app.route('/dashboardorg/<tab>')
@login_required
def dashboardOrg(tab):
    user = Users.query.filter_by(user_id = session['user_id']).first()
    organizer = Organizer.query.filter_by(user_id = session['user_id']).first()
    events = User_event.query.filter_by(user_id = session['user_id']).all()
    totalEvents = len(events)
    volCount = 0
    event_details = []
    events_category = [0,0,0,0,0,0,0]
    month = [0,0,0,0,0,0,0,0,0,0,0,0]
    status = []
    todays_date = date.today()
    today_datetime = datetime.datetime.now()
    year = todays_date.year
    for e in events:
        v = Registered_volunteers.query.filter_by(event_id = e.event_id).all()
        volCount += len(v)
        ev = Events.query.filter_by(event_id = e.event_id).first()
        if(ev.events_status_id == 1 and ev.start_date < today_datetime):
            ev.events_status_id = 3
            db.session.commit()
        event_details.append(ev)
        events_category[ev.category_id-1] +=1
        stat = Event_status.query.filter_by(status_id = ev.events_status_id).first()
        status.append(stat.status_name)
        d = ev.start_date
        if(d.year == year):
            month[d.month-1] += 1
    reviews = Reviews.query.filter_by(to_user_id = session['user_id']).all()
    total_reviews = len(reviews)

    if user.profile_image:
        image = b64encode(user.profile_image).decode("utf-8")
    else:
        with open("static/img/avatar.png", "rb") as image_file:
            image = b64encode(image_file.read()).decode("utf-8")
    categories = Category.query.all()
    c = Organizer_category.query.filter_by(organizer_user_id = session['user_id']).all()
    user_cat = []
    for ca in c:
        user_cat.append(ca.category_id)
    eStatus = ["Pending","Completed","In Progress","Cancelled"]

    registered = []
    for e in events:
        l = Registered_volunteers.query.filter_by(event_id = e.event_id).all()
        for ev in l:
            registered.append(ev)

    vols = []
    review_img = []
    review_ev = []
    #for each registration
    for re in registered:
        #check if there is a review
        rev = Reviews.query.filter_by(event_id = re.event_id, from_user_id = session['user_id'],to_user_id = re.volunteer_user_id).first()
        #if there is no review
        if (rev == None):
            #get event
            ev = Events.query.filter_by(event_id = re.event_id).first()
            #if event is completed
            if(ev.events_status_id == 2):
                review_ev.append(ev)
                #get associated organization
                vo = Volunteer.query.filter_by(user_id = re.volunteer_user_id).first()
                vols.append(vo)
                user_vol = Users.query.filter_by(user_id = re.volunteer_user_id).first()
                if user_vol.profile_image:
                    ig = b64encode(user_vol.profile_image).decode("utf-8")
                else:
                    with open("static/img/avatar.png", "rb") as image_file:
                        ig = b64encode(image_file.read()).decode("utf-8")
                review_img.append(ig)
    #must add condition to check user type down the line to render correct page
    return render_template('dashboardorganizer.html', tab=tab,user = user, organizer = organizer, vols = vols, review_img = review_img, review_ev = review_ev, image = image, totalEvents = totalEvents, volCount = volCount,total_reviews=total_reviews,events_category=events_category,event_details=event_details,status=status,month=month,categories=categories,user_cat=user_cat,eStatus=eStatus)

@app.route('/updateorg',methods=['POST','GET'])
@login_required
def updateorg():
    if (request.method == "POST"):
        user = Users.query.filter_by(user_id = session['user_id']).first()
        organizer = Organizer.query.filter_by(user_id = session['user_id']).first()
        update = False
        email = request.form.get("email")
        if(email != ""):
            user.email = email
            update = True
        phone = request.form.get("phone")
        if(phone != ""):
            user.phone = phone 
            update = True            
        name = request.form.get("name")
        if(name != ""):
            organizer.contact_name = name
            update = True
        website = request.form.get("website")
        if(website != ""):
            organizer.website = website 
            update = True
        location = request.form.get("location")
        if(location != "Select an Emirate"):
            user.location = location
            update = True
        password = request.form.get("password")
        print(password)
        if(password != "xxxx"):
            user.password = hashlib.sha256(request.form.get("password").encode('utf-8')).hexdigest()
            update = True
        image = request.files["file"]
        i = image.read()
        if(len(i) > 5):
            user.profile_image = i
            update = True

        if(update):
            db.session.commit()

    return "success"

@app.route("/events")
@login_required
def displayEvents(text="", category=""):
    if current_user.profile_image:
        image = b64encode(current_user.profile_image).decode("utf-8")
    else:
         with open("static/img/avatar.png", "rb") as image_file:
            image = b64encode(image_file.read()).decode("utf-8")
    return render_template("displayEvent.html", events=Events.query.all(), len=len, str=str, categories = Category.query.all(), image=image)

@app.route("/loadevents", methods=["POST"])
def loadevents():
    keyword = request.form['search']
    print(keyword)

    namesearch = Events.query.filter(Events.event_name.like(f'%{keyword}%'));
    descsearch = Events.query.filter(Events.event_description.like(f'%{keyword}%'));

    query = namesearch.union(descsearch).limit(5);
    return jsonify({'htmlresponse':render_template('searchlist.html', events=query, len=len)})

@app.route("/filter/location/<location>", methods=['POST'])
def FilterByLocation(location):
    locs = [event.hashable() for event in Events.query.filter(Events.location.ilike(location))]
    return jsonify({
        'success':True,
        'count': len(locs),
        'events' : locs
    })

@app.route("/filter/rating/<int:r1>/<int:r2>", methods=['POST'])
def FilterByRating(r1, r2): #gets all ratings between two numbers
    locs = [event.hashable() for event in Events.query.all() if r1 <= event.user_events[0].Users.rating <= r2]
    return jsonify({
        'success':True,
        'count': len(locs),
        'events' : locs
    })
@app.route("/filter/category/", methods=['POST']) #we will pass category id?
def FilterByCategory(): #gets all ratings between two numbers
    data = tuple(int(k) for k,v in request.form.to_dict().items() if int(v)!=0)
    
    container = request.form.to_dict().values()

    total = sum(map(lambda x: int(x),container))

    if total == 0:
        locs = Events.query.all()
    else:
        locs = Events.query.filter(Events.category_id.in_(data)).all()

    return jsonify({'htmlresponse':render_template('response.html', events=locs, len=len)})


@app.route('/search',methods=['POST','GET'])
def search():
    if request.method == "POST":
        keyword = request.form.get("searched")

        words = keyword.split()

        org = []
        vol = []
        o_images = []
        v_images = []
        uv = []
        uo = []
        for w in words:
            o = Organizer.query.filter(Organizer.contact_name.contains(w)).all()
            if (not(o == None)):
                org = org + o
            v = Volunteer.query.filter_by(first_name = w).all()
            if (not(v == None)):
                vol = vol + v
            v = Volunteer.query.filter_by(last_name = w).all()
            if (not(v == None)):
                vol = vol + v

        for o in org:
            u = Users.query.filter_by(user_id = o.user_id).first()
            uo.append(u)
            if u.profile_image:
                image = b64encode(u.profile_image).decode("utf-8")
            else:
                with open("static/img/avatar.png", "rb") as image_file:
                    image = b64encode(image_file.read()).decode("utf-8")
            o_images.append(image)

        for v in vol:
            u = Users.query.filter_by(user_id = v.user_id).first()
            uv.append(u)
            if u.profile_image:
                image = b64encode(u.profile_image).decode("utf-8")
            else:
                with open("static/img/avatar.png", "rb") as image_file:
                    image = b64encode(image_file.read()).decode("utf-8")
            v_images.append(image)

        u = Users.query.filter_by(user_id = session['user_id']).first()
        if u.profile_image:
            image = b64encode(u.profile_image).decode("utf-8")
        else:
            with open("static/img/avatar.png", "rb") as image_file:
                image = b64encode(image_file.read()).decode("utf-8")
        dashboard = ""
        if u.user_role == 1:
            dashboard = "dashboardVol"
        else:
            dashboard = "dashboardOrg"

        return render_template("viewUsers.html", dashboard=dashboard,volunteers = vol, organizers = org, o_images = o_images, v_images = v_images, uv = uv, uo = uo, image = image)
    else:
        u = Users.query.filter_by(user_id = session['user_id']).first()
        if u.profile_image:
            image = b64encode(u.profile_image).decode("utf-8")
        else:
            with open("static/img/avatar.png", "rb") as image_file:
                image = b64encode(image_file.read()).decode("utf-8")
        dashboard = ""
        if u.user_role == 1:
            dashboard = "dashboardVol"
        else:
            dashboard = "dashboardOrg"
        return render_template("viewUsers.html", dashboard = dashboard, image=image, msg = "Please enter a search keyword to look for users!")

@app.route('/searchEvent',methods=['POST'])
def searchEvent():
    if request.method == "POST":
        text = request.form['search-text']
        category = request.form['category']
        displayEvents(text,category) #text as in post title? or post description?, category is fine
        #also what are you expecting to happen? redirection to displayEvents? if so try redirecting to the page.
        return render_template("search.html")
    else:
        return render_template("search.html")

@app.route('/volprofile')
@login_required
def volunteerProfile():
    user = Users.query.filter_by(user_id = session['user_id']).first()

    if current_user.profile_image:
        image = b64encode(current_user.profile_image).decode("utf-8")
    else:
         with open("static/img/avatar.png", "rb") as image_file:
            image = b64encode(image_file.read()).decode("utf-8")
    reviews = Reviews.query.filter_by(to_user_id = current_user.user_id).all()
    counts = [0,0,0,0,0]
    names = []
    pictures = []
    for r in reviews:
        counts[r.rating-1] += 1
        u = Users.query.filter_by(user_id = r.from_user_id).first()
        if (u.user_role == 1):
            v = Volunteer.query.filter_by(user_id = r.from_user_id).first()
            n = v.first_name + " " + v.last_name
            names.append(n)
        else:
            o = Organizer.query.filter_by(user_id = r.from_user_id).first()
            names.append(o.contact_name)
        if u.profile_image:
            i = b64encode(u.profile_image).decode("utf-8")
        else:
            with open("static/img/avatar.png", "rb") as image_file:
                i = b64encode(image_file.read()).decode("utf-8")
        pictures.append(i)
        
    percentage = [0,0,0,0,0]
    if(not (len(reviews) == 0 )):
        for i in range(5):
            percentage[i] = int((counts[i]/len(reviews))*100)
            percentage[i] = str(percentage[i])+"%"
    if current_user.rating == None:
        current_user.rating = 0
    rating = (current_user.rating/5)*100
    print(percentage)
    vol = Volunteer.query.filter_by(user_id = session['user_id']).first()

    return render_template("volProfile.html", user = user, vol = vol, img=image, reviews = reviews, totalReviews = len(reviews), counts = counts,percentage=percentage, rating=rating, names = names, pictures = pictures, page="own")

@app.route('/orgprofile')
@login_required
def organizerProfile():
    user = Users.query.filter_by(user_id = session['user_id']).first()

    if current_user.profile_image:
        image = b64encode(current_user.profile_image).decode("utf-8")
    else:
         with open("static/img/avatar.png", "rb") as image_file:
            image = b64encode(image_file.read()).decode("utf-8")
    if current_user.user_role != 1: #assuming there are organizers and volunteers only.
        reviews = Reviews.query.filter_by(to_user_id = current_user.user_id).all()
        counts = [0,0,0,0,0]
        names = []
        pictures = []
        events = User_event.query.filter_by(user_id = session['user_id']).all()
        totalEvents = len(events)
        for r in reviews:
            counts[r.rating-1] += 1
            u = Users.query.filter_by(user_id = r.from_user_id).first()
            if (u.user_role == 1):
                v = Volunteer.query.filter_by(user_id = r.from_user_id).first()
                n = v.first_name + " " + v.last_name
                names.append(n)
            else:
                o = Organizer.query.filter_by(user_id = r.from_user_id).first()
                names.append(o.contact_name)
            if u.profile_image:
                i = b64encode(u.profile_image).decode("utf-8")
            else:
                with open("static/img/avatar.png", "rb") as image_file:
                    i = b64encode(image_file.read()).decode("utf-8")
            pictures.append(i)
        percentage = [0,0,0,0,0]
        if(not (len(reviews) == 0 )):
            for i in range(5):
                percentage[i] = int((counts[i]/len(reviews))*100)
                percentage[i] = str(percentage[i])+"%"
        if current_user.rating == None:
            current_user.rating = 0
        rating = (current_user.rating/5)*100
        org = Organizer.query.filter_by(user_id = session['user_id']).first()

        return render_template("orgProfile.html", user = user,org = org, img=image, reviews = reviews, totalEvents=totalEvents,totalReviews = len(reviews), counts = counts,percentage=percentage, rating=rating, names = names, pictures = pictures, page="own")
    else:
        return 'Not Organizer'

@app.route('/volsignup')
def volunteerSignUp():
    return render_template("volunteerSignup.html")

@app.route('/postEvent', methods=['GET', 'POST'])
@login_required
def postEvent(): # pseudocode only, not tested yet
    if current_user.user_role != 1:
        if request.method == 'POST':
            title = request.form['title']
            categ = request.form['category']
            start_date = dateutil.parser.parse(request.form['startDate'])
            end_date = dateutil.parser.parse(request.form['endDate'])

            volunteer_number = request.form['volnum']
            description = request.form['description']
            location = request.form['location']
            latitude = request.form['lat']
            longitude = request.form['long']
            hours = request.form['hours']
            creation_date = datetime.datetime.now()
            
            event = Events(event_name = title, event_description = description,creation_date=creation_date,start_date=start_date,end_date=end_date,location=location,capacity=volunteer_number,category_id=categ,events_status_id=1,hours=hours,lat=latitude,long=longitude)
            db.session.add(event)
            db.session.commit()

            ue = User_event(user_id = session['user_id'],event_id = event.event_id)
            db.session.add(ue)
            db.session.commit()
            categories = Category.query.all()
            return redirect(url_for("eventRestrictions", id= event.event_id))

        else:
            categories = Category.query.all()
            return render_template("postEvent.html",categories=categories)
    else:
        return 'Not Organizer'
    
@app.route('/eventRestrictions/<id>', methods=['GET', 'POST'])
@login_required
def eventRestrictions(id):
    if current_user.user_role != 1:
        if request.method == 'POST':
            age = request.form['age']
            hours = request.form['hours']
            langs = request.form.getlist('language')
            location = request.form['location']

            for l in langs:
                la = Language_requirements(event_id=id,language_id = l)
                db.session.add(la)
            db.session.commit()

            res = Event_requirement(event_id = id, age_limit = age, location = location, min_hours=hours)
            db.session.add(res)     
            db.session.commit()

            languages = Language.query.all()
            return redirect(url_for("dashboardOrg",tab="events"))

        else:
            languages = Language.query.all()
            return render_template("eventReq.html",id = id, languages=languages)
    else:
        return 'Not Organizer'


@app.route('/announcements/<id>', methods=['GET', 'POST'])
@login_required
def sendAnnouncements(id):
    if current_user.user_role != 1:
        if request.method == 'POST':
            title = request.form['title']
            date = dateutil.parser.parse(request.form['date'])
            description = request.form['description']
            
            a = Announcements(event_id = id, title = title, description=description, date=date)
            db.session.add(a)
            db.session.commit()
            return redirect(url_for("dashboardOrg", tab="events"))

        return render_template("sendAnnouncement.html")
    else:
        return 'Not Organizer'

@app.route('/deleteEvent/<id>')
@login_required
def deleteEvent(id):
    if current_user.user_role != 1:
        event = Events.query.filter_by(event_id = id).first()
        if(not(event == None)):
            ue = User_event.query.filter_by(event_id = id).all()
            for u in ue:
                db.session.delete(u)

            er = Event_requirement.query.filter_by(event_id = id).all()
            for e in er:
                db.session.delete(e)
            db.session.delete(event)

            lr = Language_requirements.query.filter_by(event_id = id).all()
            for l in lr:
                db.session.delete(l)
            db.session.commit()
        return redirect(url_for('dashboardOrg',tab="events"))
    else:
        return 'Not Organizer'


@app.route('/editEvent/<id>', methods=['GET', 'POST'])
@login_required
def editEvent(id):
    if current_user.user_role != 1:
        event = Events.query.filter_by(event_id = id).first()
        eventReq = Event_requirement.query.filter_by(event_id = id).first()
        categories = Category.query.all()
        if request.method == 'POST':
            event.event_name = request.form['title']
            event.category_id = request.form['category']
            event.start_date = dateutil.parser.parse(request.form['startDate'])
            event.end_date = dateutil.parser.parse(request.form['endDate'])

            event.capacity = request.form['volnum']
            event.devent_description = request.form['description']
            event.location = request.form['location']
            event.lat = request.form['lat']
            event.long = request.form['long']
            event.hours = request.form['hours']
            event.events_status_id = request.form['status']
            db.session.commit()
            return redirect(url_for('dashboardOrg',tab="events"))
        else:
            stats = Event_status.query.all()
            status = ["Pending", "Completed", "In progress","Cancelled"]
            start = event.start_date.strftime("%Y-%m-%dT%H:%M:%S")
            end = event.end_date.strftime("%Y-%m-%dT%H:%M:%S")
            return render_template("editEvent.html", event = event, categories=categories,start=start,end=end,stats=stats,status=status,eventReq=eventReq)
    else:
        return 'Not Organizer'

@app.route('/markattendance/<id>', methods=['GET', 'POST'])
@login_required
def markattendance(id):
    if current_user.user_role != 1:
        event = Events.query.filter_by(event_id = id).first()
        vol = Registered_volunteers.query.filter_by(event_id = id).all()
        images = []
        volunteers = []
        for v in vol:
            if ( v.volunteer_status_id == 1):
                volun = Volunteer.query.filter_by(user_id =v.volunteer_user_id ).first()
                volunteers.append(volun)
                user = Users.query.filter_by(user_id = v.volunteer_user_id).first()
                if user.profile_image:
                    i = b64encode(user.profile_image).decode("utf-8")
                else:
                    with open("static/img/avatar.png", "rb") as image_file:
                        i = b64encode(image_file.read()).decode("utf-8")
                images.append(i)
        
        return render_template("markattendance.html", id=id,event = event, volunteers=volunteers,images=images)
    else:
        return 'Not Organizer'

@app.route('/attendance/<id>/<mode>', methods=['GET', 'POST'])
@login_required
def attendance(id,mode):
    checked = request.form.getlist('checked')
    present = checked[0].split('|')
    present.remove('')
    present = [int(i) for i in present]
    #get list of volunteers
    vols = Registered_volunteers.query.filter_by(event_id = id).all()
    if mode == "list":
        ids = []
        #get volunteer ids
        for v in vols:
            iden = v.volunteer_user_id
            #if user is present
            if(iden in present):
                v.volunteer_status_id = 3
                db.session.commit()
            else:
                ids.append(iden)
        if(len(ids) > 0):
            images = []
            volunteers = []
            for iden in ids:
                volun = Volunteer.query.filter_by(user_id =iden).first()
                name = volun.first_name + " " + volun.last_name
                volunteers.append(name)
                user = Users.query.filter_by(user_id = iden).first()
                if user.profile_image:
                    i = b64encode(user.profile_image).decode("utf-8")
                else:
                    with open("static/img/avatar.png", "rb") as image_file:
                        i = b64encode(image_file.read()).decode("utf-8")
                images.append(i)
            return json.dumps({'success' : True, 'mode' : "remain"}), 200, {'ContentType' : 'application/json'}
        else:
            return json.dumps({'success' : True, 'mode' : "done"}), 200, {'ContentType' : 'application/json'}
    elif mode == "review":
        ids = []
        #get volunteer ids
        for v in vols:
            if (v.volunteer_status_id == 1):
                iden = v.volunteer_user_id
                #if user is present
                if(iden in present):
                    v.volunteer_status_id = 3
                else:
                    v.volunteer_status_id = 5
                db.session.commit()

    return "Hello"

@app.route("/displayProfile/<id>")
@login_required
def displayProfile(id):
    user = Users.query.filter_by(user_id = id).first()
    if user.profile_image:
        image = b64encode(user.profile_image).decode("utf-8")
    else:
         with open("static/img/avatar.png", "rb") as image_file:
            image = b64encode(image_file.read()).decode("utf-8")
    reviews = Reviews.query.filter_by(to_user_id = user.user_id).all()
    counts = [0,0,0,0,0]
    names = []
    pictures = []
    for r in reviews:
        counts[r.rating-1] += 1
        u = Users.query.filter_by(user_id = r.from_user_id).first()
        if (u.user_role == 1):
            v = Volunteer.query.filter_by(user_id = r.from_user_id).first()
            n = v.first_name + " " + v.last_name
            names.append(n)
        else:
            o = Organizer.query.filter_by(user_id = r.from_user_id).first()
            names.append(o.contact_name)
        if u.profile_image:
            i = b64encode(u.profile_image).decode("utf-8")
        else:
            with open("static/img/avatar.png", "rb") as image_file:
                i = b64encode(image_file.read()).decode("utf-8")
        pictures.append(i)
        
    percentage = [0,0,0,0,0]
    if(not (len(reviews) == 0 )):
        for i in range(5):
            percentage[i] = int((counts[i]/len(reviews))*100)
            percentage[i] = str(percentage[i])+"%"
    if current_user.rating == None:
        current_user.rating = 0
    rating = (current_user.rating/5)*100
    print(percentage)

    if (user.user_role == 1):
        vol = Volunteer.query.filter_by(user_id = id).first()
        return render_template("volProfile.html", user = user, vol = vol, img=image, reviews = reviews, totalReviews = len(reviews), counts = counts,percentage=percentage, rating=rating, names = names, pictures = pictures, page = "not own")
    else:
        org = Organizer.query.filter_by(user_id = id).first()
        return render_template("orgProfile.html", user = user, org = org, img=image, reviews = reviews, totalReviews = len(reviews), counts = counts,percentage=percentage, rating=rating, names = names, pictures = pictures, page = "not own")


@app.route("/unregisterEvent/<id>")
@login_required
def unregisterEvent(id):
    Registered_volunteers.query.filter_by(volunteer_user_id = session['user_id'],event_id = id).delete()
    db.session.commit()

    return redirect(url_for('dashboardVol',tab="events")) 


@app.route("/viewEvent/<id>")
@login_required
def viewEvent(id):
    event = Events.query.filter_by(event_id = id).first()
    uevent = User_event.query.filter_by(event_id = id).first()
    r = Registered_volunteers.query.filter_by(event_id = id).all()
    registered = len(r)
    if (not(uevent == None)):
        org = Organizer.query.filter_by(user_id = uevent.user_id).first()
    else:
        org = None

    if current_user.profile_image:
        i = b64encode(current_user.profile_image).decode("utf-8")
    else:
        with open("static/img/avatar.png", "rb") as image_file:
            i = b64encode(image_file.read()).decode("utf-8")

    bookmark = Bookmarked_events.query.filter_by(event_id = id, volunteer_user_id = session['user_id']).first()
    
    category = (Category.query.filter_by(category_id = event.category_id).first()).category_name
    langRe = Language_requirements.query.filter_by(event_id = id).all()
    langs = []
    for l in langRe:
        language = Language.query.filter_by(language_id = l.language_id).first()
        langs.append(language.language_name)
    return render_template("viewEvent.html",event=event, langs=langs, org=org, image = i, category= category, bookmark=bookmark, registered=registered,error=None)

@app.route("/fetchevents",methods=["POST","GET"])
def fetchevents():
    if request.method == 'POST':
        query = request.form['action']
        minimum_price = request.form['minimum_hours']
        maximum_price = request.form['maximum_hours']
        #print(query)
        if query == '':
            eventlist = Events.query.all()
        else:
            eventlist = Events.query.filter(Events.hours <= minimum_price, Events.hours <= maximum_price) 
    return jsonify({'htmlresponse': render_template('testevents.html', eventlist=eventlist)})
 
@app.route('/joinEvent/<id>')
@login_required
def joinEvent(id):
    date = datetime.datetime.now()- datetime.timedelta(days=1)
    event = Events.query.filter_by(event_id = id).first()
    
    uevent = User_event.query.filter_by(event_id = id).first()
    r = Registered_volunteers.query.filter_by(event_id = id).all()
    registered = len(r)
    bookmark = Bookmarked_events.query.filter_by(event_id = id, volunteer_user_id = session['user_id']).first()
    category = (Category.query.filter_by(category_id = event.category_id).first()).category_name
    langRe = Language_requirements.query.filter_by(event_id = id).all()
    langs = []
    for l in langRe:
        language = Language.query.filter_by(language_id = l.language_id).first()
        langs.append(language.language_name)

    if current_user.profile_image:
        i = b64encode(current_user.profile_image).decode("utf-8")
    else:
        with open("static/img/avatar.png", "rb") as image_file:
            i = b64encode(image_file.read()).decode("utf-8")

    if (not(uevent == None)):
        org = Organizer.query.filter_by(user_id = uevent.user_id).first()
    else:
        org = None

    if(date > event.start_date):
        return render_template("viewEvent.html", langs=langs, category=category, event=event, org=org, bookmark=bookmark, registered=registered, image=i, error = "The event has already started, you cannot join event now!")

    reg = Registered_volunteers.query.filter_by(volunteer_user_id = session['user_id'],event_id = id).first()
    if (not(reg == None)):
        return render_template("viewEvent.html", langs=langs, category=category, event=event, org=org, bookmark=bookmark, registered=registered, image=i, error = "You are already registered!")
    
    eventreq = Event_requirement.query.filter_by(event_id = id).first()

    if(not(eventreq == None)):
        vol = Volunteer.query.filter_by(user_id = session['user_id']).first()
        today = date.today()
        age = today.year - vol.birthdate.year - ((today.month, today.day) < (vol.birthdate.month, vol.birthdate.day))
        if eventreq.age_limit:
            if(age < eventreq.age_limit):
                return render_template("viewEvent.html",langs=langs,category=category,event=event, org=org, bookmark=bookmark, registered=registered, image=i,error = "Age limit requirement is not satisfied!")
        if eventreq.location:
            if vol.location == eventreq.location:
                return render_template("viewEvent.html",langs=langs,category=category,event=event, org=org, bookmark=bookmark, registered=registered, image=i,error = "Location requirement is not satisfied!")
        if eventreq.min_hours:
            if (vol.hours < eventreq.min_hours):
                return render_template("viewEvent.html",langs=langs,category=category,event=event, org=org, bookmark=bookmark, registered=registered, image=i,error = "Minimum hour requirement is not satisfied!")

    langs = Language_requirements.query.filter_by(event_id = id).all()
    if (not(langs == None)):
        req_lang = []
        for l in langs:
            req_lang.append(l.language_id)

        lang_vol = Volunteer_language.query.filter_by(volunteer_user_id = session['user_id']).all()
        vol_lang = []
        for l in lang_vol:
            vol_lang.append(l.language_id)

        for l in req_lang:
            if (not(l in vol_lang)):
                return render_template("viewEvent.html",langs=langs,category=category,event=event, org=org, bookmark=bookmark, registered=registered, image=i,error = "Language requirement is not satisfied!")

    rv = Registered_volunteers(volunteer_user_id = session['user_id'], event_id = id, volunteer_status_id = 1)
    db.session.add(rv)
    db.session.commit()
    return render_template("viewEvent.html",langs=langs,event=event,category=category, org=org, registered=registered, bookmark=bookmark, image=i,error = "You have registered to the event successfully!")

@app.route("/filter", methods=['GET', 'POST'])
@login_required    
def Filter():
    res = json.loads(request.form['arr'])
    data = tuple(int(k) for k,v in res.items() if int(v)!=0)
    container = res.values()
    total = sum(map(lambda x: int(x),container))

    location = request.form['location']

    min = request.form['minimum']
    max = request.form['maximum']
    sort = request.form['sort']
    print("///sort:", sort)
    if total == 0:
        if location == 'Select an Emirate':
            locs = Events.query.filter(Events.hours >= min, Events.hours <= max).all()
        else:
            locs = Events.query.filter(Events.hours >= min, Events.hours <= max, Events.location == location).all()

    else:
        if location == 'Select an Emirate':
            locs = Events.query.filter(Events.category_id.in_(data), Events.hours >= min, Events.hours <= max).all()
        else:
            locs = Events.query.filter(Events.category_id.in_(data), Events.hours >= min, Events.hours <= max, Events.location == location).all()
    
    rating = []

    for l in locs:
        e = User_event.query.filter_by(event_id = l.event_id).first()
        u = Users.query.filter_by(user_id = e.user_id).first()
        l.rating = u.rating
        rating.append(u.rating)

    if sort == '1':
        locs = sorted(locs, key=lambda x: x.start_date, reverse=True)
    elif sort == '2':
        locs = sorted(locs, key=lambda x: x.rating, reverse=True)


    return jsonify({'htmlresponse':render_template('response.html', events=locs, len=len)})





@app.route("/filter/hours", methods=['GET', 'POST'])
@login_required    
def filterHours():
    min = request.form['minimum']
    max = request.form['maximum']

    events = Events.query.filter(Events.hours >= min, Events.hours <= max).all()

    return jsonify({'htmlresponse':render_template('response.html', events=events, len=len)})

@app.route("/filter/location", methods=['GET', 'POST'])
@login_required    
def filterLocation():
    print("/////inside")
    location = request.form['location']

    events = Events.query.filter_by(location=location).all()

    return jsonify({'htmlresponse':render_template('response.html', events=events, len=len)})

@app.route("/reviewattendance/<id>/", methods=['GET', 'POST'])
@login_required
def reviewattendance(id):
    vol = Registered_volunteers.query.filter_by(event_id = id).all()
    images = []
    volunteers = []
    for v in vol:
        if(v.volunteer_status_id == None):
            volun = Volunteer.query.filter_by(user_id =v.volunteer_user_id ).first()
            volunteers.append(volun)
            user = Users.query.filter_by(user_id = v.volunteer_user_id).first()
            if user.profile_image:
                i = b64encode(user.profile_image).decode("utf-8")
            else:
                with open("static/img/avatar.png", "rb") as image_file:
                    i = b64encode(image_file.read()).decode("utf-8")
            images.append(i)
    return render_template("reviewattendance.html", id=id,volunteers=volunteers,images=images)

@app.route("/completeEvent/<id>",methods=['GET', 'POST'])
@login_required
def completeEvent(id):
    event = Events.query.filter_by(event_id = id).first()
    datelimit = datetime.datetime.now()
    #if event has not started yet
    if(datelimit < event.start_date):
        return json.dumps({'success':False}), 400, {'ContentType':'application/json'}
    event.events_status_id = 2
    users = Registered_volunteers.query.filter_by(event_id = id).all()
    for u in users:
        v = Volunteer.query.filter_by(user_id = u.volunteer_user_id).first()
        v.hours += event.hours
    db.session.commit()
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route("/removebookmark/<id>", methods=['GET', 'POST'])
@login_required
def removeBookmark(id):
    Bookmarked_events.query.filter_by(volunteer_user_id = session['user_id'],event_id=id).delete()
    db.session.commit()

    return "You have successfully removed the bookmark for this event!"


@app.route("/addbookmark/<id>", methods=['GET', 'POST'])
@login_required
def addBookmark(id):
    event = Events.query.filter_by(event_id = id).first()
    datelimit = datetime.datetime.now()- datetime.timedelta(days=1)

    if (datelimit > event.start_date):
        return jsonify({"error":'You cannot bookmark this event due to the start date'}), 401

    r = Registered_volunteers.query.filter_by(volunteer_user_id = session['user_id'],event_id=id).first()
    if not(r == None):
        return jsonify({"error":'You cannot bookmark an event you are already registered in'}), 401
    b = Bookmarked_events.query.filter_by(volunteer_user_id = session['user_id'],event_id=id).first()
    if b == None:
        b = Bookmarked_events(volunteer_user_id = session['user_id'],event_id = id)
        db.session.add(b)
        db.session.commit()
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

    return jsonify({"error":'You have already bookmarked this event'}), 401

@app.route("/delete/<id>", methods=['GET', 'POST'])
@login_required
def deleteAccount(id):
    if (request.method == 'POST'):
        user = Users.query.filter_by(user_id = id)
        Reviews.query.filter_by(to_user_id = id).delete()
        Reviews.query.filter_by(to_user_id = id).delete()

        if(user.user_role == 1):
            Registered_volunteers.query.filter_by(volunteer_user_id = id).delete()
            Volunteer_language.query.filter_by(volunteer_user_id = id).delete()
            Mailing_list.query.filer_by(volunteer_user_id = id).delete()
            Bookmarked_events.query.filter_by(volunteer_user_id = id).delete()
            Volunteer.query.filter_by(user_id = id).delete()
        else:
            user_events = User_event.query.filter_by(user_id = id).all()
            for e in user_events:
                Registered_volunteers.query.filter_by(event_id = e.event_id).delete()
                Event_requirement.query.filter_by(event_id = e.event_id).delete()
                Announcements.query.filter_by(event_id = e.event_id).delete()
                Language_requirements.query.filter_by(event_id = e.event_id).delete()
                Bookmarked_events.query.filter_by(event_id = e.event_id).delete()
                eid = e.event_id
                db.session.delete(e)
                Events.query.filter_by(event_id = eid).delete()
            Organizer.query.filter_by(user_id = id).delete()
        db.session.delete(user)
        db.session.commit()
    return render_template("index.html")
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You were logged out.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.secret_key = 'OCML3BRawWEUeaxcuKHLpw'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True, port=8080, host='0.0.0.0')