from zope.component import adapter
from zope.interface import implementer

from esdrt.content.observation import IObservation
from plone.app.content.interfaces import INameFromTitle
from plone.app.content.namechooser import NormalizingNameChooser


ATTEMPTS = 100


class INameFromData(INameFromTitle):
    pass

@adapter(IObservation)
@implementer(INameFromData)
class ReferenceNumberCreator(NormalizingNameChooser):
    """A name chooser for a Zope object manager.

    If the object is adaptable to or provides INameFromTitle, use the
    title to generate a name.
    """

    def chooseName(self, name, object):
        parent = self.context
        items = []
        items.append(object.country.upper())
        items.append(object.crf_code)
        items.append(str(object.review_year))
        prename = '-'.join(items)
        number = 1
        observations = [k for k in list(parent.keys()) if k.startswith(prename)]
        if observations:
            observations.sort()
            last_observation = observations[-1]
            number = int(last_observation.split('-')[-1])
            number = number + 1
        last_part = '%04d' % number
        name = prename + '-' + last_part

        # OFS.ObjectManager.checkValidId fails unless the id is str
        return str(name)
