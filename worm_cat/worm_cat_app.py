from flask import Flask, request, session, redirect, url_for, render_template, flash, jsonify
from forms import WormCatForm, AdminForm, LoginForm
from shutil import copyfile, make_archive

from utils.email_utility import email_results, send_message, construct_message_with_html
from utils.execute_r import ExecuteR
from utils.data_2_flare_json import create_flare
from utils.simple_encode import decode, KEY
from datetime import datetime
import json
import logging
import csv
import os
from wormcat_batch.wormcat_batch import run_wormcat_batch
from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded
from werkzeug.utils import secure_filename
import random
import time
import redis

redis_server = redis.Redis(host='localhost', port=6379, db=0)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
# Used for batch processing Wormcat
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

BASE_DIR = os.getcwd()
DYNAMIC_DIR = "./static/dynamic"
DOWNLOAD_DIR = "./static/download"


# =============================================================================== #
# Code for Wormcat data processing (CSV or Input field)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = WormCatForm()
    error = None
    ui_data = {}

    if form.validate_on_submit():
        template_to_render = 'wormcat-report.html'
        suffix = datetime.now().strftime("%b-%d-%Y-%H_%M_%S")

        # Capture the users of the system
        user_txt = "{}/users.txt".format(DYNAMIC_DIR)
        with open(user_txt, "a+") as myfile:
            myfile.write(
                "{}, {}, {}, {}\n".format(suffix, request.form['name'], request.form['email'], form.title.data))

        try:
            # Note: Annotation files are versioned by date
            active_annotation_file = '{}/active_annotation_file.json'.format(DYNAMIC_DIR)
            with open(active_annotation_file) as active:
                active_annotations = json.load(active)
            active_version = active_annotations[form.annotation_type.data]

            annotation_file = "{}_{}.csv".format(form.annotation_type.data, active_version)

            is_excel_file = session.pop('is_excel_file', None)
            if is_excel_file:
                email = request.form['email']
                batch_user = request.form['name']
                session['email'] = email
                session['batch_user'] = batch_user
                session['annotation_file'] = annotation_file
                return redirect(url_for('batch_process'))
            else:
                dir_nm = form.title.data
                dir_nm = dir_nm.replace(' ', '-')
                dir_nm = "{}_{}".format(dir_nm, suffix)
                file_nm = "worm-cat_{}.csv".format(suffix)

                # Note: The input type becomes the header of the csv file to process
                header = request.form['input_type']

                with open(file_nm, "w") as fo:
                    fo.write(header)
                    fo.write('\r\n')
                    use_file = session.pop('use_file', None)
                    if use_file is not None:
                        with open(use_file, "r") as fi:
                            for line_in in fi:
                                fo.write(line_in)
                        os.remove(use_file)
                    else:
                        fo.write(request.form['rgs'])

                executeR = ExecuteR()
                executeR.worm_cat_fun(file_nm, dir_nm, form.title.data, annotation_file, form.input_type.data)
                os.remove(file_nm)

                # title_nm = (form.title.data).replace(' ', '-').lower()
                dir_path = "{}/{}/rgs_fisher_cat1_apv.csv".format(DYNAMIC_DIR, dir_nm)
                cat1_apv = csv.DictReader(open(dir_path))
                dir_path = "{}/{}/rgs_fisher_cat2_apv.csv".format(DYNAMIC_DIR, dir_nm)
                cat2_apv = csv.DictReader(open(dir_path))
                dir_path = "{}/{}/rgs_fisher_cat3_apv.csv".format(DYNAMIC_DIR, dir_nm)
                cat3_apv = csv.DictReader(open(dir_path))

                create_flare(dir_nm)
                ui_data = {'dir': dir_nm, 'cat1_apv': cat1_apv, 'cat2_apv': cat2_apv, 'cat3_apv': cat3_apv}

                # Create Zip with flare data
                root_dir = "{}/{}".format(DYNAMIC_DIR, dir_nm)
                base_name = "{}/{}".format(DOWNLOAD_DIR, dir_nm)
                make_archive(base_name, 'zip', root_dir=root_dir)

        except:
            template_to_render = 'wormcat-error.html'

        return render_template(template_to_render,
                               ui_data=ui_data,
                               form=form)

    session.pop('use_file', None)
    return render_template('index.html',
                           ui_data={},
                           form=form,
                           error=error)


@app.route('/demos', methods=['GET'])
def demos():
    return render_template('wormcat-demos.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        user_name = decode(KEY, "w5TDnMOEw57DkMOZwpI=")
        passwd = decode(user_name, "wpTCrsKUw5zDl8OGw6DDlcOYw5XDlcOaw5M=")

        if request.form['user_name'] == user_name and request.form['password'] == passwd:
            session['user'] = {"user_name": user_name}
            return redirect(url_for('index'))
        else:
            error = "Username and or password is incorrect."

    return render_template('login.html',
                           ui_data={},
                           form=form,
                           error=error)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


# Not yet implemented
@app.route('/admin', methods=['GET', 'POST'])
def admin_form():
    form = AdminForm()
    error = None
    ui_data = {}
    return render_template('admin.html',
                           ui_data=ui_data,
                           form=form,
                           error=error)


@app.route('/sunburst', methods=['GET'])
def sunburst():
    dir = request.args.get('dir')
    html_dir = "/static/dynamic/{}/sunburst.html".format(dir)
    return redirect(html_dir)


@app.route("/sendfile", methods=["POST"])
def send_file():
    fileob = request.files["file2upload"]
    filename = secure_filename(fileob.filename)
    prefix = datetime.now().strftime("%b-%d-%Y-%H_%M_%S")
    save_path = "{}/{}-{}".format(DYNAMIC_DIR, prefix, filename)
    fileob.save(save_path)
    if is_excel_file(filename):
        session['is_excel_file'] = True
    else:
        session['is_excel_file'] = False

    session['use_file'] = save_path
    return "successful_upload"


# Helper function to test if file extension is excel
def is_excel_file(file_name):
    logger.debug("file_name={}".format(file_name))
    is_excel_ext = False
    index_of_dot = file_name.rfind('.')

    if index_of_dot != -1:
        extension = file_name[index_of_dot:]
        if extension in ['.xlsx', '.xls']:
            is_excel_ext = True
    return is_excel_ext


# =============================================================================== #
# Code for Batch processing

# wormcat-batch.html function update_progress(status_url, status_div, loop_limit)
# loop_limit must also be in sync with TASK_TIME_LIMIT
TASK_TIME_LIMIT=510
TASK_SOFT_TIME_LIMIT=500

@celery.task(time_limit=TASK_TIME_LIMIT, soft_time_limit=TASK_SOFT_TIME_LIMIT)
def send_async_email(params):
    try:
        print("send_async_email STARTED  !!!!")
        dir_nm = run_wormcat_batch(params['batch_user'],
                                   params['annotation_file'],
                                   params['xsl_file_nm'],
                                   redis_channel=params['redis_channel'],
                                   suffix=params['suffix'])
        root_dir = "{}/{}".format(DYNAMIC_DIR, dir_nm)
        base_name = "./static/download/{}".format(dir_nm)
        make_archive(base_name, 'zip', root_dir=root_dir)
        zip_file = "{}.zip".format(base_name)
        email = params['email']
        if email is not None:
            email_results(params['email'], zip_file)
            os.remove(zip_file)
    except SoftTimeLimitExceeded:
        print("SoftTimeLimitExceeded  !!!! {} XX".format(BASE_DIR))
        err_file_nm = "{}/static/dynamic/async_email_timeout.txt".format(BASE_DIR)
        with open(err_file_nm, "a+") as err_file:
            err_file.write(
                "{}, {}, {}\n".format(params['email'], params['xsl_file_nm'], params['redis_channel']))
        receiver = params['email']
        if receiver is not None:
            sender = "wormcat@gmail.com"
            message_text = "Sorry an Error occurred during processing of your batch file.\nPlease try again later."
            subject = "Error running Wormcat"
            message = construct_message_with_html(subject, sender, receiver, message_text)
            send_message(sender, receiver, message)


@app.route('/batch_process', methods=['GET', 'POST'])
def batch_process():
    error = None
    ui_data = {}
    logging.debug("request {}".format(request.form))
    if request.method == 'POST':
        if request.form['submit'] == 'Send Email':
            email = session.pop('email')
            batch_user = session.pop('batch_user')
            annotation_file = session.pop('annotation_file')
            xsl_file_nm = session.pop('use_file')
            suffix = datetime.now().strftime("%b-%d-%Y-%H_%M_%S")
            params = {'email': email, 'batch_user': batch_user, 'annotation_file': annotation_file,
                      'xsl_file_nm': xsl_file_nm, 'suffix': suffix, 'redis_channel': None}
            send_async_email.delay(params)
            flash('Sending email to {0}'.format(email))

    return render_template('wormcat-batch.html', ui_data=ui_data, error=error)


def get_message(channel, timeout=10):
    ret_val = {'name': 'ERROR', 'value': 'Unknown Error'}
    done = False
    start_time = time.time()
    while not done:
        message = redis_server.rpop(channel)
        if message:
            try:
                data = message.decode("utf-8")
                ret_val = json.loads(data)
            except (UnicodeDecodeError, AttributeError):
                ret_val = {'name': 'ERROR', 'value': 'Error decoding message'}
            done = True
        else:
            time.sleep(.25)

        current_time = time.time()
        if (current_time - start_time) > timeout:
            done = True
            ret_val = {'name': 'TIMEOUT', 'value': timeout}
    return ret_val


@celery.task(bind=True, time_limit=TASK_TIME_LIMIT)
def online_progress(self):
    done = False
    download_url = "/bad"
    current = 0
    increment = 10
    while not done:
        message = get_message(self.request.id)
        if message['name'] == 'DONE':
            download_url = "./static/download/{}.zip".format(message['value'])
            done = True
        elif message['name'] == 'SHEETS':
            current += increment
            self.update_state(state='PROGRESS',
                              meta={'current': current, 'total': 100, 'status': 'Preparing Sheets'})
            time.sleep(2)
            increment = int(80 / message['value'])
        elif message['name'] == 'MESSAGE':
            current += increment
            self.update_state(state='PROGRESS',
                              meta={'current': current, 'total': 100, 'status': message['value']})
            time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Batch completed!', 'result': download_url}


@app.route('/longtask', methods=['POST'])
def longtask():
    email = session.pop('email')
    batch_user = session.pop('batch_user')
    annotation_file = session.pop('annotation_file')
    xsl_file_nm = session.pop('use_file')
    suffix = datetime.now().strftime("%b-%d-%Y-%H_%M_%S")

    task = online_progress.apply_async()

    logging.debug("TASK_ID type {} value {}".format(type(task.id), task.id))
    params = {'email': None, 'batch_user': batch_user, 'annotation_file': annotation_file,
              'xsl_file_nm': xsl_file_nm, 'suffix': suffix, 'redis_channel': task.id}

    send_async_email.delay(params)
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = online_progress.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':  # task.state == 'PROGRESS'
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


# =============================================================================== #
# Code for Error Handling and App Configuration

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


# Retrieve data from 'static' directory. Used most typically for rendering images.
@app.route('/<path:path>')
def static_file(path):
    return app.send_static_file(path)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


# Load default config and override config from an environment variable
app.debug = True
app.config.update(dict(
    SECRET_KEY='secret key',
    WTF_CSRF_ENABLED=True,
))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9000)
