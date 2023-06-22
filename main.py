import os
import random
import string
from flask import Flask, render_template, abort, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import smtplib

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
LOW_QUALITY_FOLDER = 'static/images/low_quality'
app.secret_key = 'photographerkey'

photographer_credentials = {
    'username': 'photographer',
    'password': 'password123'
}
clients = {
    'all': {
        'username': 'all',
        'password': 'password',
        'projects': []
    },
    'AnnaJ': {
        'username': 'AnnaJ',
        'password': 'password123',
        'projects': []
    },
    'WeronikaJ': {
        'username': 'WeronikaJ',
        'password': 'password456',
        'projects': []
    },
    'BasiaSz': {
        'username': 'BasiaSz',
        'password': 'password789',
        'projects': []
    }
}

projects = [
    {
        'id': 1,
        'model': 'Anna',
        'date': '21.02.2023',
        'title': 'Sweet and sour',
        'src': ['/static/images/ProjektStazowy_012.jpg'],
        'visible': '🔒',
        'code': 'haslo123',
        'ready': True,
        'client_username': 'AnnaJ',
        'tags': ['portraits', 'all'],
        'status': 'edited'
    },
    {
        'id': 2,
        'model': 'My3',
        'date': '16.04.2023',
        'title': 'My3',
        'src': ['/static/images/20230416_KSAF_AGH_My3_KMidura_006.jpg'],
        'visible': '🔓',
        'code': None,
        'ready': True,
        'client_username': 'all',
        'tags': ['concerts', 'all'],
        'status': 'edited'
    },
    {
        'id': 3,
        'model': 'Weronika',
        'date': '15.08.2020',
        'title': 'Countrytime',
        'src': ['/static/images/IMG_2631-3.jpg'],
        'visible': '🔒',
        'code': 'haslo456',
        'ready': True,
        'client_username': 'WeronikaJ',
        'tags': ['portraits', 'all'],
        'status': 'edited'
    },
    {
        'id': 4,
        'model': '-',
        'date': '21.03.2022',
        'title': 'Planszówki z URSS',
        'src': ['/static/images/20221108_KSAF_AGH_PlanszowkiZURSS_KMidura_009.jpg'],
        'visible': '🔓',
        'code': None,
        'ready': True,
        'client_username': 'all',
        'tags': ['events', 'all'],
        'status': 'edited'
    },
    {
        "client_username": "BasiaSz",
        "code": "iKVJPaln",
        "date": "31.03.2023",
        "id": 5,
        "model": "Basia",
        "ready": False,
        "src": [
            "/static/images/low_quality/20230309_KSAF_AGH_SesjaBasia_KMidura_001.jpg",
            "/static/images/low_quality/20230309_KSAF_AGH_SesjaBasia_KMidura_002.jpg",
            "/static/images/low_quality/20230309_KSAF_AGH_SesjaBasia_KMidura_003.jpg",
            "/static/images/low_quality/20230309_KSAF_AGH_SesjaBasia_KMidura_004.jpg",
            "/static/images/low_quality/20230309_KSAF_AGH_SesjaBasia_KMidura_005.jpg",
            "/static/images/low_quality/20230309_KSAF_AGH_SesjaBasia_KMidura_006.jpg",
            "/static/images/low_quality/20230309_KSAF_AGH_SesjaBasia_KMidura_007.jpg"
        ],
        "status": "to_choose",
        "tags": [
            "portraits",
            "all"
        ],
        "title": "Heroic Chic",
        "visible": "🔒"
    }
]


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_to_low_quality(source_path, target_path):
    image = Image.open(source_path)
    watermark_image = image.copy()

    draw = ImageDraw.Draw(watermark_image)
    watermark_font = ImageFont.truetype("arial.ttf", 200)
    draw.text((600, 300), "Kat Midura", font=watermark_font, fill='#FFF', anchor="ms")

    watermark_image.save(target_path, quality=10)

def get_project_by_id(project_id):
    for project in projects:
        if project['id'] == project_id:
            return project
    return None


@app.route('/')
@app.route('/home')
def home():
    user_id = session.get('user_id')
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html', title='About')


@app.route('/projects')
def projects_page():
    tag = request.args.get('tag')

    if tag:
        filtered_projects = [project for project in projects if tag in project.get('tags', [])]
    else:
        filtered_projects = projects

    ready_projects = []
    for project in filtered_projects:
        if project['ready']:
            ready_projects.append(project)

    return render_template('projects.html', title='Projects', projects=ready_projects)

@app.route('/code/<int:project_id>', methods=['GET', 'POST'])
def code_route(project_id):
    project = next((project for project in projects if project['id'] == project_id), None)

    if project is None:
        abort(404)

    if request.method == 'POST':
        entered_code = request.form.get('code')
        if entered_code == project['code']:
            return render_template('photo_detail.html', project=project)
        else:
            return render_template('code.html', project=project, error=True)

    return render_template('code.html', project=project)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('contact.html', title='Contact')


@app.route('/photographer/add_project', methods=['GET', 'POST'])
def add_project():
    if not session.get('photographer_logged_in'):
        return redirect(url_for('login'))

    error = None

    if request.method == 'POST':
        model = request.form.get('model')
        date = request.form.get('date')
        title = request.form.get('title')
        visible = request.form.get('visible')
        code = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=8))
        ready = True if request.form.get('ready') == 'on' else False
        status = request.form['status']
        tags = request.form.get('tags').split(',')
        client_username = request.form.get('client_username')
        client_password = request.form.get('client_password')

        if 'images' not in request.files:
            error = 'No files were uploaded'
        else:
            files = request.files.getlist('images')

            if not os.path.exists(LOW_QUALITY_FOLDER):
                os.makedirs(LOW_QUALITY_FOLDER)

            filenames = []
            for file in files:
                if file.filename == '':
                    error = 'No selected file'
                    break

                if not allowed_file(file.filename):
                    error = 'Invalid file extension'
                    break

                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                if not ready:
                    low_quality_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'low_quality', filename)
                    convert_to_low_quality(file_path, low_quality_file_path)
                    filenames.append("/static/images/low_quality/" + filename)
                else:
                    filenames.append("/static/images/" + filename)

            if not error:
                if visible == '🔓' and not ready:
                    error = "Please check the 'Ready' option for an unlocked project."
                else:
                    new_id = len(projects) + 1

                    new_project = {
                        'id': new_id,
                        'model': model,
                        'date': date,
                        'title': title,
                        'src': filenames,
                        'visible': visible,
                        'code': code,
                        'ready': ready,
                        'client_username': None,
                        'status': status,
                        'tags': tags
                    }
                    projects.append(new_project)

                    client_exists = False
                    for client in clients.values():
                        if client['username'] == client_username:
                            client['projects'].append(new_project)
                            new_project['client_username'] = client_username
                            client_exists = True
                            break

                    if not client_exists:
                        new_client = {
                            'username': client_username,
                            'password': client_password,
                            'projects': [new_project]
                        }
                        clients[client_username] = new_client
                        new_project['client_username'] = client_username

                    return redirect(url_for('project_created', code=code))

    return render_template('add_project.html', error=error, photographer_logged_in=session['photographer_logged_in'])


@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    existing_images = get_project_by_id(project_id)
    if request.method == 'POST':
        model = request.form.get('model')
        date = request.form.get('date')
        title = request.form.get('title')
        visible = request.form.get('visible')
        delete_images = request.form.getlist('delete_images')
        add_images = request.files.getlist('add_images')
        status = request.form['status']

        if 'add_images' in request.files:
            add_images = request.files.getlist('add_images')
            for image in add_images:
                if image.filename != '':
                    filename = secure_filename(image.filename)
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    projects[project_id - 1]['src'].append('/static/images/' + filename)

        if 'add_existing_images' in request.form:
            add_existing_images = request.form.getlist('add_existing_images')
            for index in add_existing_images:
                projects[project_id - 1]['src'].append(existing_images[int(index)])

        for index in delete_images:
            index = int(index)
            if 0 <= index < len(projects[project_id - 1]['src']):
                deleted_image = projects[project_id - 1]['src'].pop(index)

    project = projects[project_id - 1]

    existing_images = project['src']

    return render_template('edit_project.html', project=project, existing_images=existing_images, project_id=project_id,
                           photographer_logged_in=session['photographer_logged_in'])


@app.route('/project_created/<code>')
def project_created(code):
    project = None
    for client in clients.values():
        for a in client['projects']:
            if a['code'] == code:
                project = a
                break

    if project is None:
        return 'Project not found.'

    return render_template('project_created.html', project=project,
                           photographer_logged_in=session['photographer_logged_in'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == photographer_credentials['username'] and password == photographer_credentials['password']:
            session['photographer_logged_in'] = True
            session['photographer_username'] = username
            return redirect(url_for('photographer_dashboard'))
        elif username in clients and password == clients[username]['password']:
            session['client_logged_in'] = True
            session['client_username'] = username
            return redirect(url_for('client_dashboard'))
        else:
            flash('Invalid credentials. Please try again.')

    return render_template('login.html', title='Login')


@app.route('/photographer/dashboard')
def photographer_dashboard():
    if not "photographer_username" in session:
        flash('Please log in to access the photographer dashboard.')
        return redirect(url_for('login'))
    else:
        return render_template('photographer_dashboard.html', photographer_logged_in=session['photographer_logged_in'])


@app.route('/photographer/dashboard/projects')
def projects_by_clients():
    if not "photographer_username" in session:
        flash('Please log in to access the photographer dashboard.')
        return redirect(url_for('login'))
    else:
        projects_by_client = {}

        for project in projects:
            client_username = project.get('client_username')
            if client_username:
                if client_username not in projects_by_client:
                    projects_by_client[client_username] = []
                projects_by_client[client_username].append(project)

    return render_template('projects_by_clients.html', photographer_logged_in=session['photographer_logged_in'],
                           projects_by_client=projects_by_client)


@app.route('/client/dashboard')
def client_dashboard():
    if 'client_logged_in' in session and session['client_logged_in']:
        username = session['client_username']
        ready_projects = [project for project in projects if
                          project['client_username'] == username and project['ready']]
        pending_projects = [project for project in projects if
                            not project['ready'] and project['client_username'] == username]

        return render_template('client_dashboard.html', title='Client Dashboard', ready_projects=ready_projects,
                               pending_projects=pending_projects, username=username,
                               client_logged_in=session['client_logged_in'])
    else:
        return redirect(url_for('login'))

@app.route('/photo/<path:filename>')
def get_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/photo/<int:project_id>', methods=['GET', 'POST'])
def photo_detail(project_id):
    project = get_project_by_id(project_id)

    if project is None:
        abort(404)

    if not project['ready']:
        low_quality_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'low_quality')
        project['src'] = [os.path.join(low_quality_folder, filename) for filename in project['src']]

    if request.method == 'POST':
        selected_photo = request.form.get('selected_photo')
        project['selected_photo'] = selected_photo
        flash('Photo selection saved.')

    return render_template('photo_detail.html', project=project)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
