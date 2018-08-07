'''Dispatch cascade command (from command line) to the relevant command handler module'''

# Library
from eliot import Message

# Local
from cascade import cmd_check
from cascade import cmd_annotate
from cascade import cmd_debug_dump
from cascade import cmd_debug_dumpxl
from cascade import cmd_apply_styles
from cascade import cmd_http
from cascade import quicklog

qlog = quicklog.get_logger()

def main(arguments):
    '''Dispatch cascade command (from command line) to the relevant command handler module'''

    jump_table = {
        'check':            cmd_check.check,
        'annotate':         cmd_annotate.annotate,
        'annotate-reset':   cmd_annotate.annotate_reset,
        'debug-dump':       cmd_debug_dump.dump,
        'debug-dumpxl':     cmd_debug_dumpxl.dump,
        'apply-styles':     cmd_apply_styles.apply_styles,
        'http':             cmd_http.http,
    }

    for command, handler in jump_table.items():
        if command in arguments and arguments[command]:
            Message.log(message_type='dispatch_command', command=command)
            handler(arguments)
            return

    qlog.error("The requested operation is not yet implemented.")
