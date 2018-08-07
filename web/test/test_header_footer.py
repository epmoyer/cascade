import os
from shutil import copyfile

import pytest

from cascade.word_header_footer import replace_in_header_footer

# Get the path to the test directory (this file's path)
test_root_path = os.path.dirname(os.path.realpath(__file__))

def test_header_footer():
    in_filename = os.path.join(test_root_path, 'assets', 'asset__header_footer.docx')
    out_filename = os.path.join(test_root_path, 'results', 'result__header_footer.docx')
    search_list = (
        dict(find='28-5018-10', replace='98-7654-32'),
        dict(find='Feature Description Document (FDD), RAVE', replace='New Document Title'),
    )

    copyfile(in_filename, out_filename)
    replace_in_header_footer(out_filename, search_list)

    #TODO: There is no automated checking of the resulting output.
    #      Need to add a way to search and validate the output
    #      document.