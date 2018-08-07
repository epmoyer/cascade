'''
Search and replace for Microsoft Word headers and footers.

At the current writing, the python-docx module does not provide access to
headers and footers.  This module therefore directly accesses Word
documents to make the changes.

.docx files are really .zip archives containing many files which compose a 
Word document.  The header and footer data are XML files stored within
the archive at word/footer<number>.xml and word/header<number>.xml

'''

from zipfile import ZipFile
import tempfile
import os
import re
from enum import Enum

from cascade import quicklog
from cascade.util_eliot import log_function

qlog = quicklog.get_logger()

@log_function
def replace_in_header_footer(filename, search_list):
    ''' Replace text in headers & footers of ah MS Word .docx file

    Arguments:
        filename: The filename of an MS Word .docx file
        search_list: List of dicts containing 'find' and 'replace' keys
    '''
    if not filename.endswith('.docx'):
        raise ValueError('Expected an MS Word .docx file.')

    # generate a temp file
    temp_fd, temp_filename = tempfile.mkstemp(dir=os.path.dirname(filename))
    os.close(temp_fd)

    with ZipFile(filename) as input_doc:
        header_footer_filenames = get_header_and_footer_filenames(input_doc)
        remove_from_zip(filename, temp_filename, header_footer_filenames)

        with ZipFile(temp_filename, 'a') as output_doc:
            for item_filename in header_footer_filenames:
                qlog.debug(f'Replacing headers/footers in:{item_filename}')
                xmlcontent = input_doc.read(item_filename)
                xml_string = str(xmlcontent, 'utf-8')
                modified_xml = word_xml_search_and_replace(xml_string, search_list)
                xml_out_bytes = bytes(modified_xml, 'utf-8')
                output_doc.writestr(item_filename, xml_out_bytes)

     # replace with the temp archive
    os.remove(filename)
    os.rename(temp_filename, filename)

@log_function
def remove_from_zip(zip_in_filename, zip_out_filename, filenames):
    ''' Copy zip archive, removing the specified filenames
    '''
    with ZipFile(zip_in_filename, 'r') as zipread:
        with ZipFile(zip_out_filename, 'w') as zipwrite:
            for item in zipread.infolist():
                if item.filename not in filenames:
                    data = zipread.read(item.filename)
                    zipwrite.writestr(item, data)


def get_header_and_footer_filenames(zip_file):
    '''
    Retrieve the header and footer filenames from a MS Word .docx file

    Arguments:
        zip_file: A ZipFile() object which is a MS Word .docx file
    Returns:
        a list of all header and footer filenames in the zipfile
    '''
    results = []
    for filename in zip_file.namelist():
        # TODO: Forward slash in path is probably incorrect on 
        #       Windows machines. Make Win compatible?
        if (re.match(r'word/footer\d+.xml', filename) or
            re.match(r'word/header\d+.xml', filename)):
            results.append(filename)
    return sorted(results)

class SearchState(Enum):
    FIND_OPENING_TEXT_TAG = 0
    FIND_OPENING_TEXT_TAG_END = 1
    CAPTURE_TEXT = 2

def word_xml_search_and_replace(xml, search_list):
    ''' Perform the requested search/replace operation on .docx xml

    Arguments:
        xml: A string containing MS Word .docx xml
        search_list: List of dicts containing 'find' and 'replace' keys

    Returns: 
        Resulting xml, with search/replace executed
    ''' 
    xml_replacer = XmlReplacer(xml, search_list)
    # in_text_tag = False
    xml_length = len(xml)
    skip = 0
    state = SearchState.FIND_OPENING_TEXT_TAG
    for index, char in enumerate(xml):
        if skip:
            skip -= 1
            continue

        if state == SearchState.FIND_OPENING_TEXT_TAG:
            if char == '<' and index + 3 < xml_length and xml[index:index + 4] == '<w:t':
                state = SearchState.FIND_OPENING_TEXT_TAG_END
                skip = 3
        elif state == SearchState.FIND_OPENING_TEXT_TAG_END:
            if char == '>':
                state = SearchState.CAPTURE_TEXT
        elif state == SearchState.CAPTURE_TEXT:
            if char == '<' and index + 5 < xml_length and xml[index:index + 6] == '</w:t>':
                state = SearchState.FIND_OPENING_TEXT_TAG
                skip = 5
            else:
                xml_replacer.add_clear_text_char(char, index)
        else:
            raise ValueError('Unexpected State')

    new_xml = xml_replacer.do_replace()

    return new_xml


class XmlReplacer():

    def __init__(self, xml, search_list):
        ''' Perform search and replace on MS Word xml

        Arguments:
            xml: original xml document, as string
            search_list: List of dicts containing 'find' and 'replace' keys
        '''

        self.search_list = search_list
        self.clear_text = ''
        self.clear_text_offsets = []
        self.xml = xml

    def add_clear_text_char(self, char, offset):
        self.clear_text += char
        self.clear_text_offsets.append(offset)

    def do_replace(self):
        qlog.debug(f'XmlReplacer: clear_text="{self.clear_text}"')
        operations = []
        for search in self.search_list:
            locations = [m.start() for m in re.finditer(re.escape(search['find']), self.clear_text)]
            for location in locations:
                operations.append(dict(
                    start = self.clear_text_offsets[location],
                    end = self.clear_text_offsets[location + len(search['find']) - 1],
                    replace = search['replace']
                    ))
        operations.sort(key=lambda x: x['start'], reverse=True)

        # Do replacements
        result_xml = self.xml
        qlog.debug(f'Replacement operations:{operations}')
        for operation in operations:
            result_xml = (
                result_xml[0:operation['start']] +
                operation['replace'] +
                (result_xml[operation['end']+1:] if operation['end'] + 1 < len(result_xml) else ''))

        return result_xml

