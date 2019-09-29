import os
from flask import Flask, render_template, request, redirect, send_from_directory, send_file, url_for
from flask_compress import Compress
from datetime import datetime, date
from contextlib import suppress
from functions import get_album_art, get_announcements
from werkzeug.utils import secure_filename
import sys
import requests
from werkzeug.middleware.proxy_fix import ProxyFix
import psycopg2

# DATABASE_URL = os.environ.get('DATABASE_URL', False)
# DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', '')
# if DATABASE_URL: conn = psycopg2.connect(DATABASE_URL, sslmode='require')
# else:
#     try:
#         conn = psycopg2.connect(database='mywebsite', user='postgres', password=DATABASE_PASSWORD)
#     except psycopg2.OperationalError:
#         conn = psycopg2.connect(database='postgres', user='postgres', password=DATABASE_PASSWORD)
#         conn.autocommit = True
#         cursor = conn.cursor()
#         cursor.execute(f'CREATE DATABASE mywebsite;')
#         cursor.close()
#         conn.close()
#         conn = psycopg2.connect(database='mywebsite', user='postgres', password=DATABASE_PASSWORD)

# conn.autocommit = True
# cursor = conn.cursor()
# cursor.execute('CREATE TABLE IF NOT EXISTS visitors (date TIMESTAMPTZ, ip_address TEXT, user_agent TEXT, page_accessed TEXT);')

announcements = []
DEVELOPMENT_SETTING = bool(os.environ.get('DEVELOPMENT', False))

if not DEVELOPMENT_SETTING:
    url = 'https://cssminifier.com/raw'
    data = {'input': open('static/css/style.css', 'rb').read()}
    r = requests.post(url, data=data)
    with open('static/css/style.css', 'w') as f:
        f.write(r.text)

    data = {'input': open('static/css/dark.css', 'rb').read()}
    r = requests.post(url, data=data)
    with open('static/css/dark.css', 'w') as f:
        f.write(r.text)


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 if DEVELOPMENT_SETTING else 604800
app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=1)
Compress(app)


# @app.before_request
# def save_ip():
#     requested_url = request.url
#     if 'static' not in requested_url and 'visitors' not in requested_url and 'favicon' not in requested_url:
#         cursor.execute(f"INSERT INTO visitors VALUES ('{datetime.now()}','{request.remote_addr}','{request.headers.get('User-Agent')}','{requested_url}')")


@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers: response.cache_control.max_age = 'no-store'
    return response


@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.html'), 404


@app.route('/favicon.ico')
def favicon():
    resp = send_from_directory(app.static_folder, 'images/favicon.ico')
    resp.cache_control.max_age = 7257600
    return resp


@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/')
def home(): return render_template('home.html')


@app.route('/about/')
def about(): return render_template('about.html')


@app.route('/resume/')
def resume():
    return render_template('resume.html')


@app.route('/formula-calculator/')
@app.route('/repls/')
@app.route('/programs/')  # todo: turn this into a drop down menu
def formula_calculator(): return render_template('formula_calculator.html')


@app.route('/contact/')
def contact(): return render_template('contact.html')


@app.route('/resources/')
def resources(): return render_template('resources.html')


@app.route('/search-album-art/', methods=['GET'])
def search_album_art():
    artist = request.args.get('artist')
    track = request.args.get('track')
    if None in (artist, track) or '' in (artist, track):
        image_url, alt_text = 'image not found', ''
    else:
        try:
            image_url, alt_text = get_album_art(artist, track), f'{track} Album Cover'
        except IndexError:
            image_url, alt_text = 'image not found', ''
    return render_template('search_album_art.html', image_url=image_url, alt_text=alt_text)


@app.route('/krunker/', methods=['GET'])
@app.route('/krunker-stats/', methods=['GET'])
def krunker_stats():
    krunker_username = request.args.get('krunker-username')
    if krunker_username in (None, ''):
        return render_template('krunker_stats.html')
    return redirect(f'https://krunker.io/social.html?p=profile&q={krunker_username}')


@app.route('/shift/')
def shift():
    return redirect('https://elijahlopez.itch.io/shift')


if DEVELOPMENT_SETTING:
    @app.route('/test/', methods=['GET', 'POST'])
    def test():
        if request.method == 'POST' and 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                with open('test.txt', 'w') as f:
                    f.write('test\n')
                filename = secure_filename(file.filename)
                save_name = filename.replace('_', ' ')
                save_path = os.path.join('static/MP3Editor', save_name)
                file.save(save_path)
                # do other stuff
                return url_for('static', filename=f'MP3Editor/{save_name}')
        return render_template('test.html')
    
    @app.route('/test2/')
    def test2():
        return render_template('test2.html')


@app.route('/done/<filename>', methods=['GET', 'POST'])
def upload():
    return str('file' in request.files)


@app.route('/projects/')
@app.route('/software/')
def software():
    # chrome: class=e-f-ih; .split(' users')[0]
    # firefox: class=MetadataCard-content
    # look at announcements for scraping logic
    g_dark_theme_chrome = 'https://chrome.google.com/webstore/detail/ohhpliipfhicocldcakcgpbbcmkjkian/'
    g_dark_theme_ffox   = 'https://addons.mozilla.org/addon/dark-theme-for-google-searches/'
    matte_chrome        = 'https://chrome.google.com/webstore/detail/matte-black-theme/ioadlgcadgdbcchobmhlipionnphmfja'
    matte_ffox_2        = 'https://addons.mozilla.org/addon/matte-black-v2/'
    github_theme_chrome = 'https://chrome.google.com/webstore/detail/github-dark-theme/odkdlljoangmamjilkamahebpkgpeacp'
    github_theme_ffox   = 'https://addons.mozilla.org/addon/github-dark-theme/'
    # music_caster        = 'https://github.com/elibroftw/music-caster'
    # music_editor        = 'https://github.com/elibroftw/mp3-editor'
    return render_template('software.html')


@app.route('/todo/')
def todo():
    # TODO: I want this to be a todo list that will automatically update the github repo so that it gets carried on
    # TODO: I would have to implement a username and password to only allow me to edit it
    # TODO: Learn databases
    return render_template('404.html')


@app.route('/menus/')
def menus():
    return render_template('menus.html')


@app.route('/rbhs/')
def rbhs():
    global announcements
    today = date.today()
    d2 = os.environ.get('RBHS')
    if d2 is not None: d2 = datetime.strptime(d2, '%d/%m/%Y').date()
    if d2 is None or not announcements or d2 < today:
        announcements = get_announcements()
        if announcements:
            temp = ''
            i = 1
            for title, desc in announcements:
                temp += f'<button class="accordion" id="no.{i}">{title}</button><div class="panel"><p>{desc}</p></div>'
            os.environ['RBHS'] = today.strftime('%d/%m/%Y')
            announcements = temp
        else: announcements = "<p style='color: white;'>There are no announcements for today</p>"
    return render_template('rbhs.html', announcements=announcements)


# @app.route('/stats/')
# def stats():
#     # all time should only be updated daily later onwards...
#     # SELECT * from table where date >= '2010-03-01' AND date < '2010-04-01'
#     cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM visitors')
#     all_time = cursor.fetchone()[0]
#     return render_template('stats.html', all_time=all_time, monthly='N/A', today='N/A')


@app.route('/visitors/')
def visitors():
    cursor.execute('SELECT * FROM visitors')
    rows = cursor.fetchall()
    temp = ''
    for row in rows:
        row = [str(item) for item in row]
        temp += ', '.join(row)
        temp += '<br>'
    return temp


@app.route('/to_ico/')
def to_ico():
    return render_template('to_ico.html')

# @app.route('/get_ico/', methods=['POST'])
# def get_ico():
#     file = request.args.get('track')
#     if file is None:
#         file = ''
#     return render_template('to_ico.html')


if __name__ == '__main__':
    assert os.path.exists('.env')
    if not os.path.exists('static/MP3Editor'): os.mkdir('static/MP3Editor')
    app.run(debug=True, host='', port=5000)
