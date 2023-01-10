# -*- coding: utf-8 -*-
from itertools import cycle
from functools import partial
from openpyxl import Workbook
from openpyxl.styles import Alignment
from operator import attrgetter
from Products.Five.browser import BrowserView
from StringIO import StringIO
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


XLS_SAMPLE_HEADER = (
    'Observation description', 'Country', 'CFR catedory code',
    'Inventory year', 'Gas', 'Review year', 'Fuel',
    'MS key category', 'EU key category',
    'Parameter', 'Description flags', 'Initial question text',
)

DESC = 'Description of the observation'
CFR_CODE = '1A1'
INVENTORY_YEAR = '2018'
REVIEW_YEAR = '2018'
REFERENCE_YEAR = '2018'
QUESTION_TEXT = (
    'The text of an initial Q&A question. '
    'Leave empty if you do not wish to add an initial question.'
)


# UnicodeEncodeError
def decode(s):
    return s.decode('UTF-8', 'replace') if isinstance(s, str) else s


def _get_vocabulary(context, name):
    factory = getUtility(IVocabularyFactory, name=name)
    return factory(context)


class GetSampleXLS(BrowserView):

    def populate_cells(self, sheet):
        get_vocabulary = partial(_get_vocabulary, self.context)
        get_title = attrgetter('title')

        header = XLS_SAMPLE_HEADER

        enable_key_category = self.context.enable_key_category

        if not enable_key_category:
            header = [v for v in header if "key category" not in v]

        fuel_voc = get_vocabulary('esdrt.content.fuel')
        # not a mandatory field, value can be none
        fuels = cycle(map(get_title, fuel_voc) + [None])

        country_voc = get_vocabulary('esdrt.content.eea_member_states')
        gas_voc = get_vocabulary('esdrt.content.gas')
        parameter_voc = get_vocabulary('esdrt.content.parameter')
        description_flags_voc = get_vocabulary('esdrt.content.highlight')

        countries = map(get_title, country_voc)

        ms_key_categ = cycle(['True', None])
        eu_key_categ = cycle(['True', None])
        gas = '\n'.join(map(get_title, gas_voc))
        parameter = '\n'.join(map(get_title, parameter_voc))
        description_flags = cycle(
            ['\n'.join(map(get_title, description_flags_voc)), None]
        )

        sheet.append(header)
        for idx, country in enumerate(countries):
            # get a value based on the country index position
            ms_key_cat = next(ms_key_categ)
            eu_key_cat = next(eu_key_categ)
            desc_fl = next(description_flags)
            fuel = next(fuels)
            row_0 = [
                DESC,
                country,
                CFR_CODE,
                INVENTORY_YEAR, gas,
                REVIEW_YEAR,
                fuel,
            ]
            row_key_categ = [ms_key_cat, eu_key_cat]
            row_1 = [
                parameter,
                desc_fl,
                QUESTION_TEXT,
            ]

            if enable_key_category:
                row = row_0 + row_key_categ + row_1
            else:
                row = row_0 + row_1

            sheet.append(row)

    def __call__(self):
        wb = Workbook()
        sheet = wb.create_sheet('Observation', 0)

        self.populate_cells(sheet)

        # wrap text for multi line cells and set max width
        for column in sheet.columns:
            length = []

            for cell in column:
                if cell.value:
                    multi_lines_length = [
                        len(c.rstrip())
                        for c in cell.value.splitlines()
                    ]
                    length.append(max(multi_lines_length))
                    cell.alignment = Alignment(wrap_text=True)

            sheet.column_dimensions[column[0].column].width = max(length)

        xls = StringIO()

        wb.save(xls)

        xls.seek(0)
        filename = 'observation_import_sample.xlsx'
        self.request.response.setHeader(
            'Content-type', 'application/vnd.ms-excel; charset=utf-8'
        )
        self.request.response.setHeader(
            'Content-Disposition', 'attachment; filename={0}'.format(filename)
        )
        return xls.read()
