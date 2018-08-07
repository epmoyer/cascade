""" Cascade main entry point

Passing '--develop' on the command line will enable use of the developer options.
The developer options are beta/debug features and are not intended for production
use.
"""

USAGE = (
"""Usage:
    cascade [-dgp] check <requirements.docx>
    cascade [-dgp] annotate <requirements.docx>
    cascade [-dgp] annotate-reset <requirements.docx>
    cascade [-dgplw] http
    cascade -h | --help
    cascade --version
""")

DEVELOPER_USAGE = (
"""
    cascade [-dgp] debug-dump <requirements.docx>
    cascade [-dgp] debug-dumpxl <CrdFeatureInfo.xlsm>
    cascade [-dgp] apply-styles <requirements.docx>
""")

OPTIONS =(
"""
Options:
  -h --help   Show this screen.
  --version   Show version
  -d          Debug logging
  -g          Launch debugger on exception
  -p          When launching debugger, try to use pudb
  -l          Host http locally (127.0.0.1)
  -w          Enable privacy warning
 """)

# Standard library
import os
import sys
import logging
import pprint

# Libraries
from docopt import docopt

# Local
from cascade.quicklog import Quicklog
from cascade.custom_exceptions import FatalUserError
from cascade.version import __version__
from eliot import Message


pp = pprint.PrettyPrinter(indent=3)

# Get arguments
if '--develop' in sys.argv:
    # Remove the '--develop' argument so that docopt will not see it
    sys.argv.remove('--develop')
    developer_usage = '\n'.join([line for line in DEVELOPER_USAGE.split('\n') if line.strip()])
    USAGE += developer_usage
arguments = docopt(USAGE + '\n' + OPTIONS, version=__version__)

# Start quicklog logging
qlog = Quicklog(
    log_filename=os.path.join('log', 'cascade.log'),
    logging_level=logging.DEBUG if arguments['-d'] else logging.INFO,
    maxBytes=5000000,
    backupCount=8)

qlog.begin('Cascade, Version {}'.format(__version__))

#---------------------------------------------------------------------
# Modules which use quicklog cannot be imported until the logger
# has been initialized, so they are imported here.
#---------------------------------------------------------------------
from cascade.main import main
from cascade.util_eliot import rotating_logfile
#---------------------------------------------------------------------

# Start eliot logging
eliot_handler = rotating_logfile(
    os.path.join('log', 'cascade.eliot.log'),
    auto=False)
Message.log(
    message_type="startup",
    command_line=' '.join(sys.argv),
    arguments=arguments,
    version=__version__)

if arguments['-w']:
    print('Privacy warning enabled.')

try:
    main(arguments)
except FatalUserError as e:
    # "Normal" user errors which cause application to halt
    qlog.error(str(e))
except Exception as e:
    # Unexpected exceptions (i.e. application crashes)
    qlog.fatal_exception(e)
    if arguments['-g']:
        #Launch postmortem debugger
        print('Launching postmortem debugger...')

        import traceback
        traceback.print_exc()
        e_traceback = sys.exc_info()[2]

        # Try to launch a postmortem debugger.
        # The order of preference is: pudb, ipdb, pdb
        #   pudb will not work on Windows machines, so it can be suppressed with the -p option.
        #   ipdb may not be installed on all machines, so it falls back to pdb if not installed
        debugger_launched = False
        if arguments['-p']:
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

qlog.show_counters() # Show WARNING/ERROR/CRITICAL counts (if nonzero)
qlog.end()
Message.log(message_type="exit")
eliot_handler.close()
