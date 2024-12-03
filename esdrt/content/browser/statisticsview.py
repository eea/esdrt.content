from Products.CMFCore.utils import getToolByName
from esdrt.content.reviewfolder import IReviewFolder
from five import grok
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import itertools
import copy
import operator

import tablib
from datetime import datetime

grok.templatedir('templates')


class StatisticsView(grok.View):
    grok.context(IReviewFolder)
    grok.name('statistics')
    grok.require('cmf.ManagePortal')

    def update(self):

        self.observations = self.get_all_observations()
        self.questions = self.get_all_questions()

    def get_all_observations(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='Observation',
            path='/'.join(self.context.getPhysicalPath())
        )
        data = []
        for brain in brains:
            item = dict(
                country=brain.country,
                status=brain.observation_status,
                sector=brain.get_ghg_source_sectors,
                highlight=brain.get_highlight or [],
                finalisation_reason=brain.observation_finalisation_reason,
                step=brain.observation_step,
            )
            data.append(item)
        return data

    def get_all_questions(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='Question',
            path='/'.join(self.context.getPhysicalPath())
        )
        data = []
        for brain in brains:
            item = dict(
                country=brain.country,
                status=brain.observation_status,
                sector=brain.get_ghg_source_sectors,
            )
            data.append(item)
        return data

    def get_vocabulary_values(self, name):
        try:
            factory = getUtility(IVocabularyFactory, name)
            vocabulary = factory(self.context)
            return sorted([k for k, v in vocabulary.by_token.items()])
        except:
            return []

    def get_step(self):
        step = self.request.form.get('step', '')
        if step == '':
            step = 'step1'
        return step

    def _generic_getter(self, objs, key, value, columns=[], filter_fun=None):

        """
         Generic function to get items for later rendering.
         Parameters:
          - Key: name of the field that will be shown in files
          - Value: name of the field that will be counted
          - Columns: values of the 'value' field that will be counted and shown
          - obs_filter: a function returning if a given observation should be
                        included on the count or not.

        """
        data = []
        items = {}
        step = self.get_step()
        if step == 'step1':
            objs = [item for item in objs if item['step'] == 'step1']
        elif step == 'step2':
            objs = [item for item in objs if item['step'] == 'step2']
        # Get the items, filtered if needed
        filted_items = filter(filter_fun, objs)
        #filted_items = filter(lambda x: x.step == step, filted_items)
        # Set sorting and grouping key into a function
        getkey = operator.itemgetter(key)
        filted_items.sort(key=getkey)
        # get observations grouped by the value of the key
        for gkey, item in itertools.groupby(filted_items, key=getkey):
            val = items.get(gkey, [])
            val.extend([o.get(value) for o in item])
            items[gkey] = val

        # Count how many observations are per-each of the columns
        for gkey, values in items.items():
            item = {}
            for column in columns:
                item[column] = values.count(column)

            # Calculate the sum
            val = sum(item.values())
            item['sum'] = val
            item[key] = gkey
            data.append(item)

        # Calculate the final sum
        datasum = self.calculate_sum(data, key)
        if datasum is not None:
            data.append(datasum)

        return data

    def calculate_sum(self, items, key):
        if items:
            ret = copy.copy(reduce(lambda x, y: dict((k, v + (y and y.get(k, 0) or 0)) for k, v in x.iteritems()), copy.copy(items)))
            ret[key] = 'Sum'
            return ret
        return None

    def _generic_observation(self, key, value, columns=[], filter_fun=None):
        return self._generic_getter(
            self.observations,
            key,
            value,
            columns,
            filter_fun,
        )

    def _generic_question(self, key, value, columns=[], filter_fun=None):
        return self._generic_getter(
            self.questions,
            key,
            value,
            columns,
            filter_fun,
        )

    def get_sectors(self):
        return self.get_vocabulary_values('esdrt.content.ghg_source_sectors')

    def get_countries(self):
        return self.get_vocabulary_values('esdrt.content.eea_member_states')

    def observation_status_per_country(self):
        return self._generic_observation(
            key='country',
            value='status',
            columns=['SRRE', 'LRQE', 'MSC', 'answered', 'conclusions', 'close-requested', 'finalised']
        )

    def observation_status_per_sector(self):
        return self._generic_observation(
            key='sector',
            value='status',
            columns=['SRRE', 'LRQE', 'MSC', 'answered', 'conclusions', 'close-requested', 'finalised']
        )

    def finalised_reason_per_country(self):
        return self._generic_observation(
            key='country',
            value='finalisation_reason',
            columns=['no-conclusion-yet', 'no-response-needed', 'partly-resolved', 'resolved', 'unresolved', 'significant-issue']
        )

    def finalised_reason_per_sector(self):
        return self._generic_observation(
            key='sector',
            value='finalisation_reason',
            columns=['no-conclusion-yet', 'no-response-needed', 'partly-resolved', 'resolved', 'unresolved', 'significant-issue']
        )

    def question_status_per_country(self):
        return self._generic_question(
            key='country',
            value='status',
            columns='esdrt.content.eea_member_states'
        )

    def question_status_per_sector(self):
        return self._generic_question(
            key='sector',
            value='status',
            columns='esdrt.content.ghg_source_sectors'
        )

    def observation_highlights_pgf(self):
        return self._generic_observation(
            key='sector',
            value='country',
            columns=self.get_countries(),
            filter_fun=lambda x: 'pgf' in x.get('highlight'),
        )

    def observation_highlights_psi(self):
        return self._generic_observation(
            key='sector',
            value='country',
            columns=self.get_countries(),
            filter_fun=lambda x: 'psi' in x.get('highlight', []),
        )

    def observation_highlights_ptc(self):
        return self._generic_observation(
            key='sector',
            value='country',
            columns=self.get_countries(),
            filter_fun=lambda x: 'ptc' in x.get('highlight', []),
        )
class DownloadStatisticsView(grok.View):
    grok.context(IReviewFolder)
    grok.name('download-statistics')
    grok.require('cmf.ManagePortal')

    def get_all_observations(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='Observation',
            path='/'.join(self.context.getPhysicalPath())
        )
        data = []
        for brain in brains:
            item = dict(
                country=brain.country,
                status=brain.observation_status,
                sector=brain.get_ghg_source_sectors,
                highlight=brain.get_highlight or [],
                finalisation_reason=brain.observation_finalisation_reason,
                step=brain.observation_step,
            )
            data.append(item)
        return data

    def get_vocabulary_values(self, name):
        try:
            factory = getUtility(IVocabularyFactory, name)
            vocabulary = factory(self.context)
            return sorted([k for k, v in vocabulary.by_token.items()])
        except:
            return []

    def get_step(self):
        step = self.request.form.get('step', '')
        if step == '':
            step = 'step1'
        return step

    def _generic_getter(self, objs, key, value, columns=[], filter_fun=None):

        """
         Generic function to get items for later rendering.
         Parameters:
          - Key: name of the field that will be shown in files
          - Value: name of the field that will be counted
          - Columns: values of the 'value' field that will be counted and shown
          - obs_filter: a function returning if a given observation should be
                        included on the count or not.

        """
        data = []
        items = {}
        step = self.get_step()
        if step == 'step1':
            objs = [item for item in objs if item['step'] == 'step1']
        elif step == 'step2':
            objs = [item for item in objs if item['step'] == 'step2']
        # Get the items, filtered if needed
        filted_items = filter(filter_fun, objs)
        #filted_items = filter(lambda x: x.step == step, filted_items)
        # Set sorting and grouping key into a function
        getkey = operator.itemgetter(key)
        filted_items.sort(key=getkey)
        # get observations grouped by the value of the key
        for gkey, item in itertools.groupby(filted_items, key=getkey):
            val = items.get(gkey, [])
            val.extend([o.get(value) for o in item])
            items[gkey] = val

        # Count how many observations are per-each of the columns
        for gkey, values in items.items():
            item = {}
            for column in columns:
                item[column] = values.count(column)

            # Calculate the sum
            val = sum(item.values())
            item['sum'] = val
            item[key] = gkey
            data.append(item)

        # Calculate the final sum
        datasum = self.calculate_sum(data, key)
        if datasum is not None:
            data.append(datasum)

        return data

    def calculate_sum(self, items, key):
        if items:
            ret = copy.copy(reduce(lambda x, y: dict((k, v + (y and y.get(k, 0) or 0)) for k, v in x.iteritems()), copy.copy(items)))
            ret[key] = 'Sum'
            return ret
        return None

    def _generic_observation(self, key, value, columns=[], filter_fun=None):
        return self._generic_getter(
            self.observations,
            key,
            value,
            columns,
            filter_fun,
        )

    def get_sectors(self):
        return self.get_vocabulary_values('esdrt.content.ghg_source_sectors')

    def get_countries(self):
        return self.get_vocabulary_values('esdrt.content.eea_member_states')

    def render(self):
        self.observations = self.get_all_observations()

        now = datetime.now()
        filename = 'EMRT-' + now.strftime("%Y%M%d%H%m") + " - " + self.get_step() + ".xls"

        book = tablib.Databook((self.observation_status_per_country(),
                self.observation_status_per_sector(),
                self.finalised_reason_per_sector(),
                self.finalised_reason_per_country(),
                self.observation_highlights_pgf(),
                self.observation_highlights_psi(),
                self.observation_highlights_ptc()))

        response = self.request.response
        response.setHeader("content-type", "application/vnc.ms-excel")
        response.setHeader("Content-disposition", "attachment;filename=" + filename)

        return book.xls

    def observation_status_per_country(self):
        data = tablib.Dataset()
        data.title = "Observation status per country"

        observations = self._generic_observation(
            key='country',
            value='status',
            columns=['SRRE', 'LRQE', 'MSC', 'answered', 'conclusions', 'finalised']
        )
        for observation in observations:
            data.append([observation['country'],
                observation['SRRE'],
                observation['LRQE'],
                observation['MSC'],
                observation['answered'],
                observation['conclusions'],
                observation['finalised'],
                observation['sum']])
        data.headers = ['Country', 'SR/RE', 'LR/QE', 'MSC', 'Answer received', 'Conclusions', 'Finalised', 'Sum']

        return data

    def observation_status_per_sector(self):
        data = tablib.Dataset()
        data.title = "Observation status per sector"

        observations = self._generic_observation(
            key='sector',
            value='status',
            columns=['SRRE', 'LRQE', 'MSC', 'answered', 'conclusions', 'finalised']
        )
        for observation in observations:
            data.append([observation['sector'],
                observation['SRRE'],
                observation['LRQE'],
                observation['MSC'],
                observation['answered'],
                observation['conclusions'],
                observation['finalised'],
                observation['sum']])
        data.headers = ['Sector', 'SR/RE', 'LR/QE', 'MSC', 'Answer received', 'Conclusions', 'Finalised', 'Sum']

        return data

    def finalised_reason_per_country(self):
        data = tablib.Dataset()
        data.title = "Finalised reason per country"

        observations = self._generic_observation(
            key='country',
            value='finalisation_reason',
            columns=['no-conclusion-yet', 'no-response-needed', 'partly-resolved', 'resolved', 'unresolved', 'significant-issue']
        )
        for observation in observations:
            data.append([observation['country'],
                observation['no-conclusion-yet'],
                observation['no-response-needed'],
                observation['partly-resolved'],
                observation['resolved'],
                observation['unresolved'],
                observation['significant-issue'],
                observation['sum']])
        data.headers = ['Country', 'No conclusion yet', 'No response needed', 'Party resolved', 'Resolved', 'Unresolved', 'Significant issue', 'Sum']

        return data

    def finalised_reason_per_sector(self):
        data = tablib.Dataset()
        data.title = "Finalised reason per sector"

        observations = self._generic_observation(
            key='sector',
            value='finalisation_reason',
            columns=['no-conclusion-yet', 'no-response-needed', 'partly-resolved', 'resolved', 'unresolved', 'significant-issue']
        )
        for observation in observations:
            data.append([observation['sector'],
                observation['no-conclusion-yet'],
                observation['no-response-needed'],
                observation['partly-resolved'],
                observation['resolved'],
                observation['unresolved'],
                observation['significant-issue'],
                observation['sum']])
        data.headers = ['Sector', 'No conclusion yet', 'No response needed', 'Party resolved', 'Resolved', 'Unresolved', 'Significant issue', 'Sum']

        return data


    def observation_highlights_pgf(self):
        data = tablib.Dataset()
        data.title = "PGF observations"

        observations = self._generic_observation(
            key='sector',
            value='country',
            columns=self.get_countries(),
            filter_fun=lambda x: 'pgf' in x.get('highlight'),
        )
        for observation in observations:
            row = [observation['sector']]
            for country in self.get_countries():
                row += [observation[country]]
            row += [observation['sum']]
            data.append(row)
        data.headers = ['Sector'] + self.get_countries() + ['Sum']

        return data


    def observation_highlights_psi(self):
        data = tablib.Dataset()
        data.title = "PSI observations"

        observations = self._generic_observation(
            key='sector',
            value='country',
            columns=self.get_countries(),
            filter_fun=lambda x: 'psi' in x.get('highlight'),
        )
        for observation in observations:
            row = [observation['sector']]
            for country in self.get_countries():
                row += [observation[country]]
            row += [observation['sum']]
            data.append(row)
        data.headers = ['Sector'] + self.get_countries() + ['Sum']

        return data

    def observation_highlights_ptc(self):
        data = tablib.Dataset()
        data.title = "PTC observations"

        observations = self._generic_observation(
            key='sector',
            value='country',
            columns=self.get_countries(),
            filter_fun=lambda x: 'ptc' in x.get('highlight'),
        )
        for observation in observations:
            row = [observation['sector']]
            for country in self.get_countries():
                row += [observation[country]]
            row += [observation['sum']]
            data.append(row)
        data.headers = ['Sector'] + self.get_countries() + ['Sum']

        return data
