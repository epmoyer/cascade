''' Perform text search/replace in WordDocx objects
'''

from cascade import quicklog

qlog = quicklog.get_logger()
lprint = qlog.lprint

def word_search_replace(doc, search_list):
    ''' Perform search & replace on WordDocx object

    Arguments:
        doc: A WordDocx object
        search_list: List of dicts containing 'find' and 'replace' keys
    '''
    doc.resync_paragraphs()
    replacement_count = {item['find']:0 for item in search_list}
    for paragraph in doc.paragraphs:
        for search in search_list:
            if search['find'] in paragraph.text:
                replacer = ParapraphTextReplacer(paragraph)
                replacer.replace(search)
                replacement_count[search['find']] += 1
    for search in search_list:
        find_text = search['find']
        replace_text = search['replace']
        if replacement_count[find_text] == 0:
            qlog.error(f'Expected to find (and replace) text "{find_text}"' +
                       ' in master document but it was not found.')
        else:
            lprint(f'Replaced "{find_text}" with "{replace_text}" ' +
                   f'in {replacement_count[find_text]} location(s).')


class ParapraphTextReplacer():
    ''' Search/Replace text within a paragraph

    Limitations: Will replace only the first instance of the search text
    '''

    def __init__(self, paragraph):
        self.run_mappings = []
        index_first_character = 0
        self.paragraph_text = ''
        for run in paragraph.runs:
            self.run_mappings.append(
                dict(
                    run=run,
                    index_first_character=index_first_character,
                    index_last_character=index_first_character + len(run.text) -1
                )
            )
            index_first_character += len(run.text)
            self.paragraph_text += run.text

    def replace(self, search_dict):
        ''' Search/replace in the paragraph

        Arguments:
            search_dict: dict containing 'find' and 'replace' keys
        '''
        find_text = search_dict['find']
        replace_text = search_dict['replace']

        index_search_text_start = self.paragraph_text.find(find_text)
        if index_search_text_start == -1:
            raise RuntimeError('Expected to find search text in paragraph text.')
        index_search_text_end = index_search_text_start + len(find_text) - 1
        index_first_run = self.get_run_index(index_search_text_start)
        index_last_run = self.get_run_index(index_search_text_end)

        if index_first_run == index_last_run:
            # Search text is contained in a single run.
            run = self.run_mappings[index_first_run]['run']
            run.text = run.text.replace(find_text, replace_text)
            return

        # Search spans multiple runs

        # Put replacement text into end of fist run in which the find text occurs
        run = self.run_mappings[index_first_run]['run']
        run.text = run.text[:index_search_text_start] + replace_text

        # Remove any fragment of the search test from the last run
        run_mapping = self.run_mappings[index_last_run]
        run = run_mapping['run']
        remove_length = index_search_text_end - run_mapping['index_first_character'] + 1
        run.text = run.text[remove_length:]

        # Clear the text from any intervening runs
        for index in range(index_first_run + 1, index_last_run):
            self.run_mappings[index]['run'].text = ''

    def get_run_index(self, paragraph_char_index):
        ''' For character index within paragraph, return index of run_mapping containing that char
        '''
        for run_index, run_mapping in enumerate(self.run_mappings):
            if paragraph_char_index <= run_mapping['index_last_character']:
                return run_index
        raise RuntimeError('Expected to find index in runs_mappings.')
