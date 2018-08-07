"""Handler for the 'check' command
(Commands are issued on the command line, per the docopt syntax in __main__.py)
"""

# Standard library
import os
from collections import Counter

# Libraries
from colorama import Fore

# Local
from cascade.word_docx import WordDocx
from cascade.util import validate_json, represents_int, get_requirement_id, SCHEMA__DOCUMENT_INFO, SCHEMA__PRAGMA
from cascade.util_eliot import log_function
from cascade import quicklog

qlog = quicklog.get_logger()
lprint = qlog.lprint

@log_function
def check(arguments):
    """Check a requirements document for Cascade compliance & integrity

    Checks:
        Required styles exist: 'Cascade Directive', 'Cascade Hidden Directive'
        Object ID Prefixes match "prefix" directive.
        Object ID Suffix is number or "?"
        No duplicate object IDs.
        Report unassigned Object IDs.
        Verify "next_id" directive exceeds highest Object ID used.
        No old-form object IDs.

    Returns:
        True if check passed, false otherwise
    """
    success = True

    filename = arguments['<requirements.docx>']
    if not os.path.isfile(filename):
        qlog.error('The file "{}" does not exist'.format(filename))
        return False
    lprint('Checking "{}"...'.format(filename))
    doc = WordDocx(qlog, os.path.abspath(filename))

    if doc.doc_info_directive is None:
        qlog.error('Expected "document_info" directive not found in document "{}".'.format(filename))
        return False

    doc_info_dict = doc.doc_info_directive.as_dict
    qlog.debug('doc_info_directive.as_dict: {}'.format(doc_info_dict))

    if not check_styles(doc):
        success = False

    if not validate_json(doc_info_dict, SCHEMA__DOCUMENT_INFO):
        return False

    #Extract schemas from document_info directive
    schemas = {}
    for schema in doc_info_dict['#document_info']['schemas']:
        title = schema['title']
        schemas[title] = schema

    object_ids = {}
    for object_id in doc_info_dict['#document_info']['object_ids']:
        prefix = object_id['prefix']
        object_ids[prefix] = {
            'next_id': object_id['next_id'],
            'num_unassigned': 0,
            'max': -1
        }

    lprint('   Using directives:')
    lprint('      Object ID prefix:')
    for key in object_ids:
        lprint('         "{}" (Next ID:{})'.format(key, object_ids[key]['next_id']))
    lprint('      Schemas:')
    for key in schemas:
        lprint('         "{}"'.format(key))

    # Add the #pragma schema to the list of schemas (#pragma is always allowed to
    # appear in a doc, but its form is defined by Cascade, not in #document_info)
    schemas["#pragma"] = SCHEMA__PRAGMA

    all_object_ids = []

    #-----------------------
    # Check all directives against schemas
    #-----------------------
    for directive in doc._directives:
        directive_dict = directive.as_dict
        # If the directive does not contain a single key beginning with '#' then
        # it is a shortform directive.
        if not(len(directive_dict) == 1 and list(directive_dict.keys())[0][0] == "#"):
            directive_name = '#shortform'
        else:
            directive_name = list(directive_dict.keys())[0] # The one and only key is the directive name
            directive_dict = directive_dict[directive_name]

        if directive_name == '#document_info':
            # Do nothing. This directive has already been parsed.
            pass
        elif directive_name in schemas:
            if not validate_json(directive_dict, schemas[directive_name]):
                success = False
            elif directive_name == '#shortform':
                #TODO Use meta-schema to enforce that 'id' exists in shortform schema
                object_id = directive_dict['id']
                pieces = object_id.split('-')
                prefix = '-'.join(pieces[:-1]) + '-'
                suffix = pieces[-1]
                qlog.debug('Found object_id: "{}". Prefix:{} Suffix: {}'.format(object_id, prefix, suffix))
                if prefix not in object_ids:
                    qlog.error('Prefix in object ID {} does not match any declared object ID "prefix": {}'.format(object_id, list(object_ids.keys())))
                    success = False
                elif suffix == '?':
                    object_ids[prefix]['num_unassigned'] += 1
                elif not represents_int(suffix):
                    qlog.error('Suffix in object ID {} should be a number or a single "?".'.format(object_id))
                    success = False
                else:
                    object_id_number = int(suffix)
                    object_ids[prefix]['max'] = max(object_ids[prefix]['max'], object_id_number)
                    all_object_ids.append(object_id)
                    if object_id_number >= object_ids[prefix]['next_id']:
                        qlog.error('Suffix number in object ID {} violates "next_id" directive (should be < {})'.format(object_id, object_ids[prefix]['next_id']))
                        success = False
        else:
            qlog.error('Unexpected directive: "{}". '.format(directive_name) +
                       'A schema must be declared in the "document_info" directive for ' +
                       'each directive type appearing in the document.')
            success = False

        check_directive_style(directive_name, directive)

    # TODO: Add constraint to prefix format?  Maybe just warn if looks suspicious?

    #-----------------------
    # Check for old style object ids
    #-----------------------
    for paragragh in doc.paragraphs:
        text = doc.get_text(paragragh)
        if get_requirement_id(text, fuzzy=True):
            qlog.error('Unexpected old-style object ID: "{}". Use directive form.'.format(text))
            success = False

    # Check for duplicate object IDs
    counts = Counter(all_object_ids)
    for object_id in counts:
        if counts[object_id] > 1:
            qlog.error('Object ID {} appears {} times'.format(object_id, counts[object_id]))
            success = False

    lprint('   Object ID usage summary:')
    for key in object_ids:
        lprint('      "{}"'.format(key))
        object_id = object_ids[key]
        if object_id['max'] != -1:
            lprint('         Max appearing in document is {}{}'.format(key, object_id['max']))
            if object_id['num_unassigned']:
                lprint('         There {} {} unassigned object ID{} (of the form {}?)'.format(
                    pluralize('is', 'are', object_id['num_unassigned']),
                    object_id['num_unassigned'],
                    pluralize('', 's', object_id['num_unassigned']),
                    key
                    ))
        else:
            lprint('         (Does not appear in document)')

    if success:
        lprint(Fore.GREEN + "Check PASSED" + Fore.RESET)

    return success

def pluralize(singular, plural, value):
    return singular if value == 1 else plural

@log_function
def check_styles(doc):
    '''Confirm that the required styles are present in the WordDocx document.

    returns true if all required styles are present
    '''
    required_styles = ['Cascade Directive', 'Cascade Hidden Directive']
    success = True
    for style in required_styles:
        if style not in doc._document.styles:
            qlog.error('The required style "{}" was not found in the document.'.format(style))
            success = False
    return success

def check_directive_style(directive_name, directive):
    expected_style = 'Cascade Directive' if directive_name == '#shortform' else 'Cascade Hidden Directive'
    for paragragh in directive.paragraphs:
        if paragragh.style.name != expected_style:
            qlog.warning('In "{}" directive, expected style to be "{}".  Was "{}". Paragraph text: "{}"'.format(
                directive_name,
                expected_style,
                paragragh.style.name,
                paragragh.text
                ))

