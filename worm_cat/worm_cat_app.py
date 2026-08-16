"""WormCat Web Application controller and routing layer."""

import csv
from datetime import datetime
import json
import logging
import os
from shutil import make_archive

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from forms import WormCatForm
from services.r_runner import ExecuteR
from tasks.batch_tasks import celery, online_progress, send_async_email
from utils.data_2_flare_json import create_flare

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(__name__)

# Decoupled Celery configuration attached to Flask app context
app.config['CELERY_BROKER_URL'] = celery.conf.broker_url
app.config['CELERY_RESULT_BACKEND'] = celery.conf.result_backend

BASE_DIR: str = os.getcwd()
DYNAMIC_DIR: str = os.getenv('DYNAMIC_DIR', './static/dynamic')
DOWNLOAD_DIR: str = os.getenv('DOWNLOAD_DIR', './static/download')
SMTP_SENDER_EMAIL: str = os.getenv('SMTP_SENDER_EMAIL', 'wormcat@gmail.com')
USER_LOG_PATH: str = os.getenv('USER_LOG_PATH', './static/dynamic/users.txt')


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
        os.makedirs(os.path.dirname(USER_LOG_PATH), exist_ok=True)
        with open(USER_LOG_PATH, "a+") as myfile:
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

                out_dir_path = f"{DYNAMIC_DIR}/{dir_nm}"
                executeR = ExecuteR()
                executeR.worm_cat_fun(file_nm, out_dir_path, form.title.data, annotation_file, form.input_type.data)
                os.remove(file_nm)

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

        except Exception as e:
            logger.exception("Error processing WormCat run request: %s", e)
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


@app.route('/sunburst', methods=['GET'])
def sunburst():
    dir_param = request.args.get('dir', '')
    safe_dir = secure_filename(dir_param)
    if not safe_dir:
        return render_template('404.html'), 404
    html_dir = f"/static/dynamic/{safe_dir}/sunburst.html"
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


def is_excel_file(file_name: str) -> bool:
    """Helper function to test if a file extension represents an Excel format."""
    is_excel_ext = False
    index_of_dot = file_name.rfind('.')

    if index_of_dot != -1:
        extension = file_name[index_of_dot:]
        if extension in ['.xlsx', '.xls']:
            is_excel_ext = True
    return is_excel_ext


# =============================================================================== #
# Code for Batch processing routes


@app.route('/batch_process', methods=['GET', 'POST'])
def batch_process():
    error = None
    ui_data = {}
    if request.method == 'POST':
        if request.form.get('submit') == 'Send Email':
            email = session.pop('email', None)
            batch_user = session.pop('batch_user', None)
            annotation_file = session.pop('annotation_file', None)
            xsl_file_nm = session.pop('use_file', None)
            suffix = datetime.now().strftime("%b-%d-%Y-%H_%M_%S")
            params = {
                'email': email,
                'batch_user': batch_user,
                'annotation_file': annotation_file,
                'xsl_file_nm': xsl_file_nm,
                'suffix': suffix,
                'redis_channel': None,
            }
            send_async_email.delay(params)
            flash(f'Sending email to {email}')

    return render_template('wormcat-batch.html', ui_data=ui_data, error=error)


@app.route('/longtask', methods=['POST'])
def longtask():
    session.pop('email', None)
    batch_user = session.pop('batch_user', None)
    annotation_file = session.pop('annotation_file', None)
    xsl_file_nm = session.pop('use_file', None)
    suffix = datetime.now().strftime("%b-%d-%Y-%H_%M_%S")

    task = online_progress.apply_async()

    logger.info("Enqueued async batch task with task_id=%s", task.id)
    params = {
        'email': None,
        'batch_user': batch_user,
        'annotation_file': annotation_file,
        'xsl_file_nm': xsl_file_nm,
        'suffix': suffix,
        'redis_channel': task.id,
    }

    send_async_email.delay(params)
    return jsonify({}), 202, {'Location': url_for('taskstatus', task_id=task.id)}


@app.route('/status/<task_id>')
def taskstatus(task_id: str):
    task = online_progress.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...',
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', ''),
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),
        }
    return jsonify(response)


# =============================================================================== #
# Code for Error Handling and App Configuration


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


@app.route('/<path:path>')
def static_file(path: str):
    return app.send_static_file(path)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


# Load default config and override config from environment variables
app.debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
app.config.update(dict(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "secret key"),
    WTF_CSRF_ENABLED=os.getenv("WTF_CSRF_ENABLED", "True").lower() in ("true", "1", "t"),
))

if __name__ == "__main__":
    host: str = os.getenv("FLASK_HOST", "0.0.0.0")
    port: int = int(os.getenv("FLASK_PORT", "9000"))
    app.run(host=host, port=port)
