"""Handler for the "http" command
(Commands are issued on the command line, per the docopt syntax in __main__.py)
"""

# Standard library
import pprint
from urllib.parse import urlparse, urljoin
import os
import sys
import traceback
from functools import wraps


# Library
from flask import Flask, render_template, Markup, request
from werkzeug import secure_filename
from colorama import Fore
from eliot import Message, start_action

# Local
from cascade import quicklog
from cascade import cmd_check
from cascade import cmd_annotate
from cascade import cmd_apply_styles
from cascade import cmd_aggregate
from cascade.custom_exceptions import FatalUserError
from cascade.version import __version__
import markdown

pp = pprint.PrettyPrinter(indent=3)

# Initialize logging
qlog = quicklog.get_logger()
lprint = qlog.lprint

# This global will be set by http()
global_arguments = {}

app = Flask(__name__, static_url_path = "/static", static_folder = "static")
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_PATH'] = 200000 # 200 MB max file size
results_path_local = os.path.join('cascade', 'static', 'results')
results_path_web = 'static/results/'

# TODO: Make a proper key
app.secret_key = '8&6bkai(NIu9jb0asatebiar9##99yar0'

def log_route(func):
    ''' Logging decorator for flask functions wrapped with @app.route()

    Usage:
        @app.route('/some/path')
        @log_route
        def path_handler():
            <handler code>
    '''
    @wraps(func)
    def wrapped():
        kwargs = {}
        try:
            if request.files:
                kwargs['request.files'] = {key:file.filename for key, file in request.files.items()}
        except:
            pass

        try:
            if request.form['text']:
                kwargs['request.form["text"]'] = request.form['text']
        except:
            pass

        with start_action(action_type='http', path=request.path, **kwargs):
            return func()
    return wrapped

def http(arguments):
    """Provide a web interface

    This is the main entry point for starting the http server
    """
    global global_arguments
    global_arguments = arguments
    if arguments['-l']:
        host = '127.0.0.1'
        port = 5001
    else:
        host = '0.0.0.0'
        port = 5001
    Message.log(message_type="start_http_server", host=host, port=port)
    app.run(host=host, port=port, threaded=True,)

@app.after_request
def add_header(response):
    """Force all pages to be un-cached
    """
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.context_processor
def inject_template_globals():
    """ Injects globals available to all templates
    """
    return dict(version=__version__, privacy_warning=global_arguments['-w'])

@app.errorhandler(401)
def page_unauthorized(e):
    return render_template('401.html'), 401

@app.route('/')
@log_route
def home():
    return render_template('home.html')

@app.route('/help/changelog')
@log_route
def help_changelog():
    return render_md('CHANGELOG', 'CHANGELOG.md')

def render_md(report_name, md_filename):
    with open(md_filename, 'r') as in_file:
        content_md = in_file.read()
    content_html = markdown.markdown(content_md, extensions=['markdown.extensions.tables'])
    return render_template('basic.html', report_name=report_name, report=Markup(content_html))

@app.route('/check')
@log_route
def check():
    # with start_http_action():
    return render_template('util.html', cmd_name='Check', cmd_action='/do_check')

@app.route('/do_check', methods = ['GET', 'POST'])
@log_route
def do_check():
    # with start_http_action():
    if request.method == 'POST':
        file = request.files['file']
        return run_command('Check', file, cmd_check.check, returns_files=False)

@app.route('/annotate')
@log_route
def annotate():
    return render_template('util.html', cmd_name='Annotate', cmd_action='/do_annotate')

@app.route('/do_annotate', methods=['GET', 'POST'])
@log_route
def do_annotate():
    if request.method == 'POST':
        file = request.files['file']
        return run_command('Annotate', file, cmd_annotate.annotate)

@app.route('/annotate_reset')
@log_route
def annotate_reset():
    return render_template('util.html', cmd_name='Annotate Reset', cmd_action='/do_annotate_reset')

@app.route('/do_annotate_reset', methods=['GET', 'POST'])
@log_route
def do_annotate_reset():
    if request.method == 'POST':
        file = request.files['file']
        return run_command('Annotate Reset', file, cmd_annotate.annotate_reset)

@app.route('/apply_styles')
@log_route
def apply_styles():
    return render_template('util.html', cmd_name='Apply Styles', cmd_action='/do_apply_styles')

@app.route('/do_apply_styles', methods=['GET', 'POST'])
@log_route
def do_apply_styles():
    if request.method == 'POST':
        file = request.files['file']
        return run_command('Apply Styles', file, cmd_apply_styles.apply_styles)

@app.route('/aggregate')
@log_route
def aggregate():
    return render_template('util.html', cmd_name='Aggregation Report', cmd_action='/do_aggregate')

@app.route('/do_aggregate', methods=['GET', 'POST'])
@log_route
def do_aggregate():
    if request.method == 'POST':
        file = request.files['file']
        return run_command(
            'Aggregation Report',
            file,
            cmd_aggregate.aggregate,
            output_argument='<output.csv>')


def run_command(operation, 
                file,
                command,
                output_argument='<output.docx>',
                additional_arguments={},
                returns_files=True
                ):
    """ Execute a Cascade command

    Args:
        operation: Text description of the command
        file:
            EITHER
                The input file (will be assigned to the command argument
                '<requirements.docx> by default')
            OR
                A list of dictionaries of the form:
                {
                    'argument_name': <argument name string>
                    'file': <input file>
                }
                Each file will be passed to the target command under its associated
                argument name.

        command: The function to execute
        output_argument: The output file/dir argument
        returns_file: True if the command will generate an output file when
            it completes successfully.
        additional_arguments: A dict of additional arguments to be passed
            to the command.
    """

    # Parse parameter: file
    if isinstance(file, (list, tuple)):
        incoming_file_list = file
    else:
        incoming_file_list = [
            {
                'argument_name': '<requirements.docx>', 
                'file': file
            }
        ]

    # Process incoming file(s) and save them locally
    for incoming_file_info in incoming_file_list:
        raw_filename = secure_filename(incoming_file_info['file'].filename)
        if not raw_filename:
            return render_template('message.html', message='Error: You must specify a file to upload first.') 
        local_filename = os.path.join(app.config['UPLOAD_FOLDER'], raw_filename)
        incoming_file_info['file'].save(local_filename)
        incoming_file_info['raw_filename'] = raw_filename # filename (with no path)
        incoming_file_info['local_filename'] = local_filename # filename (with local path)

    # Build command arguments
    arguments = {
        # output_argument: out_filename_local
        output_argument: results_path_local
    }
    for incoming_file_info in incoming_file_list:
        arguments[incoming_file_info['argument_name']] = incoming_file_info['local_filename']
    arguments.update(additional_arguments)

    qlog.start_print_capture()
    qlog.clear_counters()
    results = None
    try:
        results = command(arguments)
    except FatalUserError as e:
        qlog.error('Exception: {}'.format(e))
    except Exception as e:
        return process_exception(e)
    finally:
        # Remove the uploaded (incoming) file(s)
        try:
            for incoming_file_info in incoming_file_list:
                qlog.debug('Deleting file:"{}"'.format(incoming_file_info['local_filename']))
                os.remove(incoming_file_info['local_filename'])
        except Exception as e:
            pass
    qlog.show_counters()
    report = to_html(qlog.stop_print_capture())
    if returns_files and results:
        for filename in results:
            report += (
                '<b>Download:</b> ' +
                '<a href="{}" download="{}">{}</a>'.format(
                    os.path.join(results_path_web, filename), 
                    filename,
                    filename) +
                '<br>\n' 
            )

    return render_template(
        'report.html',
        operation=operation,
        report=Markup(report))

def is_safe_url(target):
    """ Check that a redirect URL is safe to follow
    From http://flask.pocoo.org/snippets/62/
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def process_exception(exception):
    qlog.critical('EXCEPTION while processing HTTP request: "{}"\n{}'.format(
        type(exception).__name__,
        str(traceback.format_exc())
        ))
    if not global_arguments['-g']:
        return render_template('exception.html') 
    # Try to launch a postmortem debugger.
    # The order of preference is: pudb, ipdb, pdb
    #   pudb will not work on Windows machines, so it can be suppressed with the -p option.
    #   ipdb may not be installed on all machines, so it falls back to pdb if not installed
    e_traceback = sys.exc_info()[2]
    debugger_launched = False
    if global_arguments['-p']:
        try:
            # Use pudb debugger if available
            import pudb
            pudb.post_mortem(e_traceback)
            debugger_launched = True
        except:
            print('Could not launch pudb.  Falling back to ipdb/pdb.')
            pass
    if not debugger_launched:
        try:
            # Use iPython debugger if available
            import ipdb
            ipdb.post_mortem(e_traceback)
        except:
            # Fall back to pdb
            import pdb
            pdb.post_mortem(e_traceback)

def to_html(text):
    out_lines = []
    for line in text.split('\n'):
        indent = len(line) - len(line.lstrip(' '))
        out_line = html_indent(indent) + line.lstrip(' ')
        out_line = out_line.replace(Fore.YELLOW, '<span class=report-yellow>')
        out_line = out_line.replace(Fore.RED,    '<span class=report-red>')
        out_line = out_line.replace(Fore.GREEN,  '<span class=report-green>')
        out_line = out_line.replace(Fore.MAGENTA,'<span class=report-magenta>')
        out_line = out_line.replace(Fore.RESET,  '</span>')
        out_lines.append(out_line)
    out_lines.append('')
    return '<br>\n'.join(out_lines)

def html_indent(level):
    if level == 0:
        return ''
    return (
        '<span class=report-monospace>' +
        '&nbsp' * level + 
        '</span>'
        )
