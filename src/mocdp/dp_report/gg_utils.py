""" Utils for graphgen """

import os
from system_cmd.meat import system_cmd_result
import networkx as nx  # @UnresolvedImport
from reprep.constants import MIME_PNG, MIME_PDF
from copy import deepcopy
import traceback
from contextlib import contextmanager


def graphviz_run(filename_dot, output, prog='dot'):
    suff = os.path.splitext(output)[1][1:]
    if not suff in ['png', 'pdf', 'ps']:
        raise ValueError((output, suff))

    cmd = [prog, '-T%s' % suff, '-o', output, filename_dot]
    system_cmd_result(cwd='.', cmd=cmd,
                 display_stdout=False,
                 display_stderr=False,
                 raise_on_error=True)

def gg_deepcopy(ggraph):
    try:
        return deepcopy(ggraph)
    except Exception as e:
        print traceback.format_exc(e)
        import warnings
        warnings.warn('Deep copy of gvgen graph failed: happens when in IPython.')
        return ggraph


def graphvizgen_plot(ggraph, output, prog='dot'):
    gg = gg_deepcopy(ggraph)
    with tmpfile(".dot") as filename_dot:
        with open(filename_dot, 'w') as f:
            gg.dot(f)
        try:
            graphviz_run(filename_dot, output, prog=prog)
        except:
            contents = open(filename_dot).read()
            import hashlib
            m = hashlib.md5()
            m.update(contents)
            s = m.hexdigest()
            filename = 'out-%s.dot' % s
            with open(filename, 'w') as f:
                f.write(contents)
            print('Saved problematic dot as %r.' % filename)
            raise

def nx_generic_graphviz_plot(G, output, prog='dot'):
    """ Converts to dot and writes on the file output """
    with tmpfile(".dot") as filename_dot:
        nx.write_dot(G, filename_dot)
        graphviz_run(filename_dot, output, prog=prog)


def gg_figure(r, name, ggraph):
    """ Adds a figure to the Report r that displays this graph
        and also its source. """
    f = r.figure(name, cols=1)

    # save file in dot file
    with tmpfile(".dot") as filename_dot:
        with open(filename_dot, 'w') as fo:
            ggraph.dot(fo)

        prog = 'dot'
        with f.data_file('graph', MIME_PNG) as filename:
            graphviz_run(filename_dot, filename, prog=prog)

        with r.data_file('graph_pdf', MIME_PDF) as filename:
            graphviz_run(filename_dot, filename, prog=prog)

    return f


@contextmanager
def tmpfile(suffix):
    """ Yields the name of a temporary file """
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(suffix=suffix)
    yield temp_file.name
    temp_file.close()
