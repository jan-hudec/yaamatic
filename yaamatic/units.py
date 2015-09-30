import dexml.fields
import pint
import re

U = pint.UnitRegistry(
        on_redefinition='ignore' # I need to redefine hour to be abbreviated h
        )
Q = U.Quantity

# Fix hour: correct abbreviation for hour is h, so override the planck
# constant:
U.define('hour = 60 * minute = h = hr')

# Add method for easier substitution into templates using () (call operator)
def in_unit(self, unit):
    return str(self.to(unit).magnitude)
Q.__call__ = in_unit

# Prevent stringification of dimensional quantities (Quantity below uses
# format, that still works)
Q.__str__ = lambda self: in_unit(self, ())

_q_re = re.compile(r'([+-]?[0-9]*(?:\.[0-9]*)?)\s*(.*)')

class Quantity(dexml.fields.Value):
    class arguments(dexml.fields.Value.arguments):
        unit = None

    def __init__(self, **kw):
        super(Quantity, self).__init__(**kw)
        if isinstance(self.default, str):
            self.default = U(self.default)
        if self.default is not None and self.unit is None:
            self.unit = Q(1, self.default)
        if isinstance(self.unit, str):
            self.unit = U(self.unit)
        if not isinstance(self.unit, Q):
            raise TypeError(
                    'unit ({:P~}) must be quantity or string convertible to quantity',
                    self.unit)
        if self.default is not None and self.default.dimensionality != self.unit.dimensionality:
            raise TypeError(
                    'unit ({:P~}) and default ({}) are not the same dimension'.format(
                        self.unit, self.default))
        if self.unit is None:
            raise ValueError('Quantity field requires unit or default')

    def parse_value(self, val):
        m = _q_re.match(val)
        if m:
            q = Q(float(m.group(1)), m.group(2) or self.unit)
            if q.dimensionality == self.unit.dimensionality:
                return q
        raise ValueError("Value ‘{}’ can't be converted to {:P}".format(
            val, self.unit.dimensionality))

    def render_value(self, val):
        return '{:C~}'.format(val)
