''' Quicklog. A helper class to facilitate logging.

* Provides easy setup and tear-down of a timestamped event log.
* Provides helper methods that simultaneously log to the event log and
  to the console (based on settable 'logging_level' and 'print_level').
* Provides colorization of (console printed) log level designations
  (WARNING, INFO, etc.).

'''

from __future__ import print_function
import sys
import logging
import logging.handlers
import traceback
from colorama import init, Fore
from eliot import Message
init(autoreset=True)

__version__ = '0.3'

class Quicklog(object):
    def __init__(
            self,
            log_filename='output.log',
            logging_level=logging.INFO,
            print_level=logging.WARNING,
            enable_colored_printing=True,
            enable_colored_logging=False,
            maxBytes=1000000,
            backupCount=5,
            logger_name='default_logger'):

        self._enable_colored_printing = enable_colored_printing
        self._enable_colored_logging = enable_colored_logging
        self._print_level = print_level
        self._log_filename = log_filename
        self._logging_level = logging_level
        self._color_clear = Fore.RESET
        self._logger_name = logger_name
        self._log_color = {
            logging.DEBUG: Fore.BLUE,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.MAGENTA
        }
        self._version = __version__

        self._log_level_name = {
            logging.DEBUG: 'DEBUG',
            logging.INFO: 'INFO',
            logging.WARNING: 'WARNING',
            logging.ERROR: 'ERROR',
            logging.CRITICAL: 'CRITICAL'
        }
        if enable_colored_logging:
            color = Fore.YELLOW
            color_clear = Fore.RESET
        else:
            color = ''
            color_clear = ''

        self._log_levels = [
                logging.DEBUG,
                logging.INFO,
                logging.WARNING,
                logging.ERROR,
                logging.CRITICAL
            ]
        self.clear_counters()

        self._print_capture = ""
        self._print_capture_enabled = False

        self._handler = logging.handlers.RotatingFileHandler(
              log_filename, maxBytes=maxBytes, backupCount=backupCount)
        formatter = logging.Formatter(color+'%(asctime)s'+color_clear+' %(message)s')
        self._handler.setFormatter(formatter)

        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(logging_level)
        self._logger.addHandler(self._handler)

        self._register_logger()

    def clear_counters(self):
        self._counters = {}
        for level in self._log_levels:
            self._counters[level] = 0

    def _register_logger(self):
        if 'quicklog_loggers' not in globals():
            globals()['quicklog_loggers'] = {}
        else:
            if self._logger_name in globals()['quicklog_loggers']:
                raise RuntimeError(
                    'Could not create a Quicklog logger named "' +
                    self._logger_name +
                    '"because one already exists.  Use quicklog.get_logger ' +
                    'to get an existing logger by name.'
                    )
        # Register the logger
        globals()['quicklog_loggers'][self._logger_name] = self

    def _unregister_logger(self):
        if self._logger_name not in globals()['quicklog_loggers']:
                raise RuntimeError(
                    'Could not remove Quicklog logger named "' +
                    self._logger_name +
                    '"because it was not registered.'
                    )
        del(globals()['quicklog_loggers'][self._logger_name])

    def show_counters(self, min_report_level=logging.WARNING):
        report_text = ''
        for level in self._log_levels:
            if level >= min_report_level:
                count = self._counters[level]
                if count > 0:
                    if report_text:
                        report_text += '\n'
                    report_text += (
                        ' ' + 
                        '{:>4} '.format(count) +
                        (self._log_color[level] if self._enable_colored_printing else '') +
                        self._log_level_name[level] +
                        ('S' if count > 1 else '') +
                        (self._color_clear if self._enable_colored_printing else '')
                    )

        if report_text:
            self.lprint('Status summary:\n{}'.format(report_text))


    def get_count(self, log_level):
        if log_level in self._counters:
            return self._counters[log_level]
        else:
            return 0

    def stop(self):
        '''Stop logging

        Removes the logging handler.
        It is generally not necessary to call this function.  It is used during testing to stop each
        (test) instance of Quicklog before a new instance is created.  Most apps create a single
        instance of Quicklog, and such apps need not call stop before terminating.
        '''
        self._logger.removeHandler(self._handler)
        self._handler = None
        self._unregister_logger()

    def debug_is_enabled(self):
        '''True if current logging level includes DEBUG'''
        return self._logging_level <= logging.DEBUG

    def start_print_capture(self):
        self._print_capture = ""
        self._print_capture_enabled = True
    
    def stop_print_capture(self):
        self._print_capture_enabled = False
        result = self._print_capture
        self._print_capture = ""
        return result

    def begin(self, app_identification_text='', show=True):
        # Log execution start
        self._logger.info('------------------------------ BEGIN ------------------------------ ')

        # Print/log application identifying info (typically app name and version)
        if app_identification_text:
            self._logger.info(app_identification_text)
            if show:
                self._print(app_identification_text)
                self._print('---------------------------------------')
        if show:
            self._print('(Logging to: "{}")'.format(self._log_filename))

    def end(self):
         # Log execution end
        self._logger.info('------------------------------- END ------------------------------- ')

    def debug(self, message, quiet=False):
        self.log(message, logging.DEBUG, quiet)

    def info(self, message, quiet=False):
        self.log(message, logging.INFO, quiet)

    def warning(self, message, quiet=False):
        self.log(message, logging.WARNING, quiet)

    def error(self, message, quiet=False):
        self.log(message, logging.ERROR, quiet)

    def critical(self, message, quiet=False):
        self.log(message, logging.CRITICAL, quiet)

    def fatal_exception(self, e):
        """Notify user (tersely) of a fatal exception. Write the traceback to the log"""
        self.error('(INTERNAL): {}: {}. Details written to log.'.format(type(e).__name__, str(e)))
        self.critical(str(traceback.format_exc()), quiet=True)

    def lprint(self, message):
        """Logs the message (at "INFO" level) and prints the message as-is (i.e. with no "INFO: " prefix)"""
        # Unicode is re-encoded for stdout, replacing any encoding errors, per
        # http://stackoverflow.com/questions/14630288/unicodeencodeerror-charmap-codec-cant-encode-character-maps-to-undefined
        message = str(message)
        self._print(message.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding))
        self.log(message, logging.INFO, quiet=True)

    def log(self, message, log_level, quiet=False):
        log_prefix = self._log_level_name[log_level]
        if self._log_color[log_level]:
            color = self._log_color[log_level]
            color_clear = self._color_clear
        else:
            color = ''
            color_clear = ''

        self._counters[log_level] += 1

        # Get string representation of message
        message = str(message)
            
        print_prefix = log_prefix
        self._logger.log(
            log_level,
            '{}{}{}: {}'.format(
                color if self._enable_colored_logging else '',
                print_prefix,
                color_clear if self._enable_colored_logging else '',
                message.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding)))
        
        if log_level >= self._print_level and not quiet:
            # Unicode is re-encoded for stdout, replacing any encoding errors, per
            # http://stackoverflow.com/questions/14630288/unicodeencodeerror-charmap-codec-cant-encode-character-maps-to-undefined
            self._print('{}{}{}: {}'.format(
                color if self._enable_colored_printing else '',
                print_prefix,
                color_clear if self._enable_colored_printing else '',
                message.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding)
                ))

        # Log to eliot
        if log_level >= self._logging_level:
            Message.log(
                message_type='qlog',
                level=self._log_level_name[log_level],
                message=message.encode(
                    sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding)
                )

    def _print(self, text):
        if self._print_capture_enabled:
            self._print_capture += text + '\n'
        print(text)

def get_logger(logger_name='default_logger'):
    if 'quicklog_loggers' in globals() and logger_name in globals()['quicklog_loggers']:
        return globals()['quicklog_loggers'][logger_name]
    raise ValueError('No Quicklog logger with the name "{}" exists'.format(logger_name))
