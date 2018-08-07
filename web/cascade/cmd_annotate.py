"""Handler for the 'annotate' command
(Commands are issued on the command line, per the docopt syntax in __main__.py)
"""

# Standard library
import os
from collections import OrderedDict

# Libraries

# Local
from cascade import cmd_check
from cascade.word_docx import WordDocx
from cascade.util import (
    is_shortform_dict, add_suffix_to_filename, make_output_file_info)
from cascade import quicklog
from cascade.util_eliot import log_function

qlog = quicklog.get_logger()
lprint = qlog.lprint

@log_function
def annotate_reset(arguments):
    return annotate(arguments, reset=True, suffix='ANNOTATE_RESET')

@log_function
def annotate(arguments, reset=False, suffix='ANNOTATED'):
    """Annotates object IDs in a requirements document.
    Object IDs of the form '<prefix>-?' are assigned a number based on the next
        available object ID number, beginning with the value specified in the
        '#document_info' directive (and incrementing for each assignment)
        EXAMPLE:  'SRD-RCN-?' --> 'SRD-RCN-101'
                  'SRD-RCN-?' --> 'SRD-RCN-102'

    If the reset option is invoked, all object IDs are cleared to the form '<prefix>->'
        EXAMPLE:  'SRD-RCN-123' --> 'SRD-RCN-?'

    Returns:
        Tuple of output filenames if successful
        None otherwise
    """

    # Integrity check
    if not cmd_check.check(arguments):
        qlog.error('Annotation aborted due to document check failures.')
        return

    in_filename = arguments['<requirements.docx>']
    if not os.path.isfile(in_filename):
        qlog.error('The file "{}" does not exist'.format(in_filename))
        return

    lprint('Annotating "{}"...'.format(in_filename))
    doc = WordDocx(qlog, os.path.abspath(in_filename))

    object_ids = OrderedDict()
    for object_id in doc.doc_info_directive.as_dict['#document_info']['object_ids']:
        prefix = object_id['prefix']
        object_ids[prefix] = {
            'next_id': object_id['next_id']
        }
    next_id_updated = False

    #next_id = int(doc.doc_info_directive.as_dict['#document_info']['object_id']['next_id'])
    #original_next_id = next_id
    for directive in doc._directives:
        directive_dict = directive.as_dict
        if is_shortform_dict(directive_dict):
            qlog.debug('Processing {}'.format(directive_dict['id']))
            original_id = directive_dict['id']
            id_parts = directive_dict['id'].split('-')
            prefix = '-'.join(id_parts[:-1]) + '-'
            changed = False
            if reset:
                if id_parts[-1] == '?':
                    lprint('   {:15s}     (Is already reset)'.format(directive_dict['id']))
                else:
                    id_parts[-1] = '?'
                    changed = True
            else:
                if id_parts[-1] == '?':
                    id_parts[-1] = "{:04d}".format(object_ids[prefix]['next_id'])
                    object_ids[prefix]['next_id'] += 1
                    next_id_updated = True
                    changed = True
            if changed:
                directive_dict['id'] = '-'.join(id_parts)
                doc.rewrite_directive(directive)
                lprint('   {:15s} --> {}'.format(original_id, directive_dict['id']))

    if reset:
        for object_id_prefix in object_ids:
            object_ids[object_id_prefix]['next_id'] = 0
            next_id_updated = True
    if next_id_updated:
        # One or more 'next_id' has changed. Write new next_id back to doc
        object_id_list = []
        for object_id_prefix in object_ids:
            object_id_list.append(OrderedDict([
                ('prefix', object_id_prefix),
                ('next_id', object_ids[object_id_prefix]['next_id'])
            ]))
        doc.doc_info_directive.as_dict['#document_info']['object_ids'] = object_id_list
        doc.rewrite_directive(doc.doc_info_directive)

    #----------------------------
    # Save
    #----------------------------
    out_file_info = make_output_file_info(
        in_filename,
        arguments['<output.docx>'],
        '_' + suffix
        )

    lprint('Saving "{}"...'.format(out_file_info['path_and_filename']))
    doc.save(os.path.abspath(out_file_info['path_and_filename']))
    lprint("Done.")

    return (out_file_info['filename'],)
