import sys
from collections import OrderedDict
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType

try:
    from yaml import load, dump
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
if sys.version_info[0] != 2 or sys.version_info[1] >= 7:
    def construct_yaml_unistr(self, node):
        return self.construct_scalar(node)

    Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_unistr)

class AplusBisC(pTypes.GroupParameter):
    def __init__(self, **opts):
        opts['type'] = 'bool'
        opts['value'] = True
        pTypes.GroupParameter.__init__(self, **opts)

        self.addChild({'name': 'First Target Index', 'type': 'int', 'value': 0, 'limits': [0, 50]})
        self.addChild({'name': 'Plot Target Count', 'type': 'int', 'value': 51, 'limits': [1, 51]})
        self.addChild({'name': 'Last Target Index', 'type': 'int', 'value': 50, 'limits': [0, 50], 'readonly': True})
        self.a = self.param('First Target Index')
        self.b = self.param('Plot Target Count')
        self.c = self.param('Last Target Index')
        self.a.sigValueChanged.connect(self.aChanged)
        self.b.sigValueChanged.connect(self.bChanged)

    def aChanged(self):
        newc = self.a.value()+self.b.value()-1
        if newc>50:
            self.b.setValue(50-self.a.value()+1)
        else:
            self.c.setValue(self.a.value()+self.b.value()-1)

    def bChanged(self):
        newc = self.a.value()+self.b.value( )-1
        if newc>50:
            self.a.setValue(50-self.b.value()+1)
        else:
            self.c.setValue(self.a.value()+self.b.value()-1)

def loadParamsFromYaml(yaml_data, param_node_dict, path_str, **kwargs):
    param_list = []
    if param_node_dict is None:
        param_node_dict = OrderedDict()
    # yaml_data can be a string, which will be treated as a file path to
    # read from, or a dict, in which case it is processed.
    if isinstance(yaml_data,basestring):
        param_config = load(file(yaml_data, 'r'), Loader=Loader)
    else:
        param_config = yaml_data

    def nodeAttributeStringToObject(node_attr_str):
        if isinstance(node_attr_str, basestring) and node_attr_str[0] == '^' and node_attr_str[-1] == '^':
            node_attr_str = node_attr_str[1:-1]
            node_attr_var = kwargs.get(node_attr_str)
            if node_attr_var is None:
                node_attr_var = locals().get(node_attr_str)
            if node_attr_var is None:
                node_attr_var = globals().get(node_attr_str)

            if node_attr_var is not None:
                return node_attr_var
            else:
                raise ValueError("Error Creating Parameter tree. Unknown node %s:"%(node_attr_str))

        return node_attr_str

    org_path_str=path_str
    for node_label, node_contents in param_config.items():
        path_str=org_path_str
        # track the full path name of the node
        # this is what pygraphqt uses to ref a param.
        if isinstance(node_contents,(dict,OrderedDict)):
            node_name = node_contents.get('name')
            node_children = node_contents.get('children',"NOT_DEFINED")
            node_type = node_contents.get('type')
            if node_name:
                if path_str:
                    path_str = path_str+"."+node_name
                else:
                    path_str = node_name

                if node_children == "NOT_DEFINED":
                    param_class = globals().get(node_type)
                    if param_class:
                        #print 'node_contents1:',node_contents
                        del node_contents['type']
                        #print "param_class",param_class
                        #print 'node_contents2:',node_contents
                        object_param = param_class(**node_contents)
                        #print 'object_param:',object_param
                        param_list.append(object_param)
                        param_node_dict[node_label] = path_str
                    else:
                        node_value = node_contents.get('value')
                        if node_value:
                            node_contents['value'] = nodeAttributeStringToObject(node_value)

                        node_value = node_contents.get('values')
                        if node_value:
                            node_contents['values'] = nodeAttributeStringToObject(node_value)

                        node_value = node_contents.get('limits')
                        if node_value:
                            node_contents['limits'] = nodeAttributeStringToObject(node_value)

                        param_list.append(node_contents)
                        param_node_dict[node_label] = path_str
                elif node_children is None:
                    node_contents['children']=[]
                    param_list.append(node_contents)
                else:
                    if node_type == 'group':
                        sub_param_list, param_node_dict = loadParamsFromYaml(node_children, param_node_dict, path_str, **kwargs)
                        node_contents['children'] = sub_param_list
                        param_list.append(node_contents)
                    else:
                        param_class = globals().get(node_type)
                        if param_class:
                            #print 'node_contents1:',node_contents
                            del node_contents['type']
                            #print "param_class",param_class
                            #print 'node_contents2:',node_contents
                            object_param = param_class(**node_contents)
                            #print 'object_param:',object_param
                            param_list.append(object_param)
                            param_node_dict[node_label] = path_str
                        else:
                            raise ValueError("Error Creating Parameter tree. Unknown node type:",node_type,node_contents)
    return param_list, param_node_dict

def printParamDict(p):
    param_node_dict = p._param_node_dict
    print 'PARAM_DICT:'
    for param_label, param_path in  param_node_dict.items():
        print param_label," :: ", param_path

def createPlotParamTree(session_ids, selected_session_id, trial_ids, selected_trial_ids):
    ## Create tree of Parameter objects
    trial_id_range=[trial_ids[0], trial_ids[-1]]
    starting_trial_id = selected_trial_ids[0]
    trial_visibility_count = (selected_trial_ids[1]-selected_trial_ids[0])+1
    possible_count_range = [1,trial_visibility_count-trial_ids[-1]]
    param_list, param_node_dict = loadParamsFromYaml(r'.\plot_param_tree.yaml', None, None,
                                                     session_ids=session_ids,
                                                     selected_session_id=selected_session_id,
                                                     trial_ids=trial_id_range,
                                                     starting_trial_id = starting_trial_id,
                                                     trial_visibility_count = trial_visibility_count,
                                                     possible_count_range = possible_count_range
                                                     )

    p = Parameter.create(name='plot_settings', type='group', children=param_list)

    for k,v in param_node_dict.items():
        param_node_dict[v]=k
    p._param_node_dict = param_node_dict

    p._plotParamChangeHandlers = dict()
    def addParamChangeHandler(param_label, change_type, callback_func):
        p._plotParamChangeHandlers.setdefault("%s:%s"%(param_label, change_type),[]).append(callback_func)
    p.addParamChangeHandler = addParamChangeHandler

    ## If anything changes in the tree, print a message
    def change(param, changes):
        #print("setting changes:")
        for param, change, data in changes:
            path = p.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
            #print('  parameter: %s'% childName)
            #print('  change:    %s'% change)
            #print('  data:      %s'% str(data))
            #print('  ----------')
            param_handle = p._param_node_dict.get(childName)
            #print 'param_handle:',param_handle
            if param_handle:
                handlerKeyStr = "%s:%s"%(param_handle, change)
                #print 'handlerKeyStr: ',handlerKeyStr
                changeHandlers=p._plotParamChangeHandlers.get(handlerKeyStr)
                if changeHandlers:
                    for handler in changeHandlers:
                        #print 'calling:',handler, (childName, change, param, data)
                        handler(param_handle, childName, change, param, data)

    p.sigTreeStateChanged.connect(change)

    t = ParameterTree()
    t.setParameters(p, showTop=False)
    return t, p
