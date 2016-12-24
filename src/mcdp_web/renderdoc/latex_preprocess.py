# -*- coding: utf-8 -*-
import os
import re

from contracts.interface import Where
from contracts.utils import raise_desc, raise_wrapped
from mcdp_web.renderdoc.markdown_transform import is_inside_markdown_quoted_block
from mocdp import logger
from mocdp.exceptions import DPSyntaxError


def latex_preprocessing(s):
    s = s.replace('~$', '&nbsp;$')
#     s = s.replace('{}', '') # cannot do - mcdp { }
    # note: nongreedy matching ("?" after *);
#     def fix(m):
#         x=m.group(1)
#         if not 'eq:' in x:
#             print('fixing %r to eq:%s' % (x, x))
#             x = 'eq:' + x
#         return '\\eqref{%s}' %x
    
    # note: thi
    group = 'TILDETILDETILDE'
    s = s.replace('~~~', group)
    s = s.replace('~', ' ') # XXX
    s = s.replace(group, '~~~')
    
    s = re.sub(r'\\textendash\s*', '&ndash;', s) # XXX
    s = re.sub(r'\\textemdash\s*', '&mdash;', s) # XXX
     
    
    s = re.sub(r'\\noindent\s*', '', s) # XXX
# {[}m{]}}, and we need to choose the \R{endurance~$T$~{[}s{]}}
    s = re.sub(r'{(\[|\])}', r'\1', s)
#     s = re.sub(r'\\R{(.*?)}', r'<r>\1</r>', s)
#     s = re.sub(r'\\F{(.*?)}', r'<f>\1</f>', s)
#     

    # no! let mathjax do it
    def subit(m):
        x = m.group(1)
        if x.startswith('eq:'):
            return '\\ref{%s}' % x
        else:
            return '<a href="#%s" class="only-number"></a>' % x
    s = re.sub(r'\\ref{(.*?)}', subit, s)
    
    s = re.sub(r'\\eqref{(.*?)}', r'\\eqref{eq:\1}', s)
    s = s.replace('eq:eq:', 'eq:')
    
    # \vref
    s = re.sub(r'\\vref{(.*?)}', r'<a class="only-number" href="#\1"></a>', s)
       
    
#     s = re.sub(r'\\eqref{(.*?)}', r'<a href="#eq:\1"></a>', s)
    
    s = re.sub(r'\\lemref{(.*?)}', r'<a href="#lem:\1"></a>', s)
    s = re.sub(r'\\tabref{(.*?)}', r'<a href="#tab:\1"></a>', s)
    s = re.sub(r'\\figref{(.*?)}', r'<a href="#fig:\1"></a>', s)
    s = re.sub(r'\\proref{(.*?)}', r'<a href="#pro:\1"></a>', s)
    s = re.sub(r'\\propref{(.*?)}', r'<a href="#prop:\1"></a>', s)
    s = re.sub(r'\\probref{(.*?)}', r'<a href="#prob:\1"></a>', s)
    s = re.sub(r'\\defref{(.*?)}', r'<a href="#def:\1"></a>', s)
    s = re.sub(r'\\exaref{(.*?)}', r'<a href="#exa:\1"></a>', s)
    s = re.sub(r'\\secref{(.*?)}', r'<a href="#sec:\1"></a>', s)
    s = re.sub(r'\\coderef{(.*?)}', r'<a href="#code:\1"></a>', s)
    
    s = sub_headers(s)               
    s = re.sub(r'\\cite\[(.*)?\]{(.*?)}', r'<a href="#bib:\2">[\1]</a>', s)
    s = re.sub(r'\\cite{(.*?)}', r'<a href="#bib:\1" replace="true"></a>', s)
    
    # note: nongreedy matching ("?" after *); and multiline (re.M) DOTALL = '\n' part of .
    s = re.sub(r'\\emph{(.*?)}', r'<em>\1</em>', s, flags=re.M | re.DOTALL)
    s = re.sub(r'\\textbf{(.*?)}', r'<strong>\1</strong>', s, flags=re.M | re.DOTALL)
    s = s.replace('~"', '&nbsp;&ldquo;')
    s = s.replace('\,', '&ensp;')
    s = s.replace('%\n', '\n')
    
    s = substitute_simple(s, 'etal', 'et. al.')

    s = replace_includegraphics(s)
    s = substitute_command(s, 'fbox', lambda name, inside: 
                           '<div class="fbox">' + inside + "</div>" )
    s = substitute_simple(s, 'scottcontinuity', 'Scott continuity')
    s = substitute_simple(s, 'scottcontinuous', 'Scott continuous')
    
    s = substitute_simple(s, 'xxx', '<div class="xxx">XXX</div>')
    
    s = substitute_simple(s, 'hfill', '')
    s = substitute_simple(s, 'centering', '')
    s = substitute_simple(s, 'bigskip', '<span class="bigskip"/>')
    s = substitute_simple(s, 'medskip', '<span class="medskip"/>')
    s = substitute_simple(s, 'smallskip', '<span class="medskip"/>')
    s = substitute_simple(s, 'par', '<br class="from_latex_par"/>')
    
    s = replace_captionsideleft(s)
    
    s = substitute_command(s, 'F', lambda name, inside: '<span class="Fcolor">%s</span>' % inside)
    s = substitute_command(s, 'R', lambda name, inside: '<span class="Rcolor">%s</span>' % inside)
    s = substitute_command(s, 'uline', lambda name, inside: '<span class="uline">%s</span>' % inside)

    for x in ['footnotesize', 'small', 'normalsize']:
        s = substitute_command(s, x, 
                               lambda name, inside: '<span class="apply-parent %s">%s</span>' % (x, inside))

    s = replace_environment(s, "defn", "definition", "def:")
    s = replace_environment(s, "lem", "lemma", "lem:")
    s = replace_environment(s, "rem", "remark", "rem:")
    s = replace_environment(s, "thm", "theorem", "thm:")
    s = replace_environment(s, "prop", "proposition", ("pro:", "prop:"))
    s = replace_environment(s, "example", "example", "exa:")
    s = replace_environment(s, "proof", "proof", "proof:")
    s = replace_environment(s, "problem", "problem", "prob:")
    s = replace_environment(s, "abstract", "abstract", 'don-t-steal-label')
    s = replace_environment(s, "centering", "centering", 'don-t-steal-label')
    s = replace_environment(s, "center", "center", 'don-t-steal-label')
    
    s = replace_environment_ext(s, "tabular", maketabular)
    s = replace_environment_ext(s, "enumerate", make_enumerate)
    s = replace_environment_ext(s, "itemize", make_itemize)
    s = replace_environment_ext(s, "minipage", makeminipage)
    s = replace_environment_ext(s, "figure", lambda inside, opt: makefigure(inside, opt, False))
    s = replace_environment_ext(s, "figure*", lambda inside, opt: makefigure(inside, opt, True))
    s = replace_environment_ext(s, "table", lambda inside, opt: maketable(inside, opt, False))
    s = replace_environment_ext(s, "table*",lambda inside, opt: maketable(inside, opt, True))
    
    s = s.replace('pro:', 'prop:')

#     s = replace_environment_ext(s, "enumerate", makenumerate)
#     s = replace_environment_ext(s, "itemize", makeitemize)
#     
    s = replace_quotes(s)
#     if 'defn' in s:
#         raise ValueError(s)
    return s

# def makenumerate(inside, opt):
def maketabular(inside, opt):
    # get alignment like {ccc}
    arg, inside = get_balanced_brace(inside)
    align = arg[1:-1]
    
    SEP = '\\\\'
    inside = inside.replace('\\tabularnewline', SEP)
    rows = inside.split(SEP)
    r_htmls = []
    for r in rows:
        columns = r.split('&')
        r_html = "".join('<td>%s</td>' % _ for _ in columns)
        r_htmls.append(r_html)
    html = "".join("<tr>%s</tr>" % _ for _ in r_htmls)
    r = ""
    r += '<table>'
    r += html
    r += '</table>'
    return r

def make_enumerate(inside, opt):
    return make_list(inside, opt, 'ul')
def make_itemize(inside, opt):
    return make_list(inside, opt, 'ul')
    
def make_list(inside, opt, name):
    # get alignment like {ccc}
    assert name in ['ul', 'ol']
    items = inside.split('\\item')
    items = items[1:]
    html = "".join("<li>%s</li>" % _ for _ in items)
    r = "<%s>%s</%s>" % (name, html, name)
    return r

def maketable(inside, opt, asterisk):
    placement = opt  # @UnusedVariable
    
    class Tmp:
        label = None
        caption = None
    
    def sub_caption(args, opts):
        assert not opts and len(args) == 1
        Tmp.caption, Tmp.label = get_s_without_label(args[0], labelprefix="tab:")
        return ''
    
    inside = substitute_command_ext(inside, 'caption', sub_caption, nargs=1, nopt=0)
    assert not '\\caption' in inside

    if Tmp.label is not None:
        idpart = ' id="%s"' % Tmp.label
    else:
        idpart = ""

    if Tmp.caption is not None:
        inside = '<figcaption>' + Tmp.caption + "</figcaption>" + inside
#     print('tmp.caption: %s' % Tmp.caption)
    res  = '<figure class="table"%s>%s</figure>' % (idpart, inside)
    
    if Tmp.label is not None:
        idpart = ' id="%s-wrap"' % Tmp.label
    else:
        idpart = ""

    res = '<div class="table-wrap"%s>%s</div>' % (idpart, res)
    return res

def makeminipage(inside, opt):
    align = opt  # @UnusedVariable
    if inside[0] == '{':
        opt_string, inside = get_balanced_brace(inside)
        latex_width = opt_string[1:-1] # remove brace
    else:
        latex_width = None
    
    if latex_width is not None:
        attrs = ' latex-width="%s"' % latex_width
    else:
        attrs = ''
    
    res  = '<div class="minipage"%s>%s</div>' % (attrs, inside)
    return res

def makefigure(inside, opt, asterisk):
    align = opt  # @UnusedVariable
    
    def subfloat_replace(args, opts):
        contents = args[0]
        caption = opts[0]
        
        caption, label = get_s_without_label(caption, labelprefix="fig:")
        if label is None:
            caption, label = get_s_without_label(caption, labelprefix="subfig:")
        if label is not None and not label.startswith('subfig:'):
            msg = 'Subfigure labels should start with "subfig:"; found %r.' % (label)
            label = 'sub' + label
            msg += 'I will change to %r.' % label
            logger.debug(msg)
            
        if label is not None:
            idpart = ' id="%s"' % label
        else:
            idpart = ""

        if caption is None: caption = 'no subfloat caption'
        res = '<figure class="subfloat"%s>%s<figcaption>%s</figcaption></figure>' % (idpart, contents, caption)
        return res
    
    inside = substitute_command_ext(inside, 'subfloat', subfloat_replace, nargs=1, nopt=1)
    class Tmp:
        label = None
    
    def sub_caption(args, opts):
        assert not opts and len(args) == 1
        x, Tmp.label = get_s_without_label(args[0], labelprefix="fig:")
        res = '<figcaption>' + x + "</figcaption>" 
#         print('caption args: %r, %r' % (args, opts))
        return res
    
    inside = substitute_command_ext(inside, 'caption', sub_caption, nargs=1, nopt=0)
    
#     print('makefigure inside without caption = %r'  % inside)
    assert not '\\caption' in inside

    if Tmp.label is not None:
        idpart = ' id="%s"' % Tmp.label
    else:
        idpart = ""

    res  = '<figure%s>%s</figure>' % (idpart, inside)
    return res

def sub_headers(s):
    def sub_header(ss, cmd, hname, number=True):
        def replace(name, inside):  # @UnusedVariable
            options = ""
            options += ' nonumber=""' if number is False else ''
            inside, label = get_s_without_label(inside, labelprefix=None)
            options += ' id="%s"' % label if label is not None else ''
            template = '<{hname}{options}>{inside}</{hname}>' 
            r = template.format(hname=hname, inside=inside, options=options)
            return r
        return substitute_command(ss, cmd, replace)
    
    # note that we need to do the * version before the others
    s = sub_header(s, cmd='section*', hname='h1', number=False)
    s = sub_header(s, cmd='section', hname='h1', number=True)
    s = sub_header(s, cmd='subsection*', hname='h2', number=False)
    s = sub_header(s, cmd='subsection', hname='h2', number=True)
    s = sub_header(s, cmd='subsubsection*', hname='h3', number=False)
    s = sub_header(s, cmd='subsubsection', hname='h3', number=True)
    return s
  
def substitute_simple(s, name, replace):
    """
        \ciao material-> submaterial
        \ciao{} material -> submaterial
    """
    start = '\\' + name
    if not start in s:
        return s
    
    # points to the '{'
    istart = s.index(start)
    i = istart + len(start)
    
    if i >= len(s) - 1:
        is_match = True
    else:
        assert i < len(s) -1 
        next_char = s[i+1] 
        
        # don't match '\ciao' when looking for '\c'
        is_match = not next_char.isalpha()
        
    if not is_match:
        return s[:i] + substitute_simple(s[i:], name, replace) 


    after0 = s[i:]
    eat_space = True
    if len(after0)> 2 and after0[:2] == '{}':
        eat_space = False
            
    if eat_space:
        while i < len(s) and (s[i] in [' ']):
            i += 1
    after = s[i:]
    
    before = s[:istart] 
    return before + replace + substitute_simple(after, name, replace)
    
    
    
class Malformed(Exception):
    pass

def substitute_command_ext(s, name, f, nargs, nopt):
    """
        Subsitute \name[x]{y}{z} with 
        f : args=(x, y), opts=None -> s
        if nargs=1 and nopt = 0:
            f : x -> s
    """
    lookfor = ('\\' + name) +( '[' if nopt > 0 else '{')
    
    try:
        start = get_next_unescaped_appearance(s, lookfor, 0)
        assert s[start:].startswith(lookfor)
#         print('s[start:] starts with %r %r' % s[start:])
    except NotFound:
        return s
    
    before = s[:start]
    rest = s[start:]
#     print('before: %r' % before)
    assert s[start:].startswith('\\'+name)
#     print('s[start:]: %r' % s[start:])
    assert rest.startswith('\\'+name)
    assert not ('\\' + name ) in before, before
    
    consume = consume0 = s[start + len(lookfor) - 1:]
    
    opts = []
    args = []
    
#     print('consume= %r'% consume)
    for _ in range(nopt):
        consume = consume_whitespace(consume)
        if not consume or consume[0] != '[':
#             print('skipping option')
            opt = None
        else:
            opt_string, consume = get_balanced_brace(consume)
#             print('opt string %r consume %r' % (opt_string, consume))
            opt = opt_string[1:-1] # remove brace
        opts.append(opt)
        
#     print('after opts= %r'% consume)
    for _ in range(nargs):
        consume = consume_whitespace(consume)
        if not consume or consume[0] != '{':
            msg = 'Command %r: Expected {: got %r. opts=%s args=%s' % (name, consume[0], opts, args)
            character = start 
            character_end =  len(s) - len(consume)
            where = Where(s, character, character_end)
            raise DPSyntaxError(msg, where=where)            
        arg_string, consume2  = get_balanced_brace(consume)
        assert arg_string + consume2 == consume
        consume = consume2
        arg = arg_string[1:-1] # remove brace
        args.append(arg)
#     print('substitute_command_ext for %r : args = %s opts = %s consume0 = %r' % (name, args, opts, consume0))
    args = tuple(args)
    opts = tuple(opts)
    replace = f(args=args, opts=opts)
    after_tran = substitute_command_ext(consume, name, f, nargs, nopt)
    res = before + replace + after_tran
#     print('before: %r' % before) 
#     print('replace: %r' % replace)
#     print('after_tran: %r' % after_tran)
    assert not ('\\' + name ) in res, res
    return res

def consume_whitespace(s):
    while s and (s[0] in  [' ']):
        s = s[1:]
    return s

def substitute_command(s, name, sub):
    """
        Subsitute \name{<inside>} with 
        sub : name, inside -> s
    """
    
    start = '\\' + name + '{'
    if not start in s:
        return s
    
    # points to the '{'
    istart = s.index(start)
    i = istart + len(start) -1 # minus brace
    after = s[i:]
#     
#     # don't match '\ciao' when looking for '\c'
#     is_match = not next_char.isalpha()
#     if not is_match:
#         return s[:i] + substitute_command(s[i:], name, sub) 
#     
#     if not after[0] == '{':
#         msg = 'I expected brace after %r, but I see .' % start
#         raise_desc(ValueError, msg, s=s) 
    try:
        assert after[0] == '{'
        inside_plus_brace, after = get_balanced_brace(after)
    except Malformed as e:
        bit = after[:max(len(after), 15 )]
        msg = 'Could not find completion for "%s".' % bit
        raise_wrapped(Malformed, e, msg)
    inside = inside_plus_brace[1:-1]
    replace = sub(name=name, inside=inside)
    before = s[:istart]
    after_tran = substitute_command(after, name, sub)
    res = before + replace + after_tran
    return res
    
    
def get_balanced_brace(s):
    """ s is a string that starts with '{'. 
        returns pair a, b, with a + b = s and 
        a starting and ending with braces
     """
    assert s[0] in ['{', '[']
    stack = []
    i = 0
    while i <= len(s):
        if s[i] == '{':
            stack.append(s[i])
        if s[i] == '[':
            stack.append(s[i])
        if s[i] == '}':
            if not stack or stack[-1] != '{':
                raise Malformed(stack)
            stack.pop()
        if s[i] == ']':
            if not stack or stack[-1] != '[':
                raise Malformed(stack)
            stack.pop()

        if not stack:
            a = s[:i+1]
            b = s[i+1:]
            break
        i += 1
    if stack:
        msg = 'Unmatched braces (stack = %s)' % stack
        raise_desc(Malformed, s, msg)
    assert a[0] in ['{', '['] 
    assert a[-1] in ['}', ']']
    assert a + b == s
    return a, b
    
def replace_quotes(s):
    """ Replaces ``xxx'' sequences """
    START = '``'
    if not START in s:
        return s
    END = "''"
    a = s.index(START)
    if not END in s[a:]:
        return s
    
    b = s.index(END, a) + len(END)
    
    inside = s[a+len(START):b-len(END)]
    if '\n\n' in inside:
        return s
    max_dist = 200
    if len(inside) > max_dist:
        return s
    repl = '&ldquo;' + inside + '&rdquo;'
    s2 = s[:a] + repl + s[b:]
    return replace_quotes(s2)
    
def replace_environment_ext(s, envname, f):
    # need to escape *
    if '*' in envname:
        envname = envname.replace('*', '\\*')
    reg = '\\\\begin{%s}(\\[.*?\\])?(.*?)\\\\end{%s}' % (envname, envname)
    # note multiline and matching '\n'
    reg = re.compile(reg, flags=re.M | re.DOTALL)
    def S(m):
        if m.group(1) is not None:
            opt = m.group(1)[1:-1]
        else:
            opt = None
        inside = m.group(2)
        return f(inside=inside, opt=opt)
    s = re.sub(reg, S, s)
    return s
    
def replace_environment(s, envname, classname, labelprefix):
    def replace_m(inside, opt):
        thm_label = opt
        contents, label = get_s_without_label(inside, labelprefix=labelprefix)
        if label is not None and isinstance(labelprefix, str):
            assert label.startswith(labelprefix), (s, labelprefix, label)
        id_part = "id='%s' "% label if label is not None else ""
        
#         print('using label %r for env %r (labelprefix %r)' % (label, envname, labelprefix))
        l = "<span class='%s_label latex_env_label'>%s</span>" % (classname, thm_label) if thm_label else ""
        rr = '<div %sclass="%s latex_env" markdown="1">%s%s</div>' % (id_part, classname, l, contents)
        return rr
    return replace_environment_ext(s, envname, replace_m)
    
def replace_captionsideleft(s):
    assert not 'includegraphics' in s
    def match(matchobj):
        first = matchobj.group(1)
        first2, label = get_s_without_label(first, labelprefix="fig:")
        second = matchobj.group(2)
        if label is not None:
            idpart = ' id="%s"' % label
        else:
            idpart = ""
        res = ('<figure class="captionsideleft"%s>' % idpart)
        res += ('%s<figcaption></figcaption></figure>') % second
        
        return res
        
    s = re.sub(r'\\captionsideleft{(.*?)}{(.*?)}', 
               match, s, flags=re.M | re.DOTALL)
    return s

def replace_includegraphics(s):
    
#     \includegraphics[scale=0.4]{boot-art/1509-gmcdp/gmcdp_antichains_upsets}
    def match(matchobj):
        latex_options = matchobj.group(1)
        # remove [, ]
        latex_options = latex_options[1:-1]
        latex_path = matchobj.group(2)
        basename = os.path.basename(latex_path)
        res = '<img src="%s.pdf" latex-options="%s" latex-path="%s"/>' % (
                basename, latex_options, latex_path
            )
        return res
        
    s = re.sub(r'\\includegraphics(\[.*?\])?{(.*?)}', 
               match, s, flags=re.M | re.DOTALL)
    return s

def get_s_without_label(contents, labelprefix=None):
    """ Returns a pair s', label 
        where label could be None """
    class Scope:
        def_id = None
    def got_it(m):
        found = m.group(1)
        if labelprefix is None:
            ok = True
        else:
            if  isinstance(labelprefix, tuple):
                options = labelprefix
            elif isinstance(labelprefix, str):
                options = (labelprefix,)
            else: 
                raise ValueError(labelprefix)
            ok = any(found.startswith(_) for _ in options)
        
        if ok:
            Scope.def_id = found
            # extract
#             print('looking for labelprefix %r found label %r in %s' % ( labelprefix, found, contents))
            return ""
        else:
#             print('not using %r' % ( found))
            # keep 
            return "\\label{%s}" % found
        
    contents2 = re.sub(r'\\label{(.*?)}', got_it, contents)
    label =  Scope.def_id
    if isinstance(labelprefix, str) and label is not None:
        assert label.startswith(labelprefix), (label, labelprefix)
    return contents2, label
    
def replace_equations(s):
    class Tmp:
        count = 0
        format = None
        
    def replace_eq(matchobj):
        contents = matchobj.group(1)        
        contents2, label = get_s_without_label(contents, labelprefix = None)
#         print('contents %r - %r label %r' % (contents, contents2, label))
        if label is not None:
#             print('found label %r' % label)
            contents2 +='\\label{%s}' % label
            contents2 +='\\tag{%s}' % (Tmp.count + 1)
            Tmp.count += 1
        f = Tmp.format
        s = f(Tmp(), contents2)
        return s
    
    # do this first
    reg = r'\$\$(.*?)\$\$' 
    Tmp.format = lambda self, x : '$$%s$$' % x
    s = re.sub(reg, replace_eq, s, flags=re.M | re.DOTALL)

    reg = r'\\\[(.*?)\\\]'
    Tmp.format = lambda self, x : '$$%s$$' % x
    s = re.sub(reg, replace_eq, s, flags=re.M | re.DOTALL)
    
    reg = r'\\begin{equation}(.*?)\\end{equation}'
    Tmp.format = lambda self, x : '\\begin{equation}%s\\end{equation}' % x
    s = re.sub(reg, replace_eq, s, flags=re.M | re.DOTALL)
    
    reg = r'\\begin{align}(.*?)\\end{align}'
    Tmp.format = lambda self, x : '\\begin{align}%s\\end{align}' % x
    s = re.sub(reg, replace_eq, s, flags=re.M | re.DOTALL)
    
    reg = r'\\begin{align\*}(.*?)\\end{align\*}'
    Tmp.format = lambda self, x : '\\begin{align*}%s\\end{align*}' % x
    s = re.sub(reg, replace_eq, s, flags=re.M | re.DOTALL)

    reg = r'\\begin{eqnarray\*}(.*?)\\end{eqnarray\*}'
    Tmp.format = lambda self, x : '\\begin{eqnarray*}%s\\end{eqnarray*}' % x
    s = re.sub(reg, replace_eq, s, flags=re.M | re.DOTALL)
    
    reg = r'\\begin{eqnarray}(.*?)\\end{eqnarray}'
    Tmp.format = lambda self, x : '\\begin{eqnarray}%s\\end{eqnarray}' % x
    s = re.sub(reg, replace_eq, s, flags=re.M | re.DOTALL)

    return s


def get_next_unescaped_appearance(s, d1, search_from):
    while True:
        if not d1 in s[search_from:]:
#             print('nope, no %r in s[%s:] = %r' % (d1,search_from, s[search_from:]))
            raise NotFound()
        maybe = s.index(d1, search_from)
        if s[maybe-1] == '\\':
#             print('found escaped match of %r (prev chars = %r)' % (d1, s[:maybe]))
            search_from = maybe + 1
        else:
            assert s[maybe:].startswith(d1)
#             print('found %r at %r ' % (d1, s[maybe:]))
            return maybe
        
class NotFound(Exception):
    pass

        
def extract_delimited(s, d1, d2, subs, domain, acceptance=None):
    """
        acceptance: s, i -> Bool
    """
    if acceptance is None:
        acceptance = lambda _s, _i : True
    try:
        a_search_from = 0
        while True:
            a = get_next_unescaped_appearance(s, d1, a_search_from)
            if acceptance(s, a):
                break
            a_search_from = a + 1 
            
#         print('found delimiter start %r in %r at a = %s' %( d1,s,a))
        assert s[a:].startswith(d1)
    except NotFound:
        return s 
    try:
        search_d1_from = a + len(d1)
#         print('search_d1_from = %s' % search_d1_from)
        b0 = get_next_unescaped_appearance(s, d2, search_d1_from)
        assert b0 >= search_d1_from
        assert s[b0:].startswith(d2)
        b = b0 + len(d2)
        complete = s[a:b]
    except NotFound:
        assert s[a:].startswith(d1)
#         print('could not find delimiter d2 %r in %r' % (d2, s[search_d1_from:]))
        return s 
    assert complete.startswith(d1)
    assert complete.endswith(d2)
    #inside = s[a+len(d1):b-len(d2)]
    key = 'KEY%s%0003dD'% (domain,len(subs))
    if 'KEY' in complete:
        msg = 'recursive - %s = %r' % (key, complete)
        msg += '\n\n'
        def abit(s):
            def nl(x):
                return x.replace('\n', ' ↵ ')
            L = len(s)
            if L < 80: return nl(s)
            ss = nl(s[:min(L, 50)])
            se = nl(s[L-min(L, 50):])
            return ss + ' ... ' + se
        for k in sorted(subs):
            msg += '%r = %s\n' % (k, abit(subs[k]))
            
        raise ValueError(msg)
    subs[key] = complete
    
#     print ('%r = %s' % (key, complete))
    s2 = s[:a] + key + s[b:]
    return extract_delimited(s2, d1, d2, subs, domain, acceptance=acceptance)
    


def extract_maths(s):
    """ returns s2, subs(str->str) """
    # these first, because they might contain $ $
    envs = [
        'equation','align','align*',
            
            # no - should be inside of $$
            'eqnarray','eqnarray*',
            
#             'tabular' # have pesky &
            ]
 
    delimiters = []
    for e in envs:
        delimiters.append(('\\begin{%s}' % e, '\\end{%s}'% e))
   
    # AFTER the environments
    delimiters.extend([('$$','$$'),
                    ('$','$'),
                   ('\\[', '\\]')])
    
    def acceptance(s0, i):
        inside = is_inside_markdown_quoted_block(s0, i)
        return not inside
    
    subs = {}
    for d1, d2 in delimiters:
        s = extract_delimited(s, d1, d2, subs, domain='MATHS', acceptance=acceptance)
        
#     # This should not be used anymore
#     for k, v in list(subs.items()):
#         # replace back if k is in a line that is a comment
#         # or there is an odd numbers of \n~~~
#         if is_inside_markdown_quoted_block(s, s.index(k)):
#             s = s.replace(k, v)
#             del subs[k]
  
    return s, subs

if __name__ == '__main__':
    s = """
For example, the expression <mcpd-value>&lt;2 J, 1 A&gt;</mcdp-value>
denotes a tuple with two elements, equal to <mcdp-value>2 J</mcpd-value>
and <code class='mcdp-value'>2 A</code>.
"""
    d1 = '<mcdp-value'
    a = get_next_unescaped_appearance(s, d1, 0)

