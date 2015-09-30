from genshi import template
import os
import os.path

from .units import U, Q

xml_loader = template.TemplateLoader([
    '.',
    template.loader.package('yaamatic', ''),
    ])

def load_stream(stream, definitions):
    return template.MarkupTemplate(stream, filename=stream.name,
            loader=xml_loader).generate(**definitions).render(method='xml')

def generate(t_name, output, *dicts):
    c = template.Context()
    c.update({
        'frange': frange,
        'table1': table1,
        'table2': table2,
        })
    for d in dicts:
        c.update(d)

    tmpl = xml_loader.load(t_name)
    out = tmpl.generate(c)

    if os.path.dirname(output):
        os.makedirs(os.path.dirname(output), exist_ok=True)
    
    out.render(method='xml', encoding='utf-8', out=open(output, 'wb'))

def frange(b, e, n):
    for i in range(n + 1):
        yield b * ((n - i)/n) + e * (i/n)

def table1(fn, rowdom):
    res = ''
    for r in rowdom:
        res += ' ' * 12 + ' {:11.5g} {:11.5g}'.format(r, fn(r)) + '\n'

def table2(fn, rowdom, coldom):
    coldom = list(coldom)
    res = ' ' * 24 + ''.join((' {:11.5g}'.format(c) for c in coldom)) + '\n'
    for r in rowdom:
        res += ' ' * 12 + ' {:11.5g}'.format(r) + ''.join(
                (' {:11.5g}'.format(fn(r, c)) for c in coldom)) + '\n'
    return res
