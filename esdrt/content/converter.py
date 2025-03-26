from esdrt.content import MessageFactory as _
from z3c.form.converter import NumberDataConverter
from z3c.form.interfaces import IWidget


import zope


symbols = {
            'decimal': ',',
            'group': '',
            'list':  ';',
            'percentSign': '%',
            'nativeZeroDigit': '0',
            'patternDigit': '#',
            'plusSign': '+',
            'minusSign': '-',
            'exponential': 'E',
            'perMille': '\xe2\x88\x9e',
            'infinity': '\xef\xbf\xbd',
            'nan': ''
}


class ESDRTNumberDataConverter(NumberDataConverter):
    def __init__(self, field, widget):
        super(ESDRTNumberDataConverter, self).__init__(field, widget)
        self.formatter.symbols.update(symbols)

    # def format(self, obj, pattern=None):
    #     import pdb; pdb.set_trace()
    #     super(ESDRTIntegerDataConverter, self).format(obj, pattern)


class ESDRTIntegerDataConverter(ESDRTNumberDataConverter):
    """A data converter for integers."""
    zope.component.adapts(
        zope.schema.interfaces.IInt, IWidget)
    type = int
    errorMessage = _('The entered value is not a valid integer literal.')
