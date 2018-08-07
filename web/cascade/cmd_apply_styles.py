"""Handler for the 'apply-styles' command
(Commands are issued on the command line, per the docopt syntax in __main__.py)
"""

# Standard library
import os

# Local
from cascade import cmd_check
from cascade.word_docx import WordDocx
from cascade.util import get_directive_type
from cascade.util import add_suffix_to_filename, make_output_file_info
from cascade import quicklog
from cascade.util_eliot import log_function

qlog = quicklog.get_logger()
lprint = qlog.lprint

@log_function
def apply_styles(arguments):
    """ Apply Cascade styles to all directives

    Used to correct documents which were converted to Cascade format 
    before Cascade used styles for directives (it previously used 
    localized ad-hoc styling applied directly to the paragraphs)

    Returns:
        Tuple of output filenames if successful
        None otherwise
    """

    in_filename = arguments['<requirements.docx>']

    if not os.path.isfile(in_filename):
        qlog.error('The file "{}" does not exist'.format(in_filename))
        return

    # Integrity Check
    if not cmd_check.check(arguments):
        qlog.error('Aborted due to document check failures.')
        return

    # Load
    lprint('Loading document...')
    doc = WordDocx(qlog, os.path.abspath(in_filename))

    # Identify clusters
    lprint('Identifying paragraph clusters...')
    clusters = doc.get_clusters()

    # Parse
    lprint('Parsing clusters...')
    directives_found = 0
    directives_styled = 0
    for cluster in clusters:
        if cluster['cluster_type'] is 'directive':
            directives_found += 1
            directive_dict = cluster['directive']
            directive_type = get_directive_type(directive_dict)
            qlog.debug("Processing directive: {}".format(directive_dict))
            if directive_type == '#shortform':
                target_style = doc._document.styles['Cascade Directive']
            else:
                target_style = doc._document.styles['Cascade Hidden Directive']
            touched = False
            for paragraph in cluster['paragraphs']:
                if paragraph.style != target_style:
                    touched = True
                    paragraph.style = target_style
            if touched:
                directives_styled += 1

    lprint('{} directives were found.'.format(directives_found))
    lprint('{} directives were re-styled.'.format(directives_styled))

    #----------------------------
    # Save
    #----------------------------
    out_file_info = make_output_file_info(
        in_filename,
        arguments['<output.docx>'],
        '_STYLED'
        )

    lprint('Saving "{}"...'.format(out_file_info['path_and_filename']))
    doc.save(out_file_info['path_and_filename'])

    return (out_file_info['filename'],)
