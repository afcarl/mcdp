from mcdp_figures.figures_ndp import MakeFiguresNDP
from mcdp_figures.figures_poset import MakeFiguresPoset
from mcdp_posets import FinitePoset
from mcdp_report.gg_ndp import gvgen_from_ndp
from mcdp_report.gg_utils import gg_get_format
from mcdp_web.utils.image_error_catch_imp import create_image_with_string
from mocdp.comp.template_for_nameddp import TemplateForNamedDP
from mocdp.exceptions import mcdp_dev_warning


def get_png_data_model(library, name, ndp, data_format): 
    mf = MakeFiguresNDP(ndp=ndp, library=library, yourname=name)
    f = 'fancy_editor' 
    res = mf.get_figure(f, data_format)
    return res

def get_png_data_syntax_model(library, name, ndp, data_format):
    mf = MakeFiguresNDP(ndp=ndp, library=library, yourname=name)
    f = 'ndp_graph_enclosed_TB' 
    res = mf.get_figure(f, data_format)
    return res

def ndp_template_enclosed(library, name, x, data_format):
    from mcdp_report.gdc import STYLE_GREENREDSYM

    return ndp_template_graph_enclosed(library, x, style=STYLE_GREENREDSYM, yourname=name,
                                       data_format=data_format, direction='TB', enclosed=True)

def ndp_template_graph_enclosed(library, template, style, yourname, data_format, direction, enclosed):
    assert isinstance(template, TemplateForNamedDP)
    mcdp_dev_warning('Wrong - need assume ndp const')

    context = library._generate_context_with_hooks()

    ndp = template.get_template_with_holes(context)

    if enclosed:
        setattr(ndp, '_hack_force_enclose', True)

    images_paths = library.get_images_paths()
    gg = gvgen_from_ndp(ndp, style=style, direction=direction,
                        images_paths=images_paths, yourname=yourname)
    return gg_get_format(gg, data_format)
    
def get_png_data_poset(library, name, x, data_format):  # @UnusedVariable
    if isinstance(x, FinitePoset):
        mf = MakeFiguresPoset(x, library=library)
        f = 'hasse_icons' 
        res = mf.get_figure(f, data_format)
        return res
    else:
        s = str(x)
        return create_image_with_string(s, size=(512, 512), color=(128, 128, 128))

def get_png_data_unavailable(library, name, x, data_format):  # @UnusedVariable
    s = str(x)
    return create_image_with_string(s, size=(512, 512), color=(0, 0, 255))
