
# Standard library
import os
import sys
import json
from json import JSONDecodeError
import re
from collections import namedtuple, OrderedDict

# Libraries
import pandas as pd
import jsonschema
from colorama import Fore
import openpyxl
from openpyxl.styles import Alignment, Border, Side, PatternFill, Color
from openpyxl.utils import get_column_letter

# Local
from cascade import quicklog
from cascade.bomstrip import open_and_seek_past_bom

qlog = quicklog.get_logger()
lprint = qlog.lprint

def make_json(data_dict, simple=None):
    """Make well formatted JSON for insertion into cascade word docs.

    JSON will be enclosed by '$ like: '${"key":"value"}$'
    JSON will be on one line (simple) if it contains only one key/value pair, or if
         the argument simple==true
    """
    if simple is None:
        # Default to simple as long as the JSON contains only one item and
        # that items is not a dict.
        simple = False
        if len(data_dict) <= 1:
            for key in data_dict:
                if not isinstance(data_dict[key], dict):
                    simple = True

    if simple:
        return '${}$'.format(json.dumps(data_dict, separators=(', ', ':')))
    return '${}$'.format(json.dumps(data_dict, indent=4, separators=(',', ':'))).replace('${\n  ', '${')

def make_json_autoformat(data_dict):
    """Makes JSON formatted for inclusion in a Word doc according to dict content"""
    if not is_shortform_dict(data_dict):
        return make_json(data_dict, simple=False)
    if 'satisfies' not in data_dict:
        return make_json(data_dict, simple=True)
    if len(data_dict['satisfies']) <= 1:
        return make_json(data_dict, simple=True)

    # Use multi-line formatting because there are multiple 'satisfies' directives
    json_text = make_json(data_dict, simple=False)
    # Remove carriage return between "id" and "method" (for a little more compactness)
    json_text = json_text.replace(',\n    "method"', ', "method"')
    return json_text

def json_to_dict(json_text):
    """Parse JSON text and return as a python dict

    On error: logs the error and returns None
    """

    json_dict = None
    try:
        json_dict = json.loads(
            json_text,
            object_pairs_hook=OrderedDict  # Preserve item order by using an OrderedDict
            )
    except JSONDecodeError as err:
        json_error_text = json_text
        # Show error location for errors of the form:
        #       "Reported JSON decode error: Expecting ',' delimiter: line 1 column 89 (char 88)"
        # pylint: disable=locally-disabled, anomalous-backslash-in-string
        result = re.search('line (?P<line>\d+) column (?P<column_loc>\d+) \(char (?P<char_loc>\d+)\)', str(err))
        if result:
            # Colorize the break between good/bad text
            json_error_text = (
                Fore.GREEN +
                json_text[:int(result.group('char_loc'))] +
                Fore.RESET +
                Fore.RED +
                json_text[int(result.group('char_loc')):] +
                Fore.RESET
                )

        qlog.error('Could not decode cascade directive (JSON parsing encountered error).'
                   + '\n   Reported JSON decode error: {}'.format(err)
                   + '\n   JSON string being parsed:'
                   + '\n      {}'.format(json_error_text)
                   + '\n   JSON sting with whitespace condensed:'
                   + '\n      {}'.format(' '.join(json_error_text.split()))
                  )
    return json_dict

def extract_json_from_directive(text):
    '''Take a sting of form "<junk>${<content>}$<junk2>" and return "${<content>}$" '''
    if '${' not in text or '}$' not in text:
        raise ValueError('Expected directive to contain "${" and "}$"')
    return '{' + text.split('${')[1].split('}$')[0] + '}'

def extract_directives_from_text(text):
    '''Return all directives appearing in a string of text

    Returns a list of all substrings of the form '${<content>}$'
    Example: 'Spam ${eggs}$ SpAm ${SPAM}$ eggs and spam'--> ['${eggs}$'.'${SPAM}$']
    '''
    return re.findall(r"(?P<directive>\${.+?}\$)", text)

def directive_to_dict(text):
    json_text = text.strip()
    if json_text.startswith('${') and json_text.endswith('}$'):
        json_text = json_text.strip('$')
        json_dict = json_to_dict(json_text)
        return json_dict
    return None

def is_shortform_dict(directive_dict):
    '''Return True if the dict is a shortform object id dict'''
    return 'id' in directive_dict

def expand_shortform_dict(directive_dict):
    '''Expand a shortform dict into its explicit form'''
    if not is_shortform_dict(directive_dict):
        raise ValueError
    return {'#shortform': directive_dict}

def get_requirement_id(text, fuzzy=False):
    """Find requirement ID of the general form 'ABC-DEF-1' within a string like '[ABC-DEF-1, X]'

    If fuzzy is false, will only find IDs with a numerical suffix
    If fuzzy is true, will find any suffix (useful for finding pending
      annotations of the form ABC-DEF-?)

    Returns the requirement ID if found.
    Returns None otherwise.
    """
    if fuzzy:
        regex = r"^\s*\[\s*(?P<requirement_id>[\w\.]+-[\w\.]+-\S*)\s*,.+]\s*$"
    else:
        regex = r"^\s*\[\s*(?P<requirement_id>[\w\.]+-[\w\.]+-\d+)\s*,.+]\s*$"
    result = re.search(regex, text)
    if result:
        return result.group('requirement_id')
    return None

def legacy_object_id_to_directive_dict(text):
    '''Convert a legacy object ID do a Cascade directive dict

    Returns None if object ID format is not parseable
        '[SRD-RCN-0001, X]'                  -->  ['id':'SRD-RCN-0001', 'method':'x']
        '[SRD-RCN-3186, X, GUI]'             -->  ['id':'SRD-RCN-0001', 'method':'x', 'type':'GUI']
        '[SRD-RCN-4843, X, RSG-3895]'        -->  ['id':'SRD-RCN-0001', 'method':'x', 'old_id':'RSG-3895']
        '[SRD-RCN-4845, X, APP_B-8439, RSG]' -->  ['id':'SRD-RCN-0001', 'method':'x', 'old_id':'APP_B-8439', 'type':'RSG']

    '''
    requirement_types = ['RSG', 'SYS', 'GUI', 'BIT', 'RLI', 'RSG', 'SR']
    pieces = text.strip().strip('[').strip(']').split(',')
    pieces = [piece.strip() for piece in pieces]
    if len(pieces) not in (2, 3, 4):
        qlog.error('Ignoring legacy Object ID item: "{}".'.format(text) +
                   ' Expected to find 2, 3, or 4 items in brackets but found {}: {}'.format(
                       len(pieces), pieces) + '.' +
                   ' You must correct this field to contain the expected items.')
        return None
    else:
        if len(pieces) == 2:
            # Form:    '[SRD-RCN-0001, X]'
            directive_dict = OrderedDict([
                ('id', pieces[0]),
                ('method', pieces[1])])
        elif len(pieces) == 3:
            if pieces[2] in requirement_types:
                # Form:    '[SRD-RCN-3186, X, GUI]'
                directive_dict = OrderedDict([
                    ('id', pieces[0]),
                    ('method', pieces[1]),
                    ('type', pieces[2]),
                ])
            else:
                # Form: '[SRD-RCN-4843, X, RSG-3895]'
                directive_dict = OrderedDict([
                    ('id', pieces[0]),
                    ('method', pieces[1]),
                    ('old_id', pieces[2]),
                ])
        elif len(pieces) == 4:
            # Form: '[SRD-RCN-4845, X, APP_B-8439, RSG]'
            if pieces[3] not in requirement_types:
                qlog.warning('Unexpected requirement type in 4th field of legacy object id: "{}".  Expected one of: {}'.format(
                    text,
                    requirement_types))
            directive_dict = OrderedDict([
                ('id', pieces[0]),
                ('method', pieces[1]),
                ('old_id', pieces[2]),
                ('type', pieces[3]),
                ])
        else:
            qlog.error('Unexpected legacy object ID format.  Expected 2, 3, or 4 fields.  Object ID will be ignored: "{}"'.format(text))
            return None
        return directive_dict

def list_to_range_tuples(item_list):
    '''Given a sorted list of numbers, return a list of range tuples spanning all numbers in the list
    Group contiguous paragraph indices to create a list of tuples where each tuple
    specifies a range of paragraphs to purge
    Example: [100,99,98,70,49,48,47,29,28,2] --> [ (100,98), (70,70), (49,47), (29,28), (2,2) ]
    '''
    sorted_unique = sorted(list(set(item_list)), reverse=True)
    ranges = []
    range_in_progress = False
    first = None
    previous = None
    for i in sorted_unique:
        if not range_in_progress:
            first = i
            previous = i
            range_in_progress = True
            continue
        else:
            if i == previous - 1:
                previous = i
                continue
            else:
                # i is not in current range
                # Save previous range
                ranges.append((first, previous))
                # Begin a new range
                first = i
                previous = i
    # Save the final range
    ranges.append((first, previous))
    return ranges

class Indent:
    '''Print/Format indentation manager'''

    def __init__(self):
        self.level = 0

    def inc(self):
        '''Increment indentation inward'''
        self.level += 1

    def dec(self):
        '''Decrement indentation outward'''
        self.level = max(self.level-1, 0)

    def print(self, text):
        '''Print with current indentation'''
        print('{}{}'.format(self.__repr__(), text))

    def format(self, text):
        '''Format with current indentation'''
        return '{}{}'.format(self.__repr__(), text)

    def __repr__(self):
        '''Return current indentation pad string'''
        return '   ' * self.level

def get_heading_level(stylename):
    '''Determines whether a stylename is a heading style. Returns heading number if true, else None
    '''

    # Headings of the form 'Heading N'
    if stylename.startswith('Heading'):
        return int(stylename.split(' ')[-1])
    # Headings of the form 'Appendix_A_Level_N'
    if stylename.startswith('Appendix_') and 'Level_' in stylename:
        return int(stylename.split('_')[-1])
    return None

def to_snippet(text, length=40):
    '''Truncate text to requested length and append "..."
    '''
    if len(text) < length:
        return text
    return text[:min(len(text), length-3)] + '...'

Splitline = namedtuple('Splitline', 'text delimiter')

def mutlisplit(text, delimiter_list, preserve_delimiters=True):
    result_list = [Splitline(text, '')]
    for delimiter in delimiter_list:
        new_result_list = []
        for item in result_list:
            new_items = [Splitline(text, delimiter) for text in item.text.split(delimiter)]
            new_items[-1] = Splitline(new_items[-1].text, item.delimiter)
            new_result_list += new_items
        result_list = new_result_list

    if preserve_delimiters:
        return [item.text + item.delimiter for item in result_list]
    else:
        return [item.text for item in result_list]

def represents_int(s):
    """Return true if string represents an integer"""
    try: 
        int(s)
        return True
    except ValueError:
        return False

def get_directive_type(directive):
    """Given a dict containing a directive, return the directive type

    Directives have the form {'<directive type>' : <dict of stuff>}
    Example: {'#requirement': {...}} --> '#requirement'
    """
    keys = list(directive.keys())
    if len(keys) != 1:
        raise ValueError('Expected directive dict to contain a single key: {}'.format(directive))
    return keys[0]


"""
This is a python dictionary which declares the JSON schema for the "document_info"
directive appearing in Cascade word documents. "JSON schema" is a standardized
format for declaring constraints on the information present in a given JSON object.
This schema defines what constitutes a properly formed "document_info" directive.

   References:
        * http://json-schema.org/
          Definition of the "JSON schema" format

        * https://spacetelescope.github.io/understanding-json-schema/
          A very readable explanation of the "JSON schema" format

        * https://github.com/Julian/jsonschema
          The Python library used herein for "JSON schema" processing

"""
SCHEMA__DOCUMENT_INFO = {
    "title": "(HEAD)",
    "type": "object",
    "properties":{
        "#document_info":{
            "type": "object",
            "properties":{
                "object_ids":{
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties":{
                            "prefix": {
                                "type": "string",
                                "pattern": "^.+-$"
                            },
                            "next_id": {
                                "type": "integer"
                            }
                        },
                        "required": ["prefix", "next_id"],
                        "additionalProperties": False
                    }
                },
                "schemas":{
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties":{
                            "title":{
                                "type": "string",
                                "pattern": "^(#shortform|#section|#requirement)$"
                            }
                        },
                        "required": ["title"]
                    }
                },
            },
            "required": ["object_ids", "schemas"],
            "additionalProperties": False,
        },
    },
    "required": ["#document_info"],
    "additionalProperties": False
}

SCHEMA__PRAGMA = {
    "title": "#pragma",
    "type":  "string"
}

def validate_json(json_dict, schema):
    validation_passed = True
    try:
        jsonschema.validate(json_dict, schema)
    except jsonschema.exceptions.ValidationError as err:
        #TODO: Log validation error detail more cleanly
        qlog.error('JSON Validation Failed:\n' + str(err))
        validation_passed = False
    return validation_passed

def uprint(text):
    """Print Unicode do stdout, replacing errors for un-encodable characters"""
    print(text.encode(sys.stdout.encoding, errors='replace'))

def add_suffix_to_filename(filename, suffix_text):
    """Append a suffix to a filename

    The name is appended before the file extension (if one exists)
    
    Examples:
        add_suffix_to_filename('my_file.txt', '_old') -> 'myfile_old.txt'
        add_suffix_to_filename('my_file', '_old') -> 'myfile_old'

    Args:
        filename: Filename string
        suffix_text: Attend string

    Returns
        Modified filename
    """
    if not '.' in filename:
        return filename + suffix_text
    pieces = filename.split('.')
    return '.'.join(pieces[:-1]) + suffix_text + '.' + pieces[-1]

def make_output_file_info(out_filename, output_argument, append_suffix, replace_extension=None):
    ''' Determine the appropriate output filename and path for a Cascade command

    Arguments:
        out_filename:
            The nominal output filename. May also contain a full path.  This is very
            typically the input filename combined with an append_suffix option.
        output_argument:
            The output filename command line argument (in the case of the http interface,
            the command line argument is used to inject the target output directory).
            May be a path, a filename, or a path and a filename.  If a path and/or
            filename is specified, then they each individually OVERRIDE the path and filename
            specified by out_filename.
        append_suffix:
            Will be appended to out_filename (before its file extension) BEFORE output_argument
            is parsed (which could override the out_filename)
            e.g. out_filename='test.txt' append_suffix='_NEW' => 'test_NEW.txt'
        replace_extension:
            If supplied, replaces the extension of out_filename BEFORE output_argument
            is parsed (which could override the out_filename)
            e.g. out_filename='test.txt' replace_extension='rst' => 'test.rst'

    Returns:
        A dict containing 'path', 'filename', 'path_and_filename'
    '''
    out_path, out_filename = os.path.split(out_filename)
    if append_suffix:
        out_filename = add_suffix_to_filename(out_filename, append_suffix)

    if replace_extension:
         out_filename = '.'.join(out_filename.split('.')[:-1]) + '.' + replace_extension

    if output_argument:
        if os.path.isdir(output_argument):
            # Output specified a path only.
            out_path = output_argument
        else:
            # Output specified either a file or a path and file
            out_path, out_filename = os.path.split(output_argument)

    return dict(
        path=out_path,
        filename=out_filename,
        path_and_filename=os.path.join(out_path, out_filename)
        )
