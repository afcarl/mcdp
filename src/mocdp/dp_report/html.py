from mocdp.lang.namedtuple_tricks import isnamedtuplewhere, get_copy_with_where
from contracts import contract
from mocdp.lang.syntax import Syntax
from mocdp.lang.parse_actions import parse_wrap
from contracts.interface import Where
from contracts.utils import indent, raise_wrapped
from mocdp.comp.tests.test_drawing import unzip


def isolate_comments(s):
    lines = s.split("\n")
    def isolate_comment(line):
        if '#' in line:
            where = line.index('#')
            good = line[:where]
            comment = line[where:]
            return good, comment
        else:
            return line, None

    return unzip(map(isolate_comment, lines))

@contract(s=str)
def ast_to_html(s, complete_document):
#     s = s.lstrip()
    s_lines, s_comments = isolate_comments(s)
    assert len(s_lines) == len(s_comments) 
#     s_only = "\n".join(s_lines)
    # Problem: initial comment, '# test connected\nmcdp'

    empty_lines = []
    for line in s_lines:
        if line.strip() == '':
            empty_lines.append(line)
        else:
            break
    full_lines = s_lines[len(empty_lines):]
    for_pyparsing = "\n".join(full_lines)
#     print('Stripped s: %r' % s[:100])
#     print('First s_lines:', s_lines[:5])
#     print('First chars in s_only: %r' % s_only[:100])

    block = parse_wrap(Syntax.dp_rvalue, for_pyparsing)[0]

    if not isnamedtuplewhere(block):
        raise ValueError(block)

#     print print_ast(block)

    block2 = make_tree(block, character_end=len(s))
#     print print_ast(block2)


    _, _, _, transformed_p = print_html_inner(block2)

    # add back the white space
    if empty_lines:
        transformed = "\n".join(empty_lines) + '\n' + transformed_p
    else:
        transformed = transformed_p
    
    lines = transformed.split('\n')
    if len(lines) != len(s_comments):
#         for i in range(min(len(lines), len(s_comments))):
#
#             print('orig %d: %s' % (i, s_lines[i]))
#             print('trans %d: %s' % (i, lines[i]))
        e = ValueError('Error in syntax: %s, %s' % (len(lines), len(s_comments)))
        print(e)
    
    out = ""
    for i, (a, comment) in enumerate(zip(lines, s_comments)):
        out += a
        if comment:
            out += '<span class="comment">%s</span>' % comment

        if i != len(lines) - 1:
            out += '\n'

    if complete_document:
        s = """<html><head>
        <link rel="stylesheet" type="text/css" href="syntax.css"> 
        </head><body>"""
        s += '\n<pre><code>'
        s += out
        s += '\n<pre><code>'
    #     s += """
    #     <style type="text/css">
    #     span.element { margin: 2px; padding: 1px; border: solid 1px black;}
    #     span.unit { color: #f80; }
    #     span.Unit { color: red; }
    #     span.ProvideKeyword, span.RequireKeyword,span.MCDP  { font-weight: bold; color: #00a;}
    #     </style>
    #     """
        s += '\n</body></html>'
        return s
    else:
        return out

def print_html_inner(x):
    assert isnamedtuplewhere(x), x
    def iterate():
        for  _, op in iterate_sub(x):
            if isnamedtuplewhere(op):
                yield print_html_inner(op)

    cur = x.where.character
    out = ""
    for _, a, b, transformed in iterate():
        if a > cur:
            out += x.where.string[cur:a]
        out += transformed
        cur = b

    if cur != x.where.character_end:
        out += x.where.string[cur:x.where.character_end]

    orig0 = x.where.string[x.where.character:x.where.character_end]

    klass = type(x).__name__
    transformed0 = "<span class='%s'>%s</span>" % (klass, out)
    return orig0, x.where.character, x.where.character_end, transformed0




def print_ast(x):
    try:
#         if isinstance(x, list):
#             s = ''
#             for i, xi in enumerate(x):
#                 first = '- '
#                 if i > 0:
#                     s += '\n'
#                 s += indent(print_ast(xi), ' ' * len(first), first=first)
#             return s
        if isnamedtuplewhere(x):
            s = '%s' % type(x).__name__
            s += '  %r' % x.where
            for k, v in iterate_sub(x):
                first = ' %s: ' % k
                s += '\n' + indent(print_ast(v), ' ' * len(first), first=first)

            if x.where is None:
                raise ValueError(x)
            return s
        else:
            return x.__repr__()
    except ValueError as e:
        raise_wrapped(ValueError, e, 'wrong', x=x)

@contract(character_end='int')
def make_tree(x, character_end):

    if not isnamedtuplewhere(x):
        return x

    if x.where.character_end is not None:
        character_end = min(x.where.character_end, character_end)

    fields = {}
    last = None
    for k, v in reversed(list(iterate_sub(x))):
        if last is None:
            v_character_end = character_end
        else:
            if isnamedtuplewhere(last):
                v_character_end = last.where.character - 1
            else:
                v_character_end = character_end

        if isinstance(v, list):
            v2 = make_tree_list(v, character_end=v_character_end)
        else:
            v2 = make_tree(v, character_end=v_character_end)
        fields[k] = v2
        last = v2

    w = x.where

    if w.character_end is None:
        w = Where(string=w.string, character=w.character,
                  character_end=character_end)

    fields['where'] = w
    return type(x)(**fields)

@contract(character_end='int')
def make_tree_list(xs, character_end):
    res = []
    for i, x in enumerate(xs):
        if i < len(xs)- 1:
            next_starts_at = xs[i + 1].where.character
        else:
            next_starts_at = character_end

        x2 = make_tree(x, next_starts_at)
        w = x2.where
        if w.character_end is None:
            where2 = Where(string=w.string, character=w.character,
                       character_end=next_starts_at)
        else:
            where2 = w
        x3 = get_copy_with_where(x2, where=where2)
        res.append(x3)

    return res


def iterate_sub(x):
    def loc(a):
        a = a[1]
        if isnamedtuplewhere(a):
            return a.where.character
        return 0

    o = list(iterate_notwhere(x))
    return sorted(o, key=loc)

def iterate_notwhere(x):
    d = x._asdict()
    for k, v in d.items():
        if k == 'where':
            continue
        yield k, v
