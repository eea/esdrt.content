import re
from functools import partial
from itertools import islice
from itertools import chain
from operator import itemgetter

from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import Acquisition

from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage

from plone import api

import openpyxl

from esdrt.content.observation import create_comment
from esdrt.content.question import create_question


PORTAL_TYPE = 'Observation'

UNUSED_FIELDS = (
    'closing_comments', 'closing_deny_comments',
    'closing_comments_phase2', 'closing_deny_comments_phase2',
)

UNCOMPLETED_ERR = (
    u'The observation on row no. {} seems to be a bit off. '
    u'Please fill all the fields as shown in the import file sample. '
)

WRONG_DATA_ERR = (
    u'The information you entered in the {} section '
    u'of row no. {} is not correct. Please consult the columns'
    u' in the sample xls file to see the correct set of data.'
)

DONE_MSG = u'Successfully imported {} observations!'

# _key_cat**a**gory because the Observation field is mistyped!
INVENTORY_COLS = (
    'year', 'gas', 'review_year', 'fuel',
    'ms_key_catagory', 'eu_key_catagory',
    'parameter', 'highlight'
)


def _read_row(idx, row):
    val = itemgetter(idx)(row).value

    if not val:
        return ''

    if isinstance(val, (int, long)):
        val = safe_unicode(str(val))
    return val.strip()


def _multi_rows(row):
    splitted = re.split(r'[,\n]\s*', row)
    return tuple(val.strip() for val in splitted)


def _get_vocabulary(context, name):
    factory = getUtility(IVocabularyFactory, name=name)
    return factory(context)


def _cached_get_vocabulary(context, prefix=''):
    cache = {}

    def get_vocabulary(name):
        name = prefix + name if prefix else name
        if name not in cache:
            cache[name] = _get_vocabulary(context, name)
        return cache[name]

    return get_vocabulary


def get_constants(context):
    XLS_COLS = {}
    XLS_COLS['text'] = partial(_read_row, 0)
    XLS_COLS['country'] = partial(_read_row, 1)
    XLS_COLS['crf_code'] = partial(_read_row, 2)
    next_col = 3


    filtered_inventory_cols = INVENTORY_COLS
    if not context.enable_key_category:
        filtered_inventory_cols = [
            v for v in INVENTORY_COLS
            if "key_catagory" not in v
        ]

    # setup readers
    for idx, col in enumerate(filtered_inventory_cols, start=next_col):
        XLS_COLS[col] = partial(_read_row, idx)

    # last column always the initial Q&A question
    XLS_COLS['question'] = partial(_read_row, idx + 1)

    return XLS_COLS


def find_dict_key(vocabulary, value):
    for key, val in vocabulary.items():
        if isinstance(val, list):
            if value in val:
                return key
        elif isinstance(val, Acquisition.ImplicitAcquisitionWrapper):
            if val.title == value:
                return key
        elif val == value:
            return key

    return False


def key_in_vocab(vocab, key):
    for term in vocab:
        if key == term.title:
            return term.token
    return False


def error_status_messages(context, request, messages):
    status = IStatusMessage(request)
    for message in messages:
        status.addStatusMessage(message, 'error')
    url = context.absolute_url() + '/observation_import_form'
    return request.response.redirect(url)


class Entry(object):

    def __init__(self, row, constants, get_vocabulary):
        self.row = row
        self.constants = constants
        self.get_vocabulary = get_vocabulary

    @property
    def title(self):
        return True

    @property
    def text(self):
        return self.constants['text'](self.row)

    @property
    def country(self):
        country_voc = self.get_vocabulary('eea_member_states')
        cell_value = self.constants['country'](self.row)
        return key_in_vocab(country_voc, cell_value)

    @property
    def crf_code(self):
        crf = self.constants['crf_code'](self.row)
        return crf if crf != '' else None

    @property
    def year(self):
        cell_value = self.constants['year'](self.row)
        return cell_value if cell_value else False

    @property
    def reference_year(self):
        return int(self.constants['reference_year'](self.row))

    @property
    def gas(self):
        gas_voc = self.get_vocabulary('gas')
        cell_value = _multi_rows(self.constants['gas'](self.row))
        keys = [key_in_vocab(gas_voc, key) for key in cell_value]
        if False in keys:
            return False
        return keys

    @property
    def scenario(self):
        scenario_voc = self.get_vocabulary('scenario_type')
        cell_value = _multi_rows(self.constants['scenario'](self.row))
        if cell_value == ('',):
            return None
        keys = [key_in_vocab(scenario_voc, key) for key in cell_value]
        if False in keys:
            return False
        return keys

    @property
    def review_year(self):
        return int(self.constants['review_year'](self.row))

    @property
    def fuel(self):
        fuel_voc = self.get_vocabulary('fuel')
        cell_value = self.constants['fuel'](self.row)
        if cell_value != '':
            return key_in_vocab(fuel_voc, cell_value)
        # This field can be none because it's not manadatory
        return None

    def _key_category(self, name):
        cell_value = self.constants[name](self.row).title()

        if cell_value == 'True':
            return cell_value
        elif cell_value == '':
            # openpyxl takes False cell values as empty strings so it is easier
            # to assume that an empty cell of the MS/EU Key Category column
            # evaluates to false
            return 'False'

        # For the incorrect data check
        return False

    @property
    def ms_key_catagory(self):
        return self._key_category('ms_key_catagory')

    @property
    def eu_key_catagory(self):
        return self._key_category('eu_key_catagory')

    @property
    def parameter(self):
        parameter_voc = self.get_vocabulary('parameter')
        cell_value = _multi_rows(self.constants['parameter'](self.row))
        keys = [key_in_vocab(parameter_voc, key) for key in cell_value]
        if False in keys:
            return False
        return keys

    @property
    def highlight(self):
        highlight_voc = self.get_vocabulary('highlight')
        col_desc_flags = self.constants['highlight'](self.row)
        if col_desc_flags != '':
            cell_value = _multi_rows(col_desc_flags)
            keys = [key_in_vocab(highlight_voc, key) for key in cell_value]
            if False in keys:
                return False
            else:
                return keys
        else:
            # This field can be none because it's not manadatory
            return None

    @property
    def question(self):
        val = self.constants['question'](self.row)
        if val is not None:
            return val.strip()

    def get_fields(self):
        fields = self.constants.keys()
        return {
            name: getattr(self, name)
            for name in fields
            if name not in UNUSED_FIELDS
            and name != 'question'
        }


def _create_observation(entry, context, request, portal_type, obj):
    obj.row_nr += 1

    fields = entry.get_fields()

    errors = []

    if '' in fields.values():
        errors.append(UNCOMPLETED_ERR.format(obj.row_nr - 1))
        # return error_status_message(
        #     context, request, UNCOMPLETED_ERR.format(obj.row_nr - 1)
        # )

    elif False in fields.values():
        key = find_dict_key(fields, False)
        key = 'description flags' if key == 'highlight' else key
        errors.append(WRONG_DATA_ERR.format(key, obj.row_nr - 1))

    if errors:
        return None, errors

    if context.enable_key_category:
        for kc in ['ms_key_catagory', 'eu_key_catagory']:
            # Values must be boolean
            if fields[kc] == 'True':
                fields[kc] = True
            else:
                fields[kc] = False

    content = api.content.create(
        context,
        type=portal_type,
        title=getattr(entry, 'title'),
        **fields
    )

    question_text = entry.question
    if question_text:
        question = create_question(content)
        question.id = 'question-1'
        content[question.id] = question
        create_comment(question_text, content[question.id])

    obj.num_entries += 1

    return content, errors


class ObservationXLSImport(BrowserView):

    num_entries = 0
    row_nr = 2

    def valid_rows_index(self, sheet):
        """There are some cases when deleted rows from an xls file are seen
        as empty rows and the importer tries to create an object with no data
        """
        idx = 1
        for row in sheet:
            if any(cell.value for cell in row):
                idx += 1
        return idx

    def do_import(self):
        xls_file = self.request.get('xls_file', None)

        wb = openpyxl.load_workbook(xls_file, read_only=True, data_only=True)
        sheet = wb.worksheets[0]

        max = self.valid_rows_index(sheet)

        # skip the document header
        valid_rows = islice(sheet, 1, max - 1)

        constants = get_constants(self.context)
        get_vocabulary = _cached_get_vocabulary(
            self.context, prefix='esdrt.content.')

        entries = []
        for row in valid_rows:
            entries.append(
                Entry(
                    row, constants,
                    get_vocabulary
                )
            )

        for entry in entries:
            _, errors = _create_observation(
                entry, self.context, self.request, PORTAL_TYPE, self
            )
            if errors:
                return error_status_messages(
                    self.context, self.request, errors)

        if self.num_entries > 0:
            status = IStatusMessage(self.request)
            status.addStatusMessage(DONE_MSG.format(self.num_entries))

        return self.request.response.redirect(self.context.absolute_url())
