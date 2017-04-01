from contracts import contract
from contracts.utils import check_isinstance, indent, raise_wrapped
import yaml

from mcdp.logs import logger


class DataEvents(object):
    # For simple values: int, string, float, date
    leaf_set = 'leaf_set' # value_set <parent> <name> <value> 
    struct_set = 'struct_set' # struct_set <name> <struct-value>
    increment = 'increment' # increment <name> <value>
    list_append = 'list_append' # list_append <list> <value>
    list_delete = 'list_delete' # list_delete <list> <index> # by index
    list_remove = 'list_remove' # list_remove <list> <value> # by value
    set_add = 'set_add' # set_add <set> <value>
    set_remove = 'set_remove' # set_remove <set> <value>
    dict_setitem = 'dict_setitem' # dict_setitem <dict> <key> <value>
    dict_delitem = 'dict_delitem' # dict_delitem <dict> <key>
    dict_rename = 'dict_rename' # dict_rename <dict> <key> <key2>
    all_events = [leaf_set, struct_set, increment, list_append, 
                  list_delete, dict_setitem, dict_delitem, dict_rename]

@contract(name=tuple)
def get_view_node(view, name):
    v = view
    while len(name):
        v = v.child(name[0])
        name = name[1:]
    return v
 
    

def event_leaf_set(parent, name, value, **kwargs):
    arguments = dict(parent=parent, name=name, value=value)
    return event_make(event_name=DataEvents.leaf_set, arguments=arguments, **kwargs)

def event_leaf_set_interpret(view, parent, name, value):
    v = get_view_node(view, parent)
    from mcdp_hdb.dbview import ViewContext0

    check_isinstance(v, ViewContext0)
    vc = v.child(name)
    vc._schema.validate(value)
    vc.check_can_write()
    vc.set(value)

def event_struct_set(name, value, **kwargs):
    arguments = dict(name=name, value=value)
    return event_make(event_name=DataEvents.struct_set, arguments=arguments, **kwargs)

def event_struct_set_interpret(view, arguments):
    raise NotImplementedError()

def event_increment(name, value, **kwargs):
    arguments = dict(name=name, value=value)
    return event_make(event_name=DataEvents.increment, arguments=arguments, **kwargs)

def event_increment_interpret(view, arguments):
    raise NotImplementedError()

def event_set_add(name, value, **kwargs):
    arguments = dict(name=name, value=value)
    return event_make(event_name=DataEvents.set_add, arguments=arguments, **kwargs)

def event_set_add_interpret(view, arguments):
    raise NotImplementedError()

def event_set_remove(name, value, **kwargs):
    arguments = dict(name=name, value=value)
    return event_make(event_name=DataEvents.set_remove,  arguments=arguments, **kwargs)


def event_set_remove_interpret(view, arguments):
    raise NotImplementedError()

def event_list_append(name, value, **kwargs):
    arguments = dict(name=name, value=value)
    return event_make(event_name=DataEvents.list_append, arguments=arguments, **kwargs)


def event_list_append_interpret(view, arguments):
    raise NotImplementedError()

def event_list_delete(name, index, **kwargs):
    arguments = dict(name=name, index=index)
    return event_make(event_name=DataEvents.list_delete, arguments=arguments, **kwargs)

def event_list_delete_interpret(view, arguments):
    raise NotImplementedError()

def event_list_remove(name, value, **kwargs):
    arguments = dict(name=name, value=value)
    return event_make(event_name=DataEvents.list_delete, arguments=arguments, **kwargs)

def event_list_remove_interpret(view, arguments):
    raise NotImplementedError()

def event_dict_setitem(name, key, value, **kwargs):
    arguments = dict(name=name, key=key, value=value)
    e = event_make(event_name=DataEvents.dict_setitem,  arguments=arguments, **kwargs)
    
    print('dict_setitem: %s' % e)
    assert 'value' in e['arguments']
    return e

def event_dict_setitem_interpret(view, name, key, value):
    from mcdp_hdb.dbview import ViewHash0
    v = get_view_node(view, name)
    check_isinstance(v, ViewHash0)
    # permissions
    v.check_can_write()
    # validate
    v._schema.prototype.validate(value)
    v._data[key] = value
    
def event_dict_delitem(name, key, **kwargs):
    arguments = dict(name=name, key=key)
    return event_make(event_name=DataEvents.dict_delitem, arguments=arguments, **kwargs)

def event_dict_delitem_interpret(view, name, key):
    from mcdp_hdb.dbview import ViewHash0
    v = get_view_node(view, name)
    check_isinstance(v, ViewHash0)
    # permissions
    v.check_can_write()
    del v._data[key] 

def event_dict_rename(name, key, key2, **kwargs):
    arguments = dict(name=name, key=key, key2=key2)
    return event_make(event_name=DataEvents.dict_rename,  arguments=arguments, **kwargs)

def event_dict_rename_interpret(view, name, key, key2):
    from mcdp_hdb.dbview import ViewHash0
    v = get_view_node(view, name)
    check_isinstance(v, ViewHash0)
    # permissions
    v.check_can_write()
    v._data[key2] = v._data.pop(key)


def event_make(_id, event_name, who, arguments):
    assert event_name in DataEvents.all_events
    return {
     'operation': event_name, 
     'id': _id,
     'who': who, 
     'arguments': arguments,
    }
# 
def event_intepret(view_manager, db0, event):
    actor = event['who']['actor']
    principals = event['who']['principals']
    view = view_manager.view(db0, actor=actor, principals=principals)
    fs = {
        DataEvents.leaf_set: event_leaf_set_interpret,
        DataEvents.struct_set: event_struct_set_interpret,
        DataEvents.increment: event_increment_interpret,
        DataEvents.list_append: event_list_append_interpret,
        DataEvents.list_remove: event_list_remove_interpret,
        DataEvents.list_delete: event_list_delete_interpret,
        DataEvents.set_add: event_set_add_interpret,
        DataEvents.set_remove: event_set_remove_interpret,
        DataEvents.dict_setitem: event_dict_setitem_interpret,
        DataEvents.dict_delitem: event_dict_delitem_interpret,
        DataEvents.dict_rename: event_dict_rename_interpret,
    }
    ename = event['operation']
    intf = fs[ename]
    arguments = event['arguments']
    try:
        logger.info('Arguments: %s' % arguments)
        intf(view=view, **arguments)
    except Exception as e:
        msg = 'Could not complete the replay of this event: \n'
        msg += indent(yaml.dump(event), 'event: ')
        from mcdp_hdb.dbview import InvalidOperation
        raise_wrapped(InvalidOperation, e, msg)
    view._schema.validate(db0)

        
def replay_events(view_manager, db0, events):
    for event in events:
        event_intepret(view_manager, db0, event)
        msg = '\nAfter playing event:\n'
        msg += indent(yaml.dump(event), '   event: ')
        msg += '\nthe DB is:\n'
        msg += indent(yaml.dump(db0), '   db: ')
        logger.debug(msg)
    return db0
#     from mcdp_hdb.dbview import ViewHash0

#     
#     def get(v00, w):
#         v = v00
#         while len(w):
#             v = v.child(w[0])
#             w = w[1:]
#         return v
    
#         
#         actor = event['who']['actor']
#         principals = event['who']['principals']
#         v0 = view_manager.view(db0, actor=actor, principals=principals)
#         
#         try:
#             args = event['arguments']
#             if event['operation'] == 'set':
#                 what = tuple(args['what'])
#                 value = args['value']
#                 if len(what) > 1: # maybe >= 1
#                     prev = get(v0, what[:-1])
#                     if isinstance(prev, ViewHash0):
#                         key = what[-1]
#                         prev[key] = value
#                     else:
#                         v = get(v0, what)
#                         v.set(value)
#                 else:
#                     v = get(v0, what)
#                     v._schema.validate(value)
#                     v.set(value)
#             elif event['operation'] == 'delete':
#                 what = tuple(args['what'])
#                 assert len(what) >= 1
#                 
#                 prev = get(v0, what[:-1])
#                 if isinstance(prev, ViewHash0):
#                     key = what[-1]
#                     del prev[key]
#                 else:
#                     msg = 'Not implemented with %s' % prev
#                     raise InvalidOperation(msg)
#             elif event['operation'] == 'rename':
#                 what = tuple(args['what'])
#                 assert len(what) >= 1
#                 
#                 prev = get(v0, what[:-1])
#                 if isinstance(prev, ViewHash0):
#                     key = what[-1]
#                     key2 = args['value']
#                     prev.rename(key, key2)
#                 else:
#                     msg = 'Not implemented with %s' % prev
#                     raise InvalidOperation(msg)
#             else:
#                 raise InvalidOperation(event['operation'])
#         except Exception as e:
#             msg = 'Could not complete the replay of this event: \n'
#             msg += indent(yaml.dump(event), 'event: ')
#             raise_wrapped(InvalidOperation, e, msg)
#             
        
        
#     
# def event_set(_id, who, what, value):
#     event = {
#      'operation': 'set', 
#      'id': _id,
#      'who': who, 
#      'arguments': {
#          'what': list(what), 
#          'value': value,
#         }
#     }
#     return event
# 
# def event_delete(_id, who, what):
#     event = {
#      'operation': 'delete', 
#      'id': _id,
#      'who': who, 
#      'arguments': {
#          'what': list(what),
#         }
#     }
#     return event
# 
# def event_rename(_id, who, what, key2):
#     event = {
#      'operation': 'rename', 
#      'id': _id,
#      'who': who, 
#      'arguments': {
#          'what': list(what),
#          'value': key2,
#         }
#     }
#     return event
