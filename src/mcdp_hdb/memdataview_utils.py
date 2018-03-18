from mcdp_utils_misc import memoize_simple



def special_string_interpret(s, prefix):
    ''' s = 'user:${path[-1]}' 
        prefix = (a, b, c)
        returns 'user:a'
    '''
#     n = len(prefix)
    for i in range(-5, 0):
        pattern = '${path[%d]}'% i
        if pattern in s:
            sub = prefix[i]
            s = s.replace(pattern, sub)
    
    if '$' in s:
        msg = 'Could not find special expression for %r' % s
        raise ValueError(msg)
    return s
            

@memoize_simple
def host_name():
    import socket
    if socket.gethostname().find('.')>=0:
        name=socket.gethostname()
    else:
        gh = socket.gethostname()
        print('gh: %s' % gh)
        try:
            name = socket.gethostbyaddr(gh)[0]
        except IOError as e:
            if e.errno == 8:
                return gh
            raise
    return name

