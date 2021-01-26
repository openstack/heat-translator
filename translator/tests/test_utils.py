#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
from toscaparser.tests.base import TestCase
import translator.common.utils


class CommonUtilsTest(TestCase):

    MemoryUnit = translator.common.utils.MemoryUnit
    cmpUtils = translator.common.utils.CompareUtils
    yamlUtils = translator.common.utils.YamlUtils
    UrlUtils = translator.common.utils.UrlUtils

    def test_convert_unit_size_to_num(self):
        size = '1 TB'
        num_to_convert = 'GB'
        expected_output = 1000
        output = self.MemoryUnit.convert_unit_size_to_num(size, num_to_convert)
        self.assertEqual(output, expected_output)

        size = '40 GB'
        num_to_convert = 'MB'
        expected_output = 40000
        output = self.MemoryUnit.convert_unit_size_to_num(size, num_to_convert)
        self.assertEqual(output, expected_output)

        size = '20 B'
        num_to_convert = None
        expected_output = 20
        output = self.MemoryUnit.convert_unit_size_to_num(size, num_to_convert)
        self.assertEqual(output, expected_output)

    def test_validate_unit(self):
        unit = 'AB'
        exp_msg = ('Provided unit "{0}" is not valid. The valid units are '
                   '{1}').format(unit, self.MemoryUnit.UNIT_SIZE_DICT.keys())
        try:
            self.MemoryUnit.validate_unit(unit)
        except Exception as err:
            self.assertIsInstance(err, ValueError)
            self.assertEqual(exp_msg, err.__str__())

    def test_unit_size_conversion_to_GNU_standard(self):
        unit = 'gB'
        standard_unit = 'GB'
        converted_unit = self.MemoryUnit.validate_unit(unit)
        self.assertEqual(converted_unit, standard_unit)

        unit = 'KB'
        standard_unit = 'kB'
        converted_unit = self.MemoryUnit.validate_unit(unit)
        self.assertEqual(converted_unit, standard_unit)

        unit = 'kb'
        standard_unit = 'kB'
        converted_unit = self.MemoryUnit.validate_unit(unit)
        self.assertEqual(converted_unit, standard_unit)

        unit = 'kB'
        standard_unit = 'kB'
        converted_unit = self.MemoryUnit.validate_unit(unit)
        self.assertEqual(converted_unit, standard_unit)

        unit = 'MIB'
        standard_unit = 'MiB'
        converted_unit = self.MemoryUnit.validate_unit(unit)
        self.assertEqual(converted_unit, standard_unit)

    def test_str_to_num_value_error(self):
        str_to_convert = '55063.000000'
        expected_output = 55063.0
        output = translator.common.utils.str_to_num(str_to_convert)
        self.assertEqual(output, expected_output)

    def test_compare_dicts_unequal(self):
        dict1 = {'allowed_values': [1, 2, 4, 8],
                 'server3': {'depends_on': ['server1', 'server2']}}
        dict2 = {'allowed_values': [1, 2, 4, 8],
                 'server3': {'depends_on': ['server2', 'server1']}}
        self.assertFalse(self.cmpUtils.compare_dicts(dict1, dict2))

    def test_dicts_equivalent_empty_dicts(self):
        self.assertTrue(self.cmpUtils.compare_dicts(None, None))
        self.assertFalse(self.cmpUtils.compare_dicts(None, {}))
        self.assertFalse(self.cmpUtils.compare_dicts(None, {'x': '2'}))

    def test_compareutils_reorder(self):
        dic = {'output': {'website_url': {'value': {'get_attr':
                                                    ['server', 'networks',
                                                     'private', 0]}}},
               'allowed_values': [2, 8, 1, 4],
               'server3': {'depends_on': ['server2', 'server1']}}
        reordered_dic = {'output': {'website_url': {'value': {'get_attr':
                                                    ['server', 'networks',
                                                     'private', 0]}}},
                         'allowed_values': [1, 2, 4, 8],
                         'server3': {'depends_on': ['server1', 'server2']}}
        self.assertEqual(reordered_dic, self.cmpUtils.reorder(dic))

    def test_compareutils_diff_dicts_both_null(self):
        expected = None
        provided = None
        self.assertEqual({},
                         self.cmpUtils.diff_dicts(expected, provided))

    def test_compareutils_diff_dicts_one_null(self):
        expected = {'keyname': 'userkey'}
        provided = None
        self.assertEqual(
            {self.cmpUtils.MISMATCH_VALUE1_LABEL: {'keyname': 'userkey'},
             self.cmpUtils.MISMATCH_VALUE2_LABEL: None},
            self.cmpUtils.diff_dicts(expected, provided))

    def test_compareutils_diff_dicts_missing_key(self):
        expected = {'server3': {'depends_on': ['server1', 'server2'],
                                'keyname': 'userkey'}}
        provided = {'server3': {'depends_on': ['server2', 'server1']}}
        self.assertEqual(
            {'server3': {'keyname':
             {self.cmpUtils.MISMATCH_VALUE1_LABEL: 'userkey',
              self.cmpUtils.MISMATCH_VALUE2_LABEL: None}}},
            self.cmpUtils.diff_dicts(expected, provided))

    def test_compareutils_diff_dicts_missing_key_other_dict(self):
        expected = {'server3': {'depends_on': ['server1', 'server2']}}
        provided = {'server3': {'depends_on': ['server2', 'server1'],
                                'keyname': 'userkey'}}
        self.assertEqual(
            {'server3': {'keyname':
             {self.cmpUtils.MISMATCH_VALUE1_LABEL: None,
              self.cmpUtils.MISMATCH_VALUE2_LABEL: 'userkey'}}},
            self.cmpUtils.diff_dicts(expected, provided))

    def test_compareutils_diff_dicts_value_diff(self):
        expected = \
            {'output':
             {'website_url':
              {'value':
               {'get_attr': ['server', 'networks', 'private', 0]}}},
             'server3': {'depends_on': ['server2', 'server1']}}
        provided = \
            {'output':
             {'website_url':
              {'value':
               {'get_attr': ['server', 'networks', 'public', 0]}}},
             'server3': {'depends_on': ['server2', 'server1']}}
        self.assertEqual(
            {'output':
             {'website_url':
              {'value':
               {'get_attr':
                {self.cmpUtils.MISMATCH_VALUE1_LABEL:
                 ['server', 'networks', 'private', 0],
                 self.cmpUtils.MISMATCH_VALUE2_LABEL:
                 ['server', 'networks', 'public', 0]}}}}},
            self.cmpUtils.diff_dicts(expected, provided))

    def test_yamlutils_get_dict_missing_file(self):
        self.assertIsNone(self.yamlUtils.get_dict('./no_file.yaml'))

    def test_yamlutils_get_dict(self):
        yaml_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../tests/data/custom_types/rsyslog.yaml')
        dict = \
            {'tosca_definitions_version': 'tosca_simple_yaml_1_0',
             'description':
             'RSYSLOG is the Rocket-fast SYStem for LOG processing.\n',
             'node_types':
             {'tosca.nodes.SoftwareComponent.Rsyslog':
              {'derived_from': 'tosca.nodes.SoftwareComponent',
               'requirements':
               [{'log_endpoint':
                 {'capability': 'tosca.capabilities.Endpoint',
                  'node': 'tosca.nodes.SoftwareComponent.Logstash',
                  'relationship': 'tosca.relationships.ConnectsTo'}}]}}}
        self.assertEqual(dict, self.yamlUtils.get_dict(yaml_file))

    def test_yamlutils_compare_yamls(self):
        yaml_file1 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../tests/data/custom_types/kibana.yaml')
        yaml_file2 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../tests/data/custom_types/collectd.yaml')
        self.assertTrue(self.yamlUtils.compare_yamls(yaml_file1, yaml_file1))
        self.assertFalse(self.yamlUtils.compare_yamls(yaml_file1, yaml_file2))

    def test_yamlutils_compare_yaml_dict(self):
        yaml_file1 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../tests/data/custom_types/rsyslog.yaml')
        yaml_file2 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../tests/data/custom_types/collectd.yaml')
        dict = \
            {'tosca_definitions_version': 'tosca_simple_yaml_1_0',
             'description':
             'RSYSLOG is the Rocket-fast SYStem for LOG processing.\n',
             'node_types':
             {'tosca.nodes.SoftwareComponent.Rsyslog':
              {'derived_from': 'tosca.nodes.SoftwareComponent',
               'requirements':
               [{'log_endpoint':
                 {'capability': 'tosca.capabilities.Endpoint',
                  'node': 'tosca.nodes.SoftwareComponent.Logstash',
                  'relationship': 'tosca.relationships.ConnectsTo'}}]}}}
        self.assertEqual({}, self.cmpUtils.diff_dicts(
            self.yamlUtils.get_dict(yaml_file1), dict))
        self.assertFalse(self.yamlUtils.compare_yaml_dict(yaml_file2, dict))

    def test_assert_value_is_num(self):
        value = 1
        output = translator.common.utils.str_to_num(value)
        self.assertEqual(value, output)

    def test_urlutils_validate_url(self):
        self.assertTrue(self.UrlUtils.validate_url("http://www.github.com/"))
        self.assertTrue(
            self.UrlUtils.validate_url("https://github.com:81/a/2/a.b"))
        self.assertTrue(self.UrlUtils.validate_url("ftp://github.com"))
        self.assertFalse(self.UrlUtils.validate_url("github.com"))
        self.assertFalse(self.UrlUtils.validate_url("123"))
        self.assertFalse(self.UrlUtils.validate_url("a/b/c"))

    def test_get_dict_value(self):
        single_snippet = \
            {'nodejs_create_config':
             {'type': 'tosca.nodes.SoftwareConfig',
              'properties':
              {'config':
               {'get_file': 'create.sh'}}}}
        actual_output_single_snippet = []
        ex_output_single_snippet = ['create.sh']
        translator.common.utils.get_dict_value(single_snippet, "get_file",
                                               actual_output_single_snippet)
        self.assertEqual(actual_output_single_snippet,
                         ex_output_single_snippet)
        multi_snippet = \
            {'resources':
             {'nodejs_create_config':
              {'type': 'tosca.nodes.SoftwareConfig',
               'properties':
               {'config':
                {'get_file': 'nodejs/create.sh'}}},
              'mongodb_create_config':
              {'type': 'tosca.nodes.SoftwareConfig',
               'properties':
               {'config':
                {'get_file': 'mongodb/create.sh'}}}}}

        actual_output_multi_snippet = []
        ex_output_multi_snippet = ['mongodb/create.sh',
                                   'nodejs/create.sh']
        translator.common.utils.get_dict_value(multi_snippet, "get_file",
                                               actual_output_multi_snippet)
        self.assertEqual(sorted(actual_output_multi_snippet),
                         ex_output_multi_snippet)
