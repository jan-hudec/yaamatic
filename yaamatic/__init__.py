"""Yaamatic JSBSim model generator."""

from os.path import basename, dirname, join
import argparse
import re
import sys

from .model import Airplane
from .templates import load_stream

_defRe = re.compile('([A-Za-z_][A-Za-z0-9_]*)(?:=(.*))?$')

def _Definition(string):
    m = _defRe.match(string)
    if m:
        if m.group(2):
            return (m.group(1), m.group(2))
        else:
            return (m.group(1), True)
    else:
        raise ValueError('Definition must be identifier optionally '
                +'followed by = and value')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('model', type=argparse.FileType(mode='rb'), # FIXME: binary or not for genshi?
            help="The input model template")
    p.add_argument('-o', '--output', type=argparse.FileType(mode='wb'), # FIXME: binary or not for genshi?
            help="The main output file. Default is derived from input model.")
    p.add_argument('-d', '--dir', type=str,
            help="The directory to write output to. Defaults to current "
                +"directory, or directory of OUTPUT if that is also given.")
    p.add_argument('--engines-dir', type=str,
            help="The directory where engines are written. Defaults to "
            +"Engines subdirectory of DIR")
    p.add_argument('-D', '--define', type=_Definition, action='append',
            default=[],
            help="Define value that will be made available in the model "
                +"template. Must be identifier, optionally followed by = "
                +"and value")
    p.add_argument('--dump-model', action='store_true',
            help='Print the preprocessed input model and stop.')
    a = p.parse_args()

    if a.dir is None:
        if a.output is not None:
            a.dir = dirname(a.output)
        else:
            a.dir = ''
    if a.engines_dir is None:
        a.engines_dir = join(a.dir, 'Engines')
    # Note: If a.output is not defined, we can't define it yet, because it
    # may be specified _inside_ the model!

    model_xml = load_stream(a.model, dict(a.define))
    if a.dump_model:
        print(model_xml)
        return 0

    aircraft = Airplane.parse(model_xml)

    print(aircraft.render(pretty=True))#DEBUG#

    for e in aircraft.engines_to_generte():
        e.generate(a.engines_dir)

    return 0
