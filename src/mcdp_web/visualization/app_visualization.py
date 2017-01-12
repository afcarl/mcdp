# -*- coding: utf-8 -*-

from collections import namedtuple

from bs4.element import Declaration, ProcessingInstruction, Doctype, Comment,\
    Tag

from mcdp_lang.namedtuple_tricks import recursive_print
from mcdp_lang.parts import CDPLanguage
from mcdp_lang.utils_lists import unwrap_list
from mcdp_library import MCDPLibrary
from mcdp_library_tests.tests import timeit_wall
from mcdp_report.html import ast_to_html
from mcdp_web.editor_fancy.app_editor_fancy_generic import specs
from mcdp_web.renderdoc.highlight import add_style
from mcdp_web.renderdoc.xmlutils import to_html_stripping_fragment, bs
from mcdp_web.utils.response import response_data
from mocdp.comp.context import Context
from mocdp.exceptions import DPSyntaxError, DPSemanticError


class AppVisualization():

    def __init__(self):
        pass

    def config(self, config):
        
        renderer = 'visualization/syntax.jinja2'
        generate_view = self.generate_view
        generate_graph = self.generate_graph
        
        for s in specs:
            url = ('/libraries/{library}/%s/{%s}/views/syntax/' % 
                   (specs[s].url_part, specs[s].url_variable))
            route = 'visualization_%s_syntax' % s
            
            config.add_route(route, url)    
            
            class G():
                def __init__(self, spec):
                    self.spec = spec

                def __call__(self, request):
                    return generate_view(request, self.spec)

            # scoping bug!                    
            #view = lambda request: self.generate_view(request, specs[s])
            config.add_view(G(specs[s]), route_name=route, renderer=renderer)
            
            graph_route = 'visualization_%s_graph' % s
            graph_url = url + 'graph.{data_format}'
            config.add_route(graph_route, graph_url)    


            class H():
                def __init__(self, spec):
                    self.spec = spec

                def __call__(self, request):
                    return generate_graph(request, self.spec)

            
            config.add_view(H(specs[s]), route_name=graph_route, renderer=renderer)


        # these are images view for which the only change is the jinja2 template
        image_views = [
            'dp_graph', 
            'dp_tree', 
            'ndp_graph',
        ]
        for image_view in image_views:
            route = 'model_%s' % image_view
            url = self.get_lmv_url('{library}', '{model_name}', image_view)
            renderer = 'visualization/model_%s.jinja2' % image_view
            config.add_route(route, url)
            config.add_view(self.view_model_info, route_name=route, renderer=renderer)
 

        config.add_route('model_ndp_repr',
                         self.get_lmv_url('{library}', '{model_name}', 'ndp_repr'))
        config.add_view(self.view_model_ndp_repr, route_name='model_ndp_repr',
                        renderer='visualization/model_generic_text_content.jinja2')


    def view_model_info(self, request):
        return {
            'model_name': self.get_model_name(request),
            'views': self._get_views(),
            'navigation': self.get_navigation_links(request),
        }
 

    def view_model_ndp_repr(self, request):
        model_name = str(request.matchdict['model_name'])  # unicode

        ndp = self.get_library(request).load_ndp(model_name)
        ndp_string = ndp.__repr__()
        ndp_string = ndp_string.decode("utf8")

        return {
            'model_name': model_name,
            'content': ndp_string,
            'navigation': self.get_navigation_links(request),
        }
 

    def generate_view(self, request, spec):
        name = str(request.matchdict[spec.url_variable])  # unicode
        ext = spec.extension
        expr = spec.parse_expr
        parse_refine = spec.parse_refine

        res = self._generate_view_syntax(request, name, ext, expr, parse_refine, spec)
        return res

    def generate_graph(self, request, spec):
        def go():
            with timeit_wall('generate_graph', 1.0):
                data_format = str(request.matchdict['data_format'])  # unicode
                library = self.get_library(request)
                widget_name = self.get_widget_name(request, spec)
#                 library_name = self.get_current_library_name(request)
#                 key = (library_name, spec, widget_name)
    
#                 if not key in self.last_processed2:
                l = self.get_library(request)
                context = l._generate_context_with_hooks()
                thing = spec.load(l, widget_name, context=context)
#                 else:
#                     thing = self.last_processed2[key]
#                     if thing is None:
#                         return response_image(request, 'Could not parse.')
    
                with timeit_wall('graph_generic - get_png_data', 1.0):
                    data = spec.get_png_data_syntax(library, widget_name, thing, 
                                             data_format=data_format)
                    
                from mcdp_web.images.images import get_mime_for_format
                mime = get_mime_for_format(data_format)
                return response_data(request, data, mime)
        return self.png_error_catch2(request, go)
    
    def _generate_view_syntax(self, request, name, ext, expr, parse_refine, spec):
        url_part = spec.url_part
        filename = '%s.%s' % (name, ext)
        l = self.get_library(request)
        library_name = self.get_current_library_name(request)
        f = l._get_file_data(filename)
        source_code = f['data']
        realpath = f['realpath']
        
        md1 = '%s.%s' % (name, MCDPLibrary.ext_explanation1)
        if l.file_exists(md1):
            fd = l._get_file_data(md1)
            html1 = self.render_markdown(fd['data'])
        else:
            html1 = None

        md2 = '%s.%s' % (name, MCDPLibrary.ext_explanation2)
        if l.file_exists(md2):
            fd = l._get_file_data(md2)
            html2 = self.render_markdown(fd['data'])
        else:
            html2 = None
            
        context = Context()
        class Tmp:
            refined = None
        def postprocess(block):
            if parse_refine is None:
                return block
            try:
                Tmp.refined = parse_refine(block, context) 
                return Tmp.refined
            except DPSemanticError:
                return block 
              
        try:
            highlight = ast_to_html(source_code,
                                    add_line_gutter=False,
                                    parse_expr=expr,
                                    postprocess=postprocess)
            
            highlight = self.add_html_links(request, highlight)
            error = ''
        except DPSyntaxError as e:
            highlight = '<pre class="source_code_with_error">%s</pre>' % source_code
            error = e.__str__()
            
        navigation = self.get_navigation_links(request)
        
        url_edit = ("/libraries/%s/%s/%s/views/edit_fancy/" %  
                    (navigation['current_library'],
                     url_part,
                     name)) 
        context = l._generate_context_with_hooks()
        thing = spec.load(l, name, context=context)
        with timeit_wall('graph_generic - get_png_data', 1.0):
            svg_data0 = spec.get_png_data_syntax(l, name, thing, data_format='svg')
            fragment = bs(svg_data0)
            assert fragment.svg is not None
#             if True:
#                 for a in ['width', 'height']:
#                     if a in fragment.svg.attrs:
#                         del fragment.svg.attrs[a]
#                         c = Comment('Removed attribute %r' % a)
#                         fragment.svg.insert_before(c)
            if True:
                style = {}
                for a in ['width', 'height']:
                    if a in fragment.svg.attrs:
                        value = fragment.svg.attrs[a]
                        del fragment.svg.attrs[a]
                        style['max-%s' %a ]= value
                add_style(fragment.svg, **style)
                    
            for e in list(fragment):
                remove = (Declaration, ProcessingInstruction, Doctype)
                if isinstance(e, remove):
                    c = Comment('Removed object of type %s' % type(e).__name__)
                    e.replace_with(c)
            remove_all_titles(fragment.svg)
            
            if Tmp.refined is not None:
                table = identifier2ndp(Tmp.refined)
            else:
                print('no refined available')
                table = {}
            print table
            def link_for_dp_name(identifier0):
                identifier = identifier0 # todo translate
                if identifier in table:
                    a = table[identifier]
                    libname = a.libname if a.libname is not None else library_name
                    href = self.get_lmv_url(libname, a.name, 'syntax')
                    #href = '/libraries/%s/models/%s/views/syntax/' %(libname, name)
                    return href
                else:
                    return None
                                        
            
            add_html_links_to_svg(fragment.svg, link_for_dp_name)
            svg_data = to_html_stripping_fragment(fragment)
        res= {
            'source_code': source_code,
            'error': unicode(error, 'utf-8'),
            'highlight': highlight,
            'realpath': realpath,
            'navigation': navigation, 
            'current_view': 'syntax',
            'explanation1_html': html1,
            'explanation2_html': html2,
            'svg_data': unicode(svg_data, 'utf-8'),
            'url_edit': url_edit,
        }
        return res

    def add_html_links(self, request, frag):
        """ Puts links to the models. """
        library = self.get_current_library_name(request)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(frag, 'html.parser', from_encoding='utf-8')
        from bs4.element import NavigableString

        # look for links of the type:
        # <span class="FromLibraryKeyword">new</span>
        #     <span class="NDPName"> Actuation_a2_vel</span>
        # </span>

        def break_string(s):
            """ Returns initial ws, middle, final ws. """
            middle = s.strip()
            initial = s[:len(s) - len(s.lstrip())]
            final = s[len(s.rstrip()):]
            assert initial + middle + final == s, (initial, middle, final, s)
            return initial, middle, final

        def get_name_from_tag(tag):
            _, middle, _ = break_string(tag.string)
            return middle.encode('utf-8')

        def add_link_to_ndpname(tag, href):
            initial, middle, final = break_string(tag.string)
            tag.string = ''
            name = middle
            attrs = {'class': 'link-to-model', 'href': href, 'target': '_blank'}
            new_tag = soup.new_tag("a", **attrs)
            new_tag.string = name
            tag.append(NavigableString(initial))
            tag.append(new_tag)
            tag.append(NavigableString(final))

        def sub_ndpname():

            for tag in soup.select('span.NDPName'):
                if 'NDPNameWithLibrary' in tag.parent['class']:
                    continue

                ndpname = get_name_from_tag(tag)
                href = self.get_lmv_url(library, ndpname, 'syntax')
                add_link_to_ndpname(tag=tag, href=href)

        def sub_ndpname_with_library():
            for tag in soup.select('span.NDPNameWithLibrary'):
                tag_libraryname = list(tag.select('span.LibraryName'))[0]
                tag_ndpname = list(tag.select('span.NDPName'))[0]

                ndpname = get_name_from_tag(tag_ndpname)
                libname = get_name_from_tag(tag_libraryname)
                href = self.get_lmv_url(libname, ndpname, 'syntax')
                add_link_to_ndpname(tag=tag_ndpname, href=href)

#             if False:
#                 # TODO: add this as a feature
#                 img = '/solver/%s/compact_graph' % name
#                 attrs = {'src': img, 'class': 'popup'}
#                 new_tag = soup.new_tag("img", **attrs)
#                 tag.append(new_tag)

        def sub_template_name():
            for tag in soup.select('span.TemplateName'):
                if 'TemplateNameWithLibrary' in tag.parent['class']:
                    continue

                templatename = get_name_from_tag(tag)
                href = self.get_ltv_url(library, templatename, 'syntax')

                add_link_to_ndpname(tag=tag, href=href)

        def sub_template_name_with_library():
            for tag in soup.select('span.TemplateNameWithLibrary'):
                tag_libraryname = list(tag.select('span.LibraryName'))[0]
                tag_templatename = list(tag.select('span.TemplateName'))[0]

                templatename = get_name_from_tag(tag_templatename)
                libname = get_name_from_tag(tag_libraryname)
                href = self.get_ltv_url(libname, templatename, 'syntax')
                add_link_to_ndpname(tag=tag_templatename, href=href)

        def sub_poset_name():
            for tag in soup.select('span.PosetName'):
                if 'PosetNameWithLibrary' in tag.parent['class']:
                    continue

                posetname = get_name_from_tag(tag)
                href = self.get_lpv_url(library, posetname, 'syntax')

                add_link_to_ndpname(tag=tag, href=href)

        def sub_poset_name_with_library():
            for tag in soup.select('span.PosetNameWithLibrary'):
                tag_libraryname = list(tag.select('span.LibraryName'))[0]
                tag_posetname = list(tag.select('span.PosetName'))[0]

                posetname = get_name_from_tag(tag_posetname)
                libname = get_name_from_tag(tag_libraryname)
                href = self.get_lpv_url(libname, posetname, 'syntax')
                add_link_to_ndpname(tag=tag_posetname, href=href)


        def sub_libraryname():
            # Need to be last
            for tag in soup.select('span.LibraryName'):
                libname = get_name_from_tag(tag)
                href = '/libraries/%s/' % libname
                add_link_to_ndpname(tag=tag, href=href)

        try:
            sub_ndpname()
            sub_ndpname_with_library()
            sub_template_name()
            sub_template_name_with_library()
            sub_poset_name()
            sub_poset_name_with_library()
            sub_libraryname()  # keep last
        except:
            # print soup
            raise
        # keep above last!

        # Add documentation links for each span
        # that has a class that finishes in "Keyword"
        if False: 
            def select_tags():
                for tag in soup.select('span'):
                    if 'class' in tag.attrs:
                        klass = tag.attrs['class'][0]
                        if 'Keyword' in klass:
                            yield tag

            manual = '/docs/language_notes/'

            for tag in select_tags():
                keyword = tag.attrs['class'][0]
                link = manual + '#' + keyword
                text = tag.string
                tag.string = ''
                attrs = {'class': 'link-to-keyword', 'href': link, 'target': '_blank'}
                new_tag = soup.new_tag("a", **attrs)
                new_tag.string = text
                tag.append(new_tag)

        return soup.prettify()

def remove_all_titles(svg):
    assert isinstance(svg, Tag) and svg.name == 'svg'
    for e in svg.select('[title]'):
        del e.attrs['title']
    for e in svg.select('title'):
        e.extract()

def add_html_links_to_svg(svg, link_for_dpname):
    assert isinstance(svg, Tag) and svg.name == 'svg'
    
    def enclose_in_link(element, href):
        a = Tag(name='a')
        a['href'] = href
        a.append(element.__copy__())
        element.replace_with(a)
        
#     <text font-family="Anka/Coder Narrow" font-size="14.00" text-anchor="start" x="421.092" y="-863.288">nozzle</text>
    for e in svg.select('text'):
        t = e.text.encode('utf-8')
        is_identifier = not ' ' in t and not '[' in t
        if is_identifier:
            href = link_for_dpname(t)
            if href is not None:
                s0 = e.next_sibling
                while s0 != None:
                    if isinstance(s0, Tag) and s0.name == 'image':
                        enclose_in_link(s0, href)
                        break
                    s0 = s0.next_sibling
                
                enclose_in_link(e, href)
                
                
        

LibnameName = namedtuple('LibnameName', 'libname name')
   
CDP = CDPLanguage
def identifier2ndp(xr):
    """ Returns a map identifier -> (libname, ndpname) where libname can be None """
    
    res = {}
    
    if isinstance(xr, CDP.BuildProblem):
        for s in unwrap_list(xr.statements.statements):
            if isinstance(s, CDP.SetNameNDPInstance):
                print recursive_print(s)
                name = s.name.value
                ndp = s.dp_rvalue
                if isinstance(ndp, CDP.DPInstance):
                    if isinstance(ndp.dp_rvalue, CDP.LoadNDP):
                        load_arg = ndp.dp_rvalue.load_arg
                        res[name] = get_from_load_arg(load_arg)
                elif isinstance(ndp, CDP.CoproductWithNames):
                    look_in_coproduct_with_names(ndp, res)
                    
    elif isinstance(xr, CDP.CoproductWithNames):
        look_in_coproduct_with_names(xr, res)
    return res

def get_from_load_arg(load_arg):
    if isinstance(load_arg, CDP.NDPName):
        model = load_arg.value
        libname = None
    elif isinstance(load_arg, CDP.NDPNameWithLibrary):
        libname =load_arg.library.value 
        model = load_arg.name.value
    else:
        raise Exception(recursive_print(load_arg))
    return LibnameName(libname, model)

def look_in_coproduct_with_names(x, res):
    assert isinstance(x, CDP.CoproductWithNames)

    ops = unwrap_list(x.elements)
    nops = len(ops)
    n = nops/2
    for i in range(n):
        e, load = ops[i*2], ops[i*2 +1]
        assert isinstance(e, CDP.CoproductWithNamesName)
        name = e.value
        res[name] = get_from_load_arg(load.load_arg)
                