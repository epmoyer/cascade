''' Utilities supporting the eliot logging framework

https://github.com/ScatterHQ/eliot
https://eliot.readthedocs.io/en/1.2.0/

'''
# Standard library
import json
from pathlib import Path
from functools import wraps

# Library
import eliot
from eliot import start_action
from flask import request

class rotating_logfile():
    ''' A log file rotation handler for the eliot logging framework'''
    def __init__(self, filename, num_logs=4, auto=True, max_bytes=5000000):
        '''
        If auto rotation is disabled, then the logs will only be rotated
            1) At startup (class init)
            2) By explicitly calling to do_rotate_check().
        '''
        self.filename = filename
        self.file = open(
            filename, 
            "a")
        self.max_bytes = max_bytes
        self.num_logs = num_logs
        self.auto = auto
        self.do_rotate_check()

        # Register this handler as an eliot logging destination
        eliot.add_destinations(self.write)

    def write(self, log_dict):
        ''' Write a dict to the logfile (as JSON) '''
        if self.auto:
            self.do_rotate_check()
        self.file.write(json.dumps(log_dict) + '\n')
        self.file.flush()

    def do_rotate_check(self):
        ''' Rotate the logs (if necessary)'''
        if self.num_logs > 1:
            if self.file.tell() > self.max_bytes:
                self._rotate_file(None, 1)

    def _rotate_file(self, current_id, next_id):
        ''' Rotate the log file with current_id to next_id

        For the active log file, current_id == None
        '''
        if current_id is None:
            self.file.close()

        current_suffix = '' if current_id is None else f'.{current_id}'
        current_file = Path(self.filename + current_suffix)
        next_file = Path(self.filename + f'.{next_id}')

        # If next file exists, then bump its suffix
        if next_file.is_file():
            if next_id == self.num_logs:
                # Delete the next file
                next_file.unlink()
            else:
                # Bump the next file
                self._rotate_file(next_id, next_id + 1)

        # Rename current file
        current_file.rename(next_file)

        if current_id is None:
            # Open new base file
            self.file = open(self.filename, "a")

    def close(self):
        ''' Close the logfile '''
        self.file.close()

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
        with start_action(action_type='http', path=request.path):
            return func()
    return wrapped

def log_function(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        with start_action(action_type=func.__name__):
            return_value = func(*args, **kwargs)
            return return_value
    return wrapped