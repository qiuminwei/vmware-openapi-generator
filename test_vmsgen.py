import vmsgen
import unittest
from unittest import mock as mock

class TestVmsGen(unittest.TestCase):

    def test_tags_from_service_name(self):

        # case 1: tags generation from short name
        expected = ['']
        vmsgen.TAG_SEPARATOR = ''
        actual = vmsgen.tags_from_service_name('three.levels.deep')
        self.assertEqual(expected, actual)

        # case 2: test tags generation from proper name
        expected = ['levels_deep']
        vmsgen.TAG_SEPARATOR = '_'
        actual = vmsgen.tags_from_service_name('more.than.three.levels.deep')
        self.assertEqual(expected, actual)

    def test_get_input_params(self):

        # case 1.1: SSL is secure
        test_args = ['vmsgen', '-vc', 'v_url']
        ssl_verify_expected = True
        with mock.patch('sys.argv', test_args):
            _, _, _, ssl_verify_actual = vmsgen.get_input_params()
        self.assertEqual(ssl_verify_expected, ssl_verify_actual)

        # case 1.2: SSL is insecure
        test_args = ['vmsgen', '-vc', 'v_url', '-k']
        ssl_verify_expected = False
        with mock.patch('sys.argv', test_args):
            _, _, _, ssl_verify_actual = vmsgen.get_input_params()
        self.assertEqual(ssl_verify_expected, ssl_verify_actual)

        # case 2.1: tag separator option (default)
        test_args = ['vmsgen', '-vc', 'v_url', '-k']
        tag_separator_expected = '/'
        with mock.patch('sys.argv', test_args):
            vmsgen.get_input_params()
        self.assertEqual(tag_separator_expected, vmsgen.TAG_SEPARATOR)

        # case 2.2: tag separator option
        expected = '_'
        test_args = ['vmsgen', '-vc', 'v_url', '-s', expected]
        with mock.patch('sys.argv', test_args):
            vmsgen.get_input_params()
        self.assertEqual(expected, vmsgen.TAG_SEPARATOR)

        # case 3.1: operation id option is FALSE
        test_args = ['vmsgen', '-vc', 'v_url', '-k']
        generate_op_id_expected = False
        with mock.patch('sys.argv', test_args):
            vmsgen.get_input_params()
        self.assertEqual(generate_op_id_expected, vmsgen.GENERATE_UNIQUE_OP_IDS)

        # case 3.1: operation id option is TRUE
        generate_op_id_expected = True
        test_args = ['vmsgen', '-vc', 'v_url', '-k', '-uo']
        with mock.patch('sys.argv', test_args):
            vmsgen.get_input_params()
        self.assertEqual(generate_op_id_expected, vmsgen.GENERATE_UNIQUE_OP_IDS)

    def test_post_process_path(self):
        '''
            Test cases to check if post process path which adds vmware-use-header-authn as a nessecary header params
        '''
        # case 1: case where hardcoded header should be added
        path_obj = {'path':'/com/vmware/cis/session', 'method':'post', "operationId":"create"}
        header_parameter = {'in': 'header', 'required': True, 'type': 'string',
                            'name': 'vmware-use-header-authn',
                            'description': 'Custom header to protect against CSRF attacks in browser based clients'}
        path_obj_expected  = {'path':'/com/vmware/cis/session', 'method':'post', "operationId":"create", 'parameters':[header_parameter]}
        vmsgen.post_process_path(path_obj)
        self.assertEqual(path_obj_expected, path_obj)

        # case 2.1: case where hardcoded header should be shouldn't be added based on path
        path_obj = {'path':'mock/path', 'method':'post', "operationId":"mock"}
        path_obj_expected  = {'path':'mock/path', 'method':'post', "operationId":"mock"}
        vmsgen.post_process_path(path_obj)
        self.assertEqual(path_obj_expected, path_obj)

        # case 2.2: case where hardcoded header should be shouldn't be added based on method
        path_obj = {'path':'/com/vmware/cis/session', 'method':'get', "operationId":"get"}
        path_obj_expected  = {'path':'/com/vmware/cis/session', 'method':'get', "operationId":"get"}
        vmsgen.post_process_path(path_obj)
        self.assertEqual(path_obj_expected, path_obj)

        # case 3: adding the vmw-task=true parameter to path when operationId end with $task
        path_obj = {'path':'mock/path', 'method':'get', "operationId":"mock$task"}
        path_obj_expected  = {'path':'mock/path?vmw-task=true', 'method':'get', "operationId":"mock$task"}
        vmsgen.post_process_path(path_obj)
        self.assertEqual(path_obj_expected, path_obj)

    def test_get_response_object_name(self):
        '''
           test case for response type name to be used based on method is get or not
        '''
        # case 1:
        operation_id = 'get'
        service_id = 'tag'
        type_name = 'tag'
        type_name_expected = vmsgen.get_response_object_name(service_id, operation_id)
        self.assertEqual(type_name, type_name_expected)

        # case 2:
        operation_id = 'post'
        service_id = 'tag'
        type_name = 'tag.post'
        type_name_expected = vmsgen.get_response_object_name(service_id, operation_id)
        self.assertEqual(type_name, type_name_expected)

    def test_is_type_builtin(self):
        '''
        '''
        typeset_cases          = ['binary', 'boolean', 'datetime', 'double', 'dynamicstructure', 'exception', 'id', 'long', 'opaque', 'secret', 'string', 'uri']

        typeset_cases_out_expected = [True]*len(typeset_cases)
        typeset_cases_out_actual   = []

        for val in typeset_cases:
            typeset_cases_out_actual.append(vmsgen.is_type_builtin(val))

        self.assertEqual(typeset_cases_out_actual, typeset_cases_out_expected)

    def test_metamodel_to_swagger_type_converter(self):

        input_type_cases        = ['date_time', 'secret', 'any_error', 'dynamic_structure', 'uri', 'id', 'long', 'double', 'binary', 'notValidType']

        input_type_out_expected = [('string','date-time'), ('string', 'password'), ('string', None), ('object', None), ('string', 'uri'), ('string', None), ('integer', 'int64'), ('number', 'double'), ('string', 'binary'), ('notvalidtype', None)]
        input_type_out_actual   = []

        for val in input_type_cases:
            input_type_out_actual.append(vmsgen.metamodel_to_swagger_type_converter(val))

        self.assertEqual(input_type_out_actual, input_type_out_expected)

    def test_visit_builtin(self):

        builtin_type = 'BOOLEAN'
        new_prop     = {}
        expected     = {'type':'boolean'}
        vmsgen.visit_builtin(builtin_type, new_prop)
        self.assertEqual(new_prop, expected)

        builtin_type = 'date_time'
        new_prop     = {}
        expected     = {'type':'string', 'format':'date-time'}
        vmsgen.visit_builtin(builtin_type, new_prop)
        self.assertEqual(new_prop, expected)

        builtin_type = 'dynamic_structure'
        new_prop     = {}
        expected     = {'type':'object'}
        vmsgen.visit_builtin(builtin_type, new_prop)
        self.assertEqual(new_prop, expected)

        builtin_type = 'long'
        new_prop     = {'type':'array'}
        expected     = {'items': {'format': 'int64', 'type': 'integer'}, 'type': 'array'}
        vmsgen.visit_builtin(builtin_type, new_prop)
        self.assertEqual(new_prop, expected)



    def test_build_path(self):

        # function def : build_path(service_name, method, path, documentation, parameters, operation_id, responses, consumes, produces)

        # case 1: generic mock example
        expected = {
            'tags': ['mock_tag'],
            'method': 'get',
            'path': '/com/vmware/mock_package/mock_tag',
            'summary': 'mock documentation',
            'responses': 'mock responses',
            'consumes': 'mock consumes',
            'produces': 'mock produces',
            'operationId': 'mock id',
            'parameters': [{'mock params':'params 1'}]
        }
        actual = vmsgen.build_path('com.vmware.mock_package.mock_tag', 'get', '/com/vmware/mock_package/mock_tag', 'mock documentation', [{'mock params':'params 1'}], 'mock id', 'mock responses','mock consumes', 'mock produces')
        self.assertEqual(actual, expected)

        # case 2 related specifically to '/com/vmware/cis/session'
        # case 2.1: case where hardcoded header should be added
        expected = {
            'tags': ['session'],
            'method': 'post',
            'path': '/com/vmware/cis/session',
            'summary': 'mock documentation',
            'responses': 'mock responses',
            'consumes': 'mock consumes',
            'produces': 'mock produces',
            'operationId': 'mock id',
            'security': [{'basic_auth': []}],
            'parameters': [
                {
                    'in': 'header',
                    'required': True,
                    'type': 'string',
                    'name': 'vmware-use-header-authn',
                    'description': 'Custom header to protect against CSRF attacks in browser based clients'
                }
            ]
        }
        actual = vmsgen.build_path('com.vmware.cis.session', 'post', '/com/vmware/cis/session', 'mock documentation', None, 'mock id', 'mock responses','mock consumes', 'mock produces')
        self.assertEqual(actual, expected)
        
        # case 2.2: case where hardcoded header shouldn't be added shown here only based on method but same can be done for path
        expected = {
            'tags': ['session'], 
            'method': 'get', 
            'path': '/com/vmware/cis/session', 
            'summary': 'mock documentation', 
            'responses': 'mock responses', 
            'consumes': 'mock consumes', 
            'produces': 'mock produces', 
            'operationId': 'mock id', 
            'parameters': [{'mock params':'params 1'}]
        }
        actual = vmsgen.build_path('com.vmware.cis.session', 'get', '/com/vmware/cis/session', 'mock documentation', [{'mock params':'params 1'}], 'mock id', 'mock responses','mock consumes', 'mock produces')
        self.assertEqual(actual, expected)


    def test_cleanup(self):

        # case 1: [path dict] -> delete path and method mentioned inside path_dict value because key is the path and value of path_dict's key is method, hence remove the redundant data.
        path_dict = {
            'mock_path':{
                'mock_method_1':{
                    'mock_attr': 'value',
                    'method': 'mock_method_1', 
                    'path': 'mock_path'
                    },
                'mock_method_2':{
                    'mock_attr': 'value',
                    'method': 'mock_method_2', 
                    'path': 'mock_path'
                    }  
                }
            }

        path_dict_expected = {
            'mock_path':{
                'mock_method_1':{
                    'mock_attr': 'value',
                    },
                'mock_method_2':{
                    'mock_attr': 'value',
                    }  
                }
            }

        type_dict = {}

        vmsgen.cleanup(path_dict, type_dict)
        self.assertEqual(path_dict, path_dict_expected)

        # case 2: [type dict] -> delete attribute named 'required' present in any property of any model's structure type 
        path_dict = {}
        type_dict = {
            'mock.type':{
                'properties':{
                    'mock property 1':{
                        'required': True
                    },
                    'mock property 2':{
                    }
                }
            }
        }
        type_dict_expected = {
            'mock.type':{
                'properties':{
                    'mock property 1':{
                    },
                    'mock property 2':{ 
                    }
                }
            }
        }
        vmsgen.cleanup(path_dict, type_dict)
        self.assertEqual(type_dict, type_dict_expected)

    def test_remove_query_params(self):

        # case 1: Absolute Duplicate paths, which will remain unchanged
        path_dict = {
            'mock/path1?action=mock_action':{
                'post':{
                    'parameters' : [] # parameters attr is always created even if there isn't any
                }
            },
            'mock/path1':{
                'post':{
                }
            }
        }

        path_dict_expected = {
            'mock/path1?action=mock_action':{
                'post':{
                    'parameters' : []
                }
            },
            'mock/path1':{
                'post':{
                }
            }
        }
        vmsgen.remove_query_params(path_dict)
        self.assertEqual(path_dict, path_dict_expected)


        # case 2: Partial Duplicate, adding the Operations of the new duplicate path to that of the existing path based on method type
        # case 2.1: only one of them as query parameter
        path_dict = {
            'mock/path1?action=mock_action':{
                'post':{
                    'parameters' : []
                }
            },
            'mock/path1':{
                'get':{
                    'parameters' : []
                }
            }
        }
        path_dict_expected = {
            'mock/path1': {
                'post': {
                    'parameters': [
                        {
                            'name': 'action', 
                            'in': 'query', 
                            'description':'action=mock_action', 
                            'required': True, 
                            'type': 'string', 
                            'enum': ['mock_action']
                        }
                    ]
                }, 
                'get': {
                    'parameters' : []
                }
            }
        }
        vmsgen.remove_query_params(path_dict)
        self.assertEqual(path_dict, path_dict_expected)

        # case 2.2: both of them has query parameter
        path_dict = {
            'mock/path1?action=mock_action_1':{
                'post':{
                    'parameters' : []
                }
            },
            'mock/path1?action=mock_action_2':{
                'get':{
                    'parameters' : []
                }
            }
        }
        path_dict_expected = {
            'mock/path1': {
                'post': {
                    'parameters': [{'name': 'action',  'in': 'query', 'description': 'action=mock_action_1', 'required': True, 'type': 'string', 'enum': ['mock_action_1']}]
                }, 
                'get': {
                    'parameters': [{'name': 'action',  'in': 'query', 'description': 'action=mock_action_2', 'required': True, 'type': 'string', 'enum': ['mock_action_2']}]
                }
            }
        }
        vmsgen.remove_query_params(path_dict)
        self.assertEqual(path_dict, path_dict_expected)

        # case 3: QueryParameters are fixed
        # case 3.1 : method types are different
        path_dict = {
            'mock/path1?action=mock_action_1':{
                'post':{
                    'parameters' : []
                }
            },
            'mock/path1?action=mock_action_2':{
                'get':{
                    'parameters' : []
                }
            }
        }

        path_dict_expected = {
            'mock/path1': {
                'get': {
                    'parameters': [{'name': 'action', 'in': 'query', 'description': 'action=mock_action_2', 'required': True, 'type': 'string', 'enum': ['mock_action_2']}]
                }, 
                'post': {
                    'parameters': [{'name': 'action', 'in': 'query', 'description': 'action=mock_action_1', 'required': True, 'type': 'string', 'enum': ['mock_action_1']}]
                }
            }
        }

        vmsgen.remove_query_params(path_dict)
        self.assertEqual(path_dict, path_dict_expected)

        # case 3.2 : method types are same
        path_dict = {
            'mock/path1?action=mock_action_1':{
                'post':{
                    'parameters' : []
                }
            },
            'mock/path1?action=mock_action_2':{
                'post':{
                    'parameters' : []
                }
            }
        }

        path_dict_expected = {
            'mock/path1': {
                'post': {
                    'parameters': [{'name': 'action', 'in': 'query', 'description': 'action=mock_action_1', 'required': True, 'type': 'string', 'enum': ['mock_action_1']}]
                }
            },
            'mock/path1?action=mock_action_2': {
                'post': {
                    'parameters': []
                }
            }
        }
        vmsgen.remove_query_params(path_dict)
        self.assertEqual(path_dict, path_dict_expected)

    def test_remove_com_vmware_from_dict(self):

        # case 1 (path dict processing): removing com.vmware. from every key-value pair which contains it and $ from every ref value of definition
        # case 1.1: remove com.vmware from value of when key is either of ('$ref', 'summary', 'description')
        # case 1.2: removing $ sign from ref value's, example: { "$ref" : "#/definitions/vcenter.vcha.cluster.failover$task_result" }
        # case 1.3: removing attr required when it is with '$ref'
        
        path_dict = {
            'com/vmware/mock/path':{
                'get': {
                    'tags': ['mock'], 
                    'summary': 'com.vmware.mock',  # 1.1:  example 1
                    'parameters': [
                        {
                            "in" : "path",
                            "description" : "com.vmware.somemockparam description" # # 1.1: example 2
                        },
                        {
                            "$ref": '#/parameters/com.vmware.somemockparam' # 1.1 : example 3
                        }
                    ], 
                    'responses': {
                        'mock 200': {
                            'description': 'description about com.vmware.mock_response',
                            'schema': {
                                '$ref': '#/definitions/com.vmware.mock_response$result', # 1.2
                                'required': False # 1.3
                            }
                        }
                    },
                    'operationId': 'get'
                }
            }
        }

        path_dict_expected = {
            'com/vmware/mock/path': {
                'get': {
                    'tags': ['mock'], 
                    'summary': 'mock', 
                    'parameters': [
                        {
                            'in': 'path', 
                            'description': 'somemockparam description'
                        }, 
                        {
                            '$ref': '#/parameters/somemockparam'
                        }
                    ],
                    'responses': {
                        'mock 200': {
                            'description': 'description about mock_response', 
                            'schema': {
                                '$ref': '#/definitions/mock_response_result'
                            }
                        }
                    },
                    'operationId': 'get'
                }
            }
        }

        vmsgen.remove_com_vmware_from_dict(path_dict)   
        self.assertEqual(path_dict, path_dict_expected)

        # case 2 (type dict processing)
        # case 2.1 : remove com.vmware and replace '$' from key's
        # case 2.2 : removing attr required when it is with '$ref'
        type_dict = { 
            'com.vmware.mock.mock_check$list' : { # 2.1 : example 1
                'type': 'object', 
                'properties': {
                    'value': {
                        'description': ' value desc.', 
                        'type': 'array', 
                        'items': {
                            '$ref': '#/definitions/com.vmware.mock_check_item', # 2.1 : example 2
                            'required': True # 2.2
                        }
                    },
                    'data': {
                        'description': ' data desc ', 
                        'type': 'object'
                    },
                    'required': ['value']
                }
            }
        }
        type_dict_expected = {
            'mock.mock_check_list': {
                'type': 'object', 
                'properties': {
                    'value': {
                        'description': 
                        ' value desc.', 
                        'type': 'array', 
                        'items': {
                            '$ref': '#/definitions/mock_check_item'
                        }
                    }, 
                    'data': {
                        'description': ' data desc ', 
                        'type': 'object'
                    }, 
                    'required': ['value']
                }
            }
        }
        vmsgen.remove_com_vmware_from_dict(type_dict)
        self.assertEqual(type_dict, type_dict_expected)

    def test_create_camelized_op_id(self):

        # case 1 - without query parameter: removes com/vmware/ and replaces '/' & '-' with '_' also converts the first letter of all the words except the first one from lower to upper before concatenating to form unique op id
        path = "com/vmware/mock-path"
        http_method = "post"
        operations_dict = {
            'operationId' : 'post'
        }
        op_id_expected = 'postMockPath'
        op_id_actual = vmsgen.create_camelized_op_id(path, http_method, operations_dict)
        self.assertEqual(op_id_actual, op_id_expected)

        # Case 2 - similar to case 1 with added query param to path
        path = "com/vmware/mock-path?action=value"
        http_method = "post"
        operations_dict = {
            'operationId' : 'post'
        }
        op_id_expected = 'postMockPath'
        op_id_actual = vmsgen.create_camelized_op_id(path, http_method, operations_dict)
        self.assertEqual(op_id_actual, op_id_expected)

        # Case 3 - similar to case 1 with path variable
        path = "com/vmware/mock-path/{mock}/test"
        http_method = "post"
        operations_dict = {
            'operationId' : 'post'
        }
        op_id_expected = 'postMockPathTest'
        op_id_actual = vmsgen.create_camelized_op_id(path, http_method, operations_dict)
        self.assertEqual(op_id_actual, op_id_expected)

        # Note: create_unique_op_ids(path_dict) test cases are handled in test cases provided for create_camelized_op_id

    def test_categorize_service_urls_by_package_names(self):

        # A simple mock example to show case the result
        base_url = "https://vcip/rest"
        service_urls_map = [
            "https://vcip/rest/com/vmware/package-mock-1/mock/",
            "https://vcip/rest/com/vmware/package-mock-1/mock-test/",
            "https://vcip/rest/com/vmware/package-mock-2/"
        ]
        path_dict_expected = {
            "package-mock-1" : [
                "https://vcip/rest/com/vmware/package-mock-1/mock/",
                "https://vcip/rest/com/vmware/package-mock-1/mock-test/"
            ],
            "package-mock-2" : ["https://vcip/rest/com/vmware/package-mock-2/"]
        }
        path_dict_actual = vmsgen.categorize_service_urls_by_package_names(service_urls_map, base_url) 
        self.assertEqual(path_dict_actual, path_dict_expected)

    def test_find_url(self):
        
        # case 1: if only one element is in the list return it
        list_of_links = [{'method': 'POST', 'href':'https://vcip/rest/com/vmware/mock?~action=value'}]
        ret_expected = ('https://vcip/rest/com/vmware/mock?~action=value','POST')
        ret_actual = vmsgen.find_url(list_of_links)

        self.assertEqual(ret_actual, ret_expected)


        # case 2: if multiple links are provided
        # case 2.1 : return a link which does not contain "~action"
        list_of_links = [
            {'method': 'POST', 'href':'https://vcip/rest/com/vmware/mock?~action=value'},
            {'method': 'POST', 'href':'https://vcip/rest/com/vmware/mock-action-value'}
        ]
        ret_expected = ('https://vcip/rest/com/vmware/mock-action-value','POST')
        ret_actual = vmsgen.find_url(list_of_links)

        self.assertEqual(ret_actual, ret_expected)


        # case 2.2 : all links have ~action in them then check if any of them has id: and return it.
        list_of_links = [
            {'method': 'POST', 'href':'https://vcip/rest/com/vmware/mock?~action=value'},
            {'method': 'POST', 'href':'https://vcip/rest/com/vmware/mock/id:{mock_id}?~action=value'}
        ]
        ret_expected = ('https://vcip/rest/com/vmware/mock/id:{mock_id}?~action=value','POST')
        ret_actual = vmsgen.find_url(list_of_links)

        self.assertEqual(ret_actual, ret_expected)


        # case 2.3 : all links have ~action in them and none of them have id:, pick any by default first one.
        list_of_links = [
            {'method': 'POST', 'href':'https://vcip/rest/com/vmware/mock?~action=value1'},
            {'method': 'POST', 'href':'https://vcip/rest/com/vmware/mock?~action=value2'}
        ]
        ret_expected = ('https://vcip/rest/com/vmware/mock?~action=value1','POST')
        ret_actual = vmsgen.find_url(list_of_links)
        self.assertEqual(ret_actual, ret_expected)
        
if __name__ == '__main__':
    unittest.main()
