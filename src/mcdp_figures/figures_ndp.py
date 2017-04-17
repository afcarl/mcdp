from contracts import contract
from contracts.utils import raise_wrapped

from mcdp.constants import MCDPConstants
from mcdp_report.gg_ndp import gvgen_from_ndp
from mcdp_report.image_source import NoImages

from .figure_interface import MakeFigures
from .formatters import MakeFigures_Formatter, TextFormatter, GGFormatter


__all__ = [
    'MakeFiguresNDP',
]

class MakeFiguresNDP(MakeFigures):
    
    @contract(image_source='None|isinstance(ImagesSource)')
    def __init__(self, ndp, image_source=None, yourname=None):
        self.ndp = ndp
        self.yourname = yourname
        if image_source is None:
            image_source = NoImages()
        self.image_source = image_source
        
        aliases = {
            'ndp_graph_enclosed': 'ndp_graph_enclosed_LR',
            'ndp_graph_expand': 'ndp_graph_expand_LR',
            'ndp_graph_templatized': 'ndp_graph_templatized_LR',
            'ndp_graph_templatized_labeled': 'ndp_graph_templatized_labeled_LR',
            'ndp_graph_normal': 'ndp_graph_normal_LR',
        }
        
        from mcdp_report.gdc import STYLE_GREENREDSYM
        
        figure2function = {
            'fancy_editor': (Enclosed, 
                dict(direction='TB', enclosed=True, style=STYLE_GREENREDSYM, skip_initial=False)),
            'fancy_editor_LR': (Enclosed, 
                dict(direction='LR', enclosed=True, style=STYLE_GREENREDSYM, skip_initial=False)),
            'ndp_graph_enclosed_LR': (Enclosed, 
                dict(direction='LR', enclosed=True, style=STYLE_GREENREDSYM)), 
            'ndp_graph_enclosed_TB': (Enclosed, 
                dict(direction='TB', enclosed=True, style=STYLE_GREENREDSYM)),
            'ndp_graph_expand_LR': (Expand, 
                dict(direction='LR', style=STYLE_GREENREDSYM)), 
            'ndp_graph_expand_TB': (Expand, 
                dict(direction='TB', style=STYLE_GREENREDSYM)),
            'ndp_graph_templatized_LR': (Templatized, 
                dict(direction='LR', style=STYLE_GREENREDSYM, labeled=False)), 
            'ndp_graph_templatized_TB': (Templatized, 
                dict(direction='TB', style=STYLE_GREENREDSYM, labeled=False)),
            'ndp_graph_templatized_labeled_LR': (Templatized, 
                dict(direction='LR', style=STYLE_GREENREDSYM, labeled=True)), 
            'ndp_graph_templatized_labeled_TB': (Templatized, 
                dict(direction='TB', style=STYLE_GREENREDSYM, labeled=True)),
            'ndp_graph_normal_LR': (Normal, 
                dict(direction='LR', style=STYLE_GREENREDSYM)), 
            'ndp_graph_normal_TB': (Normal, 
                dict(direction='TB', style=STYLE_GREENREDSYM)),
            
            'ndp_repr_long': (NDP_repr_long, dict()),
        }
        
        # now add the ones from DP
        from .figures_dp import MakeFiguresDP
        mfdp = MakeFiguresDP(None)
        for alias, x in  mfdp.aliases.items():
            if alias in aliases:
                raise ValueError(alias)
            aliases[alias] = x
        for which, (constructor, params) in mfdp.figure2function.items():
            if which in figure2function:
                raise ValueError(which)
            
            params2 = dict(params)
            params2['constructor'] = constructor
            figure2function[which] = (BridgeFormatter, params2)
            BridgeFormatter(**params2)
        
        MakeFigures.__init__(self, aliases=aliases, figure2function=figure2function)
    
    def get_image_source(self):
        return self.image_source
    
    def get_ndp(self):
        return self.ndp
    
    def get_yourname(self):
        return self.yourname

class BridgeFormatter(MakeFigures_Formatter):
    def __init__(self, constructor, **kwargs):
        try:    
            self.dpf = constructor(**kwargs)
        except TypeError as e:
            msg = 'Could not instance %s with params %s' %\
                (constructor, kwargs)
            raise_wrapped(TypeError, e, msg)
            
    def available_formats(self):
        return self.dpf.available_formats()
    
    def get(self, mf, formats):
        ndp = mf.get_ndp()
        dp = ndp.get_dp()
        from .figures_dp import MakeFiguresDP
        mf2 = MakeFiguresDP(dp=dp)
        
        return self.dpf.get(mf2, formats)
    
class NDP_repr_long(TextFormatter):
    
    def get_text(self, mf):
        ndp = mf.get_ndp()
        return ndp.repr_long()
    

class Normal(GGFormatter):
    """ This is not enclosed """
    def __init__(self, direction, style):
        self.direction = direction
        self.style = style
        
    def get_gg(self, mf):
        ndp = mf.get_ndp()
        image_source = mf.get_image_source()
        yourname = mf.get_yourname()
        
        gg = gvgen_from_ndp(ndp=ndp, style=self.style, image_source=image_source,
                            yourname=yourname, direction=self.direction,
                            skip_initial=True)
        return gg
    
    
def templatize_children_for_figures(ndp, enclosed):
    from mocdp.comp.composite import CompositeNamedDP
    from mocdp.ndp.named_coproduct import NamedDPCoproduct
    from mocdp.comp.composite_templatize import cndp_templatize_children
    from mocdp.comp.composite_templatize import ndpcoproduct_templatize
    

    if isinstance(ndp, CompositeNamedDP):
        ndp2 = cndp_templatize_children(ndp)
        # print('setting _hack_force_enclose %r' % enclosed)
        if enclosed:
            setattr(ndp2, '_hack_force_enclose', True)
    elif isinstance(ndp, NamedDPCoproduct):
        ndp2 = ndpcoproduct_templatize(ndp)
    else:
        ndp2 = ndp
    return ndp2

class Enclosed(GGFormatter):
    def __init__(self, direction, enclosed, style, skip_initial=True):
        self.direction = direction
        self.enclosed = enclosed
        self.style = style
        self.skip_initial = skip_initial
         
    def get_gg(self, mf):

        ndp = mf.get_ndp()
        
        ndp2 = templatize_children_for_figures(ndp, enclosed=self.enclosed)
         
        image_source = mf.get_image_source()
        # we actually don't want the name on top
        yourname = None  # name
        
        gg = gvgen_from_ndp(ndp2, style=self.style, direction=self.direction,
                            image_source=image_source, yourname=yourname,
                            skip_initial=self.skip_initial)
        
        return gg

        
class Templatized(GGFormatter):
    def __init__(self, direction, style, labeled):
        self.direction = direction
        self.style = style
        self.labeled = labeled
         
    def get_gg(self, mf):
        ndp = mf.get_ndp()
        image_source = mf.get_image_source()
        
        yourname = None 
        if self.labeled:
            if hasattr(ndp, MCDPConstants.ATTR_LOAD_NAME):
                yourname = getattr(ndp,MCDPConstants.ATTR_LOAD_NAME)

        from mocdp.comp.composite_templatize import ndp_templatize
        ndp = ndp_templatize(ndp, mark_as_template=False) 
    
        gg = gvgen_from_ndp(ndp=ndp, style=self.style, yourname=yourname,
                            image_source=image_source, direction=self.direction,
                            skip_initial=True)
        return gg

class Expand(GGFormatter):

    def __init__(self, direction, style):
        self.direction = direction
        self.style = style

    def get_gg(self, mf):
        """ This expands the children, forces the enclosure """
        image_source = mf.get_image_source()
        ndp = mf.get_ndp()
        yourname = None  # name
        gg = gvgen_from_ndp(ndp, style=self.style,   direction=self.direction,
                            image_source=image_source, yourname=yourname,
                            skip_initial=True)
        return gg
    
    