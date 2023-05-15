from flask import Flask, request, session, render_template, url_for, flash, redirect
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask import jsonify
import random
import uuid
import urllib.parse

# Configure app
app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_tracking.db'

# Configure flask session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./flask_session"
app.config['ENABLE_AB_TESTING'] = True
app.config['DEFAULT_VERSION'] = 'a'  # Set this to 'a' or 'b'
app.secret_key = "pipers"
Session(app)

# Set up database and database models
db = SQLAlchemy(app)

# Version A
class SiteVisitA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(36))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    entry_time = db.Column(db.DateTime)
    exit_time = db.Column(db.DateTime)
    last_page = db.Column(db.String(255))

class PrivacyPolicyA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(36), nullable=False)
    decision = db.Column(db.String(2), nullable=False)

    def __init__(self, visitor_id, decision):
        self.visitor_id = visitor_id
        self.decision = decision

class DonateClickA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(36), nullable=False)
    header_clicks = db.Column(db.Integer, nullable=False, default=0)
    index_clicks = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, visitor_id):
        self.visitor_id = visitor_id
        self.header_clicks = 0
        self.index_clicks = 0

# Version B
class SiteVisitB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(36))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    entry_time = db.Column(db.DateTime)
    exit_time = db.Column(db.DateTime)
    last_page = db.Column(db.String(255))

class PrivacyPolicyB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(36), nullable=False)
    decision = db.Column(db.String(2), nullable=False)

    def __init__(self, visitor_id, decision):
        self.visitor_id = visitor_id
        self.decision = decision

class DonateClickB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(36), nullable=False)
    header_clicks = db.Column(db.Integer, nullable=False, default=0)
    index_clicks = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, visitor_id):
        self.visitor_id = visitor_id
        self.header_clicks = 0
        self.index_clicks = 0

class DonatePopupB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(36))
    action = db.Column(db.String(50))

    def __init__(self, visitor_id, action):
        self.visitor_id = visitor_id
        self.action = action

with app.app_context():
    db.create_all()

# General

def get_next_version():
    session['current_version'] = random.choice(['a', 'b'])
    session.modified = True
    return session['current_version']

@app.route('/')
def index():
    if app.config['ENABLE_AB_TESTING']:
        version = get_next_version()
    else:
        version = app.config['DEFAULT_VERSION']

    visitor_id = session.get("visitor_id")
    if not visitor_id:
        visitor_id = generate_visitor_id_a() if version == 'a' else generate_visitor_id_b()
        session["visitor_id"] = visitor_id

    if version == 'a':
        log_site_visit_once_a(visitor_id)
        return render_template('index_a.html', visitor_id=visitor_id)
    else:
        log_site_visit_once_b(visitor_id)
        return render_template('index_b.html', visitor_id=visitor_id)

@app.route('/index_a')
def index_a():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('index_a.html', visitor_id=visitor_id)

@app.route('/index_b')
def index_b():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('index_b.html', visitor_id=visitor_id)

@app.before_request
def reset_site_visit_logged():
    if 'site_visit_logged_a' in session:
        del session['site_visit_logged_a']
    if 'site_visit_logged_b' in session:
        del session['site_visit_logged_b']


# Version A
# Function to log data: this function saves the time spent on the previous page in the database. Unit of time is seconds.
def generate_visitor_id_a():
    return str(uuid.uuid4())[:10]

def log_site_visit_a(visitor_id):
    site_visit = SiteVisitA(
        visitor_id=visitor_id,
        entry_time=datetime.now(),
        ip_address=get_user_ip(),
        user_agent=request.user_agent.string,
    )
    db.session.add(site_visit)
    db.session.commit()

def log_site_visit_once_a(visitor_id):
    if 'site_visit_logged_a' not in session or not session['site_visit_logged_a']:
        site_visit = SiteVisitA(
            visitor_id=visitor_id,
            entry_time=datetime.now(),
            ip_address=get_user_ip(),
            user_agent=request.user_agent.string,
        )
        db.session.add(site_visit)
        db.session.commit()
        session['site_visit_logged_a'] = True
        session.modified = True
    else:
        session.modified = False

def get_user_ip():
    if 'X-Forwarded-For' in request.headers:
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0]
    return request.remote_addr

def log_exit_a(last_page):
    site_visit = SiteVisitA.query.filter_by(visitor_id=session.get('visitor_id')).order_by(SiteVisitA.id.desc()).first()
    if site_visit:
        site_visit.exit_time = datetime.now()
        site_visit.last_page = last_page
        db.session.commit()

def update_donate_clicks_a(visitor_id, button_type):
    donate_click = DonateClickA.query.filter_by(visitor_id=visitor_id).first()
    if not donate_click:
        donate_click = DonateClickA(visitor_id=visitor_id)
        db.session.add(donate_click)

    if button_type == 'header_a':
        donate_click.header_clicks += 1
    elif button_type == 'index_a':
        donate_click.index_clicks += 1

    db.session.commit()

@app.route('/track_donate_click_a', methods=['POST'])
def track_donate_click_a():
    visitor_id = request.form.get('visitor_id')
    button_type = request.form.get('button_type')
    update_donate_clicks_a(visitor_id, button_type)
    return 'OK'

@app.route('/track_exit_a', methods=['POST'])
def track_exit_route_a():
    last_page = request.form.get('last_page')
    log_exit_a(last_page)
    return '', 204

@app.route('/get_visitor_id_a', methods=['GET'])
def get_visitor_id_a():
    # Check if visitor_id is already in the session
    if 'visitor_id' not in session:
        session['visitor_id'] = generate_visitor_id_a()

    visitor_id = session['visitor_id']
    log_site_visit_a(visitor_id)  # Log the site visit
    return jsonify(visitor_id=visitor_id),

@app.route('/log_privacy_decision_a', methods=['POST'])
def log_privacy_decision_a():
    visitor_id = request.form['visitor_id']
    decision = request.form['decision']
    privacy_policy_record = PrivacyPolicyA(visitor_id, decision)
    db.session.add(privacy_policy_record)
    db.session.commit()
    return jsonify(success=True)

@app.route('/privacy_banner_a')
def privacy_banner_a():
    return render_template('privacy_banner_a.html')

@app.route('/about_a')
def about_a():
    visitor_id = session.get("visitor_id")
    if not visitor_id:
        visitor_id = generate_visitor_id_a()
        session["visitor_id"] = visitor_id
    log_site_visit_once_a(visitor_id)
    return render_template('about_a.html', visitor_id=visitor_id)

@app.route('/map_a')
def map_a():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('map_a.html', visitor_id=visitor_id)

@app.route('/projects_a')
def projects_a():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('projects_a.html', visitor_id=visitor_id)

@app.route('/donate_a')
def donate_a():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('donate_a.html', visitor_id=visitor_id)

@app.route('/header_a')
def header_a():
    return render_template('header_a.html')

@app.route('/footer_a')
def footer_a():
    return render_template('footer_a.html')

@app.route('/privacy_a')
def privacy_a():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('privacy_a.html', visitor_id=visitor_id)

@app.route('/learn_more_a')
def learn_more_a():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('learn_more_a.html', visitor_id=visitor_id)

@app.route('/gallery_a')
def gallery_a():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('gallery_a.html', visitor_id=visitor_id)

@app.route('/gallery_mali_a')
def gallery_mali_a():
    country_images = [{'filename': 'mali/mali1.jpg'}, {'filename': 'mali/mali2.jpg'}, {'filename': 'mali/mali3.jpg'}, {'filename': 'mali/mali4.jpg'}, {'filename': 'mali/mali5.jpg'}, {'filename': 'mali/mali6.jpg'}, {'filename': 'mali/mali7.jpg'}, {'filename': 'mali/mali8.jpg'}, {'filename': 'mali/mali9.jpg'}, {'filename': 'mali/mali10.jpg'}, {'filename': 'mali/mali11.jpg'}, {'filename': 'mali/mali12.jpg'}, {'filename': 'mali/mali13.jpg'}, {'filename': 'mali/mali14.jpg'}, {'filename': 'mali/mali15.jpg'}, {'filename': 'mali/mali16.jpg'}, {'filename': 'mali/mali17.jpg'}, {'filename': 'mali/mali18.jpg'}, {'filename': 'mali/mali19.jpg'}, {'filename': 'mali/mali20.jpg'}, {'filename': 'mali/mali22.jpg'}, {'filename': 'mali/mali23.jpg'}, {'filename': 'mali/mali24.jpg'}, {'filename': 'mali/mali25.jpg'}, {'filename': 'mali/mali27.jpg'}, {'filename': 'mali/mali28.jpg'}, {'filename': 'mali/mali29.jpg'}, {'filename': 'mali/mali30.jpg'}, {'filename': 'mali/mali31.jpg'}, {'filename': 'mali/mali33.jpg'}, {'filename': 'mali/mali34.jpg'}, {'filename': 'mali/mali35.jpg'}, {'filename': 'mali/mali36.jpg'}, {'filename': 'mali/mali37.jpg'}, {'filename': 'mali/mali38.jpg'}, {'filename': 'mali/mali39.jpg'}, {'filename': 'mali/mali40.jpg'}, {'filename': 'mali/mali41.jpg'}, {'filename': 'mali/mali42.jpg'}, {'filename': 'mali/mali43.jpg'}, {'filename': 'mali/mali44.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('gallery_mali_a.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_kenya_a')
def gallery_kenya_a():
    country_images = [{'filename': 'kenya/kenya1.jpg'}, {'filename': 'kenya/kenya2.jpg'}, {'filename': 'kenya/kenya3.jpg'}, {'filename': 'kenya/kenya4.jpg'}, {'filename': 'kenya/kenya5.jpg'}, {'filename': 'kenya/kenya6.jpg'}, {'filename': 'kenya/kenya7.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('gallery_kenya_a.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_burkina_a')
def gallery_burkina_a():
    country_images = [{'filename': 'burkina/burkina1.jpg'}, {'filename': 'burkina/burkina2.jpg'}, {'filename': 'burkina/burkina3.jpg'}, {'filename': 'burkina/burkina4.jpg'}, {'filename': 'burkina/burkina5.jpg'}, {'filename': 'burkina/burkina6.jpg'}, {'filename': 'burkina/burkina7.jpg'}, {'filename': 'burkina/burkina8.jpg'}, {'filename': 'burkina/burkina9.jpg'}, {'filename': 'burkina/burkina10.jpg'}, {'filename': 'burkina/burkina11.jpg'}, {'filename': 'burkina/burkina12.jpg'}, {'filename': 'burkina/burkina13.jpg'}, {'filename': 'burkina/burkina14.jpg'}, {'filename': 'burkina/burkina15.jpg'}, {'filename': 'burkina/burkina16.jpg'}, {'filename': 'burkina/burkina17.jpg'}, {'filename': 'burkina/burkina18.jpg'}, {'filename': 'burkina/burkina19.jpg'}, {'filename': 'burkina/burkina20.jpg'}, {'filename': 'burkina/burkina21.jpg'}, {'filename': 'burkina/burkina22.jpg'}, {'filename': 'burkina/burkina23.jpg'}, {'filename': 'burkina/burkina24.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('gallery_burkina_a.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_gambia_a')
def gallery_gambia_a():
    country_images = [{'filename': 'gambia/gambia1.jpg'}, {'filename': 'gambia/gambia2.jpg'}, {'filename': 'gambia/gambia3.jpg'}, {'filename': 'gambia/gambia4.jpg'}, {'filename': 'gambia/gambia5.jpg'}, {'filename': 'gambia/gambia6.jpg'}, {'filename': 'gambia/gambia7.jpg'}, {'filename': 'gambia/gambia8.jpg'}, {'filename': 'gambia/gambia9.jpg'}, {'filename': 'gambia/gambia10.jpg'}, {'filename': 'gambia/gambia11.jpg'}, {'filename': 'gambia/gambia12.jpg'}, {'filename': 'gambia/gambia13.jpg'}, {'filename': 'gambia/gambia14.jpg'}, {'filename': 'gambia/gambia15.jpg'}, {'filename': 'gambia/gambia16.jpg'}, {'filename': 'gambia/gambia17.jpg'}, {'filename': 'gambia/gambia18.jpg'}, {'filename': 'gambia/gambia19.jpg'}, {'filename': 'gambia/gambia20.jpg'}, {'filename': 'gambia/gambia21.jpg'}, {'filename': 'gambia/gambia22.jpg'}, {'filename': 'gambia/gambia23.jpg'}, {'filename': 'gambia/gambia24.jpg'}, {'filename': 'gambia/gambia25.jpg'}, {'filename': 'gambia/gambia26.jpg'}, {'filename': 'gambia/gambia27.jpg'}, {'filename': 'gambia/gambia28.jpg'}, {'filename': 'gambia/gambia29.jpg'}, {'filename': 'gambia/gambia30.jpg'}, {'filename': 'gambia/gambia31.jpg'}, {'filename': 'gambia/gambia32.jpg'}, {'filename': 'gambia/gambia33.jpg'}, {'filename': 'gambia/gambia34.jpg'}, {'filename': 'gambia/gambia35.jpg'}, {'filename': 'gambia/gambia36.jpg'}, {'filename': 'gambia/gambia37.jpg'}, {'filename': 'gambia/gambia38.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('gallery_gambia_a.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_malawi_a')
def gallery_malawi_a():
    country_images = [{'filename': 'malawi/malawi1.jpg'}, {'filename': 'malawi/malawi2.jpg'}, {'filename': 'malawi/malawi3.jpg'}, {'filename': 'malawi/malawi4.jpg'}, {'filename': 'malawi/malawi5.jpg'}, {'filename': 'malawi/malawi6.jpg'}, {'filename': 'malawi/malawi7.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('gallery_malawi_b.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_sierra_leone_a')
def gallery_sierra_leone_a():
    country_images = [{'filename': 'sierra_leone/sierra_leone1.jpg'}, {'filename': 'sierra_leone/sierra_leone2.jpg'}, {'filename': 'sierra_leone/sierra_leone3.jpg'}, {'filename': 'sierra_leone/sierra_leone4.jpg'}, {'filename': 'sierra_leone/sierra_leone5.jpg'}, {'filename': 'sierra_leone/sierra_leone6.jpg'}, {'filename': 'sierra_leone/sierra_leone7.jpg'}, {'filename': 'sierra_leone/sierra_leone8.jpg'}, {'filename': 'sierra_leone/sierra_leone9.jpg'}, {'filename': 'sierra_leone/sierra_leone10.jpg'}, {'filename': 'sierra_leone/sierra_leone11.jpg'}, {'filename': 'sierra_leone/sierra_leone12.jpg'}, {'filename': 'sierra_leone/sierra_leone13.jpg'}, {'filename': 'sierra_leone/sierra_leone14.jpg'}, {'filename': 'sierra_leone/sierra_leone15.jpg'}, {'filename': 'sierra_leone/sierra_leone16.jpg'}, {'filename': 'sierra_leone/sierra_leone17.jpg'}, {'filename': 'sierra_leone/sierra_leone18.jpg'}, {'filename': 'sierra_leone/sierra_leone19.jpg'}, {'filename': 'sierra_leone/sierra_leone20.jpg'}, {'filename': 'sierra_leone/sierra_leone21.jpg'}, {'filename': 'sierra_leone/sierra_leone22.jpg'}, {'filename': 'sierra_leone/sierra_leone23.jpg'}, {'filename': 'sierra_leone/sierra_leone24.jpg'}, {'filename': 'sierra_leone/sierra_leone25.jpg'}, {'filename': 'sierra_leone/sierra_leone26.jpg'}, {'filename': 'sierra_leone/sierra_leone27.jpg'}, {'filename': 'sierra_leone/sierra_leone28.jpg'}, {'filename': 'sierra_leone/sierra_leone29.jpg'}, {'filename': 'sierra_leone/sierra_leone30.jpg'}, {'filename': 'sierra_leone/sierra_leone31.jpg'}, {'filename': 'sierra_leone/sierra_leone32.jpg'}, {'filename': 'sierra_leone/sierra_leone33.jpg'}, {'filename': 'sierra_leone/sierra_leone34.jpg'}, {'filename': 'sierra_leone/sierra_leone35.jpg'}, {'filename': 'sierra_leone/sierra_leone36.jpg'}, {'filename': 'sierra_leone/sierra_leone37.jpg'}, {'filename': 'sierra_leone/sierra_leone38.jpg'}, {'filename': 'sierra_leone/sierra_leone39.jpg'}, {'filename': 'sierra_leone/sierra_leone40.jpg'}, {'filename': 'sierra_leone/sierra_leone41.jpg'}, {'filename': 'sierra_leone/sierra_leone42.jpg'}, {'filename': 'sierra_leone/sierra_leone43.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('gallery_sierra_leone_a.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_sudan_a')
def gallery_sudan_a():
    country_images = [{'filename': 'sudan/sudan1.jpg'}, {'filename': 'sudan/sudan2.jpg'}, {'filename': 'sudan/sudan3.jpg'}, {'filename': 'sudan/sudan4.jpg'}, {'filename': 'sudan/sudan5.jpg'}, {'filename': 'sudan/sudan6.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('gallery_sudan_a.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_tanzania_a')
def gallery_tanzania_a():
    country_images = [{'filename': 'tanzania/tanzania1.jpg'}, {'filename': 'tanzania/tanzania2.jpg'}, {'filename': 'tanzania/tanzania3.jpg'}, {'filename': 'tanzania/tanzania4.jpg'}, {'filename': 'tanzania/tanzania5.jpg'}, {'filename': 'tanzania/tanzania6.jpg'}, {'filename': 'tanzania/tanzania7.jpg'}, {'filename': 'tanzania/tanzania8.jpg'}, {'filename': 'tanzania/tanzania9.jpg'}, {'filename': 'tanzania/tanzania10.jpg'}, {'filename': 'tanzania/tanzania11.jpg'}, {'filename': 'tanzania/tanzania12.jpg'}, {'filename': 'tanzania/tanzania13.jpg'}, {'filename': 'tanzania/tanzania14.jpg'}, {'filename': 'tanzania/tanzania15.jpg'}, {'filename': 'tanzania/tanzania16.jpg'}, {'filename': 'tanzania/tanzania17.jpg'}, {'filename': 'tanzania/tanzania18.jpg'}, {'filename': 'tanzania/tanzania19.jpg'}, {'filename': 'tanzania/tanzania20.jpg'}, {'filename': 'tanzania/tanzania21.jpg'}, {'filename': 'tanzania/tanzania22.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('gallery_tanzania_a.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/osiligi_a')
def osiligi_a():
    country_images = [{'filename': 'osiligi/osiligi1.jpg'}, {'filename': 'osiligi/osiligi2.jpg'}, {'filename': 'osiligi/osiligi3.jpg'}, {'filename': 'osiligi/osiligi4.jpg'}, {'filename': 'osiligi/osiligi5.jpg'}, {'filename': 'osiligi/osiligi6.jpg'}, {'filename': 'osiligi/osiligi7.jpg'}, {'filename': 'osiligi/osiligi8.jpg'}, {'filename': 'osiligi/osiligi9.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('osiligi_a.html', country_images=country_images, visitor_id=visitor_id)







# Version B
# Function to log data: this function saves the time spent on the previous page in the database. Unit of time is seconds.
def generate_visitor_id_b():
    return str(uuid.uuid4())[:10]

def log_site_visit_b(visitor_id):
    site_visit = SiteVisitB(
        visitor_id=visitor_id,
        entry_time=datetime.now(),
        ip_address=get_user_ip(),
        user_agent=request.user_agent.string,
    )
    db.session.add(site_visit)
    db.session.commit()

def log_site_visit_once_b(visitor_id):
    if 'site_visit_logged' not in session or not session['site_visit_logged']:
        site_visit = SiteVisitB(
            visitor_id=visitor_id,
            entry_time=datetime.now(),
            ip_address=get_user_ip(),
            user_agent=request.user_agent.string,
        )
        db.session.add(site_visit)
        db.session.commit()
        session['site_visit_logged'] = True
        session.modified = True
    else:
        session.modified = False

def get_user_ip_b():
    if 'X-Forwarded-For' in request.headers:
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0]
    return request.remote_addr

def save_user_action_b(visitor_id, action):
    donate_popup = DonatePopupB(visitor_id=visitor_id, action=action)
    db.session.add(donate_popup)
    db.session.commit()

def log_exit_b(last_page):
    site_visit = SiteVisitB.query.filter_by(visitor_id=session.get('visitor_id')).order_by(SiteVisitB.id.desc()).first()
    if site_visit:
        site_visit.exit_time = datetime.now()
        site_visit.last_page = last_page
        db.session.commit()

def update_donate_clicks_b(visitor_id, button_type):
    donate_click = DonateClickB.query.filter_by(visitor_id=visitor_id).first()
    if not donate_click:
        donate_click = DonateClickB(visitor_id=visitor_id)
        db.session.add(donate_click)

    if button_type == 'header_b':
        donate_click.header_clicks += 1
    elif button_type == 'index_b':
        donate_click.index_clicks += 1

    db.session.commit()

@app.route('/track_donate_click_b', methods=['POST'])
def track_donate_click_b():
    visitor_id = request.form.get('visitor_id')
    button_type = request.form.get('button_type')
    update_donate_clicks_b(visitor_id, button_type)
    return 'OK'

@app.route('/track_exit_b', methods=['POST'])
def track_exit_route_b():
    last_page = request.form.get('last_page')
    log_exit_b(last_page)
    return '', 204

@app.route('/get_visitor_id_b', methods=['GET'])
def get_visitor_id_b():
    # Check if visitor_id is already in the session
    if 'visitor_id' not in session:
        session['visitor_id'] = generate_visitor_id_b()

    visitor_id = session['visitor_id']
    log_site_visit_b(visitor_id)  # Log the site visit
    return jsonify(visitor_id=visitor_id),

@app.route('/log_privacy_decision_b', methods=['POST'])
def log_privacy_decision_b():
    visitor_id = request.form['visitor_id']
    decision = request.form['decision']
    privacy_policy_record = PrivacyPolicyB(visitor_id, decision)
    db.session.add(privacy_policy_record)
    db.session.commit()
    return jsonify(success=True)

@app.route('/track_user_action_b', methods=['POST'])
def track_user_action_b():
    visitor_id = request.form.get('visitor_id')
    if not visitor_id:
        visitor_id = session.get('visitor_id')
    action = request.form.get('action')

    # Save the action to the database (you need to implement this function)
    save_user_action_b(visitor_id, action)

    return 'OK'

@app.route('/privacy_banner_b')
def privacy_banner_b():
    return render_template('privacy_banner_b.html')

@app.route('/about_b')
def about_b():
    visitor_id = session.get("visitor_id")
    if not visitor_id:
        visitor_id = generate_visitor_id_b()
        session["visitor_id"] = visitor_id
    log_site_visit_once_b(visitor_id)
    return render_template('about_b.html', visitor_id=visitor_id)

@app.route('/map_b')
def map_b():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('map_b.html', visitor_id=visitor_id)

@app.route('/projects_b')
def projects_b():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('projects_b.html', visitor_id=visitor_id)

@app.route('/donate_b')
def donate_b():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_b(visitor_id)
    return render_template('donate_b.html', visitor_id=visitor_id)

@app.route('/header_b')
def header_b():
    return render_template('header_b.html')

@app.route('/footer_b')
def footer_b():
    return render_template('footer_b.html')

@app.route('/donate_popup_b')
def donate_popup_b():
    return render_template('donate_popup_b.html')

@app.route('/privacy_b')
def privacy_b():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('privacy_b.html', visitor_id=visitor_id)

@app.route('/learn_more_b')
def learn_more_b():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('learn_more_b.html', visitor_id=visitor_id)

@app.route('/gallery_b')
def gallery_b():
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_a()
    visitor_id = session["visitor_id"]
    log_site_visit_once_a(visitor_id)
    return render_template('gallery_b.html', visitor_id=visitor_id)

@app.route('/gallery_mali_b')
def gallery_mali_b():
    country_images = [{'filename': 'mali/mali1.jpg'}, {'filename': 'mali/mali2.jpg'}, {'filename': 'mali/mali3.jpg'}, {'filename': 'mali/mali4.jpg'}, {'filename': 'mali/mali5.jpg'}, {'filename': 'mali/mali6.jpg'}, {'filename': 'mali/mali7.jpg'}, {'filename': 'mali/mali8.jpg'}, {'filename': 'mali/mali9.jpg'}, {'filename': 'mali/mali10.jpg'}, {'filename': 'mali/mali11.jpg'}, {'filename': 'mali/mali12.jpg'}, {'filename': 'mali/mali13.jpg'}, {'filename': 'mali/mali14.jpg'}, {'filename': 'mali/mali15.jpg'}, {'filename': 'mali/mali16.jpg'}, {'filename': 'mali/mali17.jpg'}, {'filename': 'mali/mali18.jpg'}, {'filename': 'mali/mali19.jpg'}, {'filename': 'mali/mali20.jpg'}, {'filename': 'mali/mali22.jpg'}, {'filename': 'mali/mali23.jpg'}, {'filename': 'mali/mali24.jpg'}, {'filename': 'mali/mali25.jpg'}, {'filename': 'mali/mali27.jpg'}, {'filename': 'mali/mali28.jpg'}, {'filename': 'mali/mali29.jpg'}, {'filename': 'mali/mali30.jpg'}, {'filename': 'mali/mali31.jpg'}, {'filename': 'mali/mali33.jpg'}, {'filename': 'mali/mali34.jpg'}, {'filename': 'mali/mali35.jpg'}, {'filename': 'mali/mali36.jpg'}, {'filename': 'mali/mali37.jpg'}, {'filename': 'mali/mali38.jpg'}, {'filename': 'mali/mali39.jpg'}, {'filename': 'mali/mali40.jpg'}, {'filename': 'mali/mali41.jpg'}, {'filename': 'mali/mali42.jpg'}, {'filename': 'mali/mali43.jpg'}, {'filename': 'mali/mali44.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('gallery_mali_b.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_kenya_b')
def gallery_kenya_b():
    country_images = [{'filename': 'kenya/kenya1.jpg'}, {'filename': 'kenya/kenya2.jpg'}, {'filename': 'kenya/kenya3.jpg'}, {'filename': 'kenya/kenya4.jpg'}, {'filename': 'kenya/kenya5.jpg'}, {'filename': 'kenya/kenya6.jpg'}, {'filename': 'kenya/kenya7.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_b(visitor_id)
    return render_template('gallery_kenya_b.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_burkina_b')
def gallery_burkina_b():
    country_images = [{'filename': 'burkina/burkina1.jpg'}, {'filename': 'burkina/burkina2.jpg'}, {'filename': 'burkina/burkina3.jpg'}, {'filename': 'burkina/burkina4.jpg'}, {'filename': 'burkina/burkina5.jpg'}, {'filename': 'burkina/burkina6.jpg'}, {'filename': 'burkina/burkina7.jpg'}, {'filename': 'burkina/burkina8.jpg'}, {'filename': 'burkina/burkina9.jpg'}, {'filename': 'burkina/burkina10.jpg'}, {'filename': 'burkina/burkina11.jpg'}, {'filename': 'burkina/burkina12.jpg'}, {'filename': 'burkina/burkina13.jpg'}, {'filename': 'burkina/burkina14.jpg'}, {'filename': 'burkina/burkina15.jpg'}, {'filename': 'burkina/burkina16.jpg'}, {'filename': 'burkina/burkina17.jpg'}, {'filename': 'burkina/burkina18.jpg'}, {'filename': 'burkina/burkina19.jpg'}, {'filename': 'burkina/burkina20.jpg'}, {'filename': 'burkina/burkina21.jpg'}, {'filename': 'burkina/burkina22.jpg'}, {'filename': 'burkina/burkina23.jpg'}, {'filename': 'burkina/burkina24.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_b(visitor_id)
    return render_template('gallery_burkina_b.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_gambia_b')
def gallery_gambia_b():
    country_images = [{'filename': 'gambia/gambia1.jpg'}, {'filename': 'gambia/gambia2.jpg'}, {'filename': 'gambia/gambia3.jpg'}, {'filename': 'gambia/gambia4.jpg'}, {'filename': 'gambia/gambia5.jpg'}, {'filename': 'gambia/gambia6.jpg'}, {'filename': 'gambia/gambia7.jpg'}, {'filename': 'gambia/gambia8.jpg'}, {'filename': 'gambia/gambia9.jpg'}, {'filename': 'gambia/gambia10.jpg'}, {'filename': 'gambia/gambia11.jpg'}, {'filename': 'gambia/gambia12.jpg'}, {'filename': 'gambia/gambia13.jpg'}, {'filename': 'gambia/gambia14.jpg'}, {'filename': 'gambia/gambia15.jpg'}, {'filename': 'gambia/gambia16.jpg'}, {'filename': 'gambia/gambia17.jpg'}, {'filename': 'gambia/gambia18.jpg'}, {'filename': 'gambia/gambia19.jpg'}, {'filename': 'gambia/gambia20.jpg'}, {'filename': 'gambia/gambia21.jpg'}, {'filename': 'gambia/gambia22.jpg'}, {'filename': 'gambia/gambia23.jpg'}, {'filename': 'gambia/gambia24.jpg'}, {'filename': 'gambia/gambia25.jpg'}, {'filename': 'gambia/gambia26.jpg'}, {'filename': 'gambia/gambia27.jpg'}, {'filename': 'gambia/gambia28.jpg'}, {'filename': 'gambia/gambia29.jpg'}, {'filename': 'gambia/gambia30.jpg'}, {'filename': 'gambia/gambia31.jpg'}, {'filename': 'gambia/gambia32.jpg'}, {'filename': 'gambia/gambia33.jpg'}, {'filename': 'gambia/gambia34.jpg'}, {'filename': 'gambia/gambia35.jpg'}, {'filename': 'gambia/gambia36.jpg'}, {'filename': 'gambia/gambia37.jpg'}, {'filename': 'gambia/gambia38.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('gallery_gambia_b.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_malawi_b')
def gallery_malawi_b():
    country_images = [{'filename': 'malawi/malawi1.jpg'}, {'filename': 'malawi/malawi2.jpg'}, {'filename': 'malawi/malawi3.jpg'}, {'filename': 'malawi/malawi4.jpg'}, {'filename': 'malawi/malawi5.jpg'}, {'filename': 'malawi/malawi6.jpg'}, {'filename': 'malawi/malawi7.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('gallery_malawi_b.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_sierra_leone_b')
def gallery_sierra_leone_b():
    country_images = [{'filename': 'sierra_leone/sierra_leone1.jpg'}, {'filename': 'sierra_leone/sierra_leone2.jpg'}, {'filename': 'sierra_leone/sierra_leone3.jpg'}, {'filename': 'sierra_leone/sierra_leone4.jpg'}, {'filename': 'sierra_leone/sierra_leone5.jpg'}, {'filename': 'sierra_leone/sierra_leone6.jpg'}, {'filename': 'sierra_leone/sierra_leone7.jpg'}, {'filename': 'sierra_leone/sierra_leone8.jpg'}, {'filename': 'sierra_leone/sierra_leone9.jpg'}, {'filename': 'sierra_leone/sierra_leone10.jpg'}, {'filename': 'sierra_leone/sierra_leone11.jpg'}, {'filename': 'sierra_leone/sierra_leone12.jpg'}, {'filename': 'sierra_leone/sierra_leone13.jpg'}, {'filename': 'sierra_leone/sierra_leone14.jpg'}, {'filename': 'sierra_leone/sierra_leone15.jpg'}, {'filename': 'sierra_leone/sierra_leone16.jpg'}, {'filename': 'sierra_leone/sierra_leone17.jpg'}, {'filename': 'sierra_leone/sierra_leone18.jpg'}, {'filename': 'sierra_leone/sierra_leone19.jpg'}, {'filename': 'sierra_leone/sierra_leone20.jpg'}, {'filename': 'sierra_leone/sierra_leone21.jpg'}, {'filename': 'sierra_leone/sierra_leone22.jpg'}, {'filename': 'sierra_leone/sierra_leone23.jpg'}, {'filename': 'sierra_leone/sierra_leone24.jpg'}, {'filename': 'sierra_leone/sierra_leone25.jpg'}, {'filename': 'sierra_leone/sierra_leone26.jpg'}, {'filename': 'sierra_leone/sierra_leone27.jpg'}, {'filename': 'sierra_leone/sierra_leone28.jpg'}, {'filename': 'sierra_leone/sierra_leone29.jpg'}, {'filename': 'sierra_leone/sierra_leone30.jpg'}, {'filename': 'sierra_leone/sierra_leone31.jpg'}, {'filename': 'sierra_leone/sierra_leone32.jpg'}, {'filename': 'sierra_leone/sierra_leone33.jpg'}, {'filename': 'sierra_leone/sierra_leone34.jpg'}, {'filename': 'sierra_leone/sierra_leone35.jpg'}, {'filename': 'sierra_leone/sierra_leone36.jpg'}, {'filename': 'sierra_leone/sierra_leone37.jpg'}, {'filename': 'sierra_leone/sierra_leone38.jpg'}, {'filename': 'sierra_leone/sierra_leone39.jpg'}, {'filename': 'sierra_leone/sierra_leone40.jpg'}, {'filename': 'sierra_leone/sierra_leone41.jpg'}, {'filename': 'sierra_leone/sierra_leone42.jpg'}, {'filename': 'sierra_leone/sierra_leone43.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('gallery_sierra_leone_b.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_sudan_b')
def gallery_sudan_b():
    country_images = [{'filename': 'sudan/sudan1.jpg'}, {'filename': 'sudan/sudan2.jpg'}, {'filename': 'sudan/sudan3.jpg'}, {'filename': 'sudan/sudan4.jpg'}, {'filename': 'sudan/sudan5.jpg'}, {'filename': 'sudan/sudan6.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('gallery_sudan_b.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/gallery_tanzania_b')
def gallery_tanzania_b():
    country_images = [{'filename': 'tanzania/tanzania1.jpg'}, {'filename': 'tanzania/tanzania2.jpg'}, {'filename': 'tanzania/tanzania3.jpg'}, {'filename': 'tanzania/tanzania4.jpg'}, {'filename': 'tanzania/tanzania5.jpg'}, {'filename': 'tanzania/tanzania6.jpg'}, {'filename': 'tanzania/tanzania7.jpg'}, {'filename': 'tanzania/tanzania8.jpg'}, {'filename': 'tanzania/tanzania9.jpg'}, {'filename': 'tanzania/tanzania10.jpg'}, {'filename': 'tanzania/tanzania11.jpg'}, {'filename': 'tanzania/tanzania12.jpg'}, {'filename': 'tanzania/tanzania13.jpg'}, {'filename': 'tanzania/tanzania14.jpg'}, {'filename': 'tanzania/tanzania15.jpg'}, {'filename': 'tanzania/tanzania16.jpg'}, {'filename': 'tanzania/tanzania17.jpg'}, {'filename': 'tanzania/tanzania18.jpg'}, {'filename': 'tanzania/tanzania19.jpg'}, {'filename': 'tanzania/tanzania20.jpg'}, {'filename': 'tanzania/tanzania21.jpg'}, {'filename': 'tanzania/tanzania22.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('gallery_tanzania_b.html', country_images=country_images, visitor_id=visitor_id)

@app.route('/osiligi_b')
def osiligi_b():
    country_images = [{'filename': 'osiligi/osiligi1.jpg'}, {'filename': 'osiligi/osiligi2.jpg'}, {'filename': 'osiligi/osiligi3.jpg'}, {'filename': 'osiligi/osiligi4.jpg'}, {'filename': 'osiligi/osiligi5.jpg'}, {'filename': 'osiligi/osiligi6.jpg'}, {'filename': 'osiligi/osiligi7.jpg'}, {'filename': 'osiligi/osiligi8.jpg'}, {'filename': 'osiligi/osiligi9.jpg'}]
    if 'visitor_id' not in session:
        session["visitor_id"] = generate_visitor_id_b()
    visitor_id = session["visitor_id"]
    log_site_visit_once_b(visitor_id)
    return render_template('osiligi_b.html', country_images=country_images, visitor_id=visitor_id)

if __name__ == '__main__':
    app.run()