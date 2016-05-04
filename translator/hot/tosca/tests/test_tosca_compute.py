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

import json
import mock
from mock import patch

from toscaparser.nodetemplate import NodeTemplate
from toscaparser.tests.base import TestCase
from toscaparser.utils.gettextutils import _
import toscaparser.utils.yamlparser
from translator.hot.tosca.tosca_compute import ToscaCompute


class ToscaComputeTest(TestCase):

    def _tosca_compute_test(self, tpl_snippet, expectedprops):
        nodetemplates = (toscaparser.utils.yamlparser.
                         simple_parse(tpl_snippet)['node_templates'])
        name = list(nodetemplates.keys())[0]
        try:
            nodetemplate = NodeTemplate(name, nodetemplates)
            nodetemplate.validate()
            toscacompute = ToscaCompute(nodetemplate)
            toscacompute.handle_properties()
            if not self._compare_properties(toscacompute.properties,
                                            expectedprops):
                raise Exception(_("Hot Properties are not"
                                  " same as expected properties"))
        except Exception:
            # for time being rethrowing. Will be handled future based
            # on new development in Glance and Graffiti
            raise

    def _compare_properties(self, hotprops, expectedprops):
        return all(item in hotprops.items() for item in expectedprops.items())

    def test_node_compute_with_host_and_os_capabilities(self):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
            capabilities:
              host:
                properties:
                  disk_size: 10 GB
                  num_cpus: 4
                  mem_size: 4 GB
              os:
                properties:
                  architecture: x86_64
                  type: Linux
                  distribution: Fedora
                  version: 18.0
        '''
        expectedprops = {'flavor': 'm1.large',
                         'image': 'fedora-amd64-heat-config'}
        self._tosca_compute_test(
            tpl_snippet,
            expectedprops)

    def test_node_compute_without_os_capabilities(self):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
            capabilities:
              host:
                properties:
                  disk_size: 10 GB
                  num_cpus: 4
                  mem_size: 4 GB
              #left intentionally
        '''
        expectedprops = {'flavor': 'm1.large',
                         'image': None}
        self._tosca_compute_test(
            tpl_snippet,
            expectedprops)

    def test_node_compute_without_host_capabilities(self):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
            capabilities:
              os:
                properties:
                  architecture: x86_64
                  type: Linux
                  distribution: Fedora
                  version: 18.0
        '''
        expectedprops = {'flavor': None,
                         'image': 'fedora-amd64-heat-config'}
        self._tosca_compute_test(
            tpl_snippet,
            expectedprops)

    def test_node_compute_without_properties_and_os_capabilities(self):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
            properties:
              #left intentionally
            capabilities:
              #left intentionally
        '''
        expectedprops = {'flavor': None,
                         'image': None}
        self._tosca_compute_test(
            tpl_snippet,
            expectedprops)

    def test_node_compute_with_only_type(self):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
        '''
        expectedprops = {'flavor': None,
                         'image': None}
        self._tosca_compute_test(
            tpl_snippet,
            expectedprops)

    def test_node_compute_host_capabilities_without_properties(self):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
            capabilities:
              host:
                properties:
                #left intentionally
        '''
        expectedprops = {'flavor': None}
        self._tosca_compute_test(
            tpl_snippet,
            expectedprops)

    def test_node_compute_host_capabilities_without_disk_size(self):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
            capabilities:
              host:
                properties:
                  num_cpus: 4
                  mem_size: 4 GB
        '''
        expectedprops = {'flavor': 'm1.large'}
        self._tosca_compute_test(
            tpl_snippet,
            expectedprops)

    def test_node_compute_host_capabilities_without_mem_size(self):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
            capabilities:
              host:
                properties:
                  num_cpus: 4
                  disk_size: 10 GB
        '''
        expectedprops = {'flavor': 'm1.large'}
        self._tosca_compute_test(
            tpl_snippet,
            expectedprops)

    def test_node_compute_host_capabilities_without_mem_size_disk_size(self):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
            capabilities:
              host:
                properties:
                  num_cpus: 4
        '''
        expectedprops = {'flavor': 'm1.large'}
        self._tosca_compute_test(
            tpl_snippet,
            expectedprops)

    @patch('requests.post')
    @patch('requests.get')
    @patch('os.getenv')
    def test_node_compute_with_nova_flavor(self, mock_os_getenv,
                                           mock_get, mock_post):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
            capabilities:
              host:
                properties:
                  num_cpus: 1
                  disk_size: 1 GB
                  mem_size: 1 GB
        '''
        with patch('translator.common.utils.'
                   'check_for_env_variables') as mock_check_env:
            mock_check_env.return_value = True
            mock_os_getenv.side_effect = ['demo', 'demo',
                                          'demo', 'http://abc.com/5000/',
                                          'demo', 'demo',
                                          'demo', 'http://abc.com/5000/']
            mock_ks_response = mock.MagicMock()
            mock_ks_response.status_code = 200
            mock_ks_content = {
                'access': {
                    'token': {
                        'id': 'd1dfa603-3662-47e0-b0b6-3ae7914bdf76'
                    },
                    'serviceCatalog': [{
                        'type': 'compute',
                        'endpoints': [{
                            'publicURL': 'http://abc.com'
                        }]
                    }]
                }
            }
            mock_ks_response.content = json.dumps(mock_ks_content)
            mock_nova_response = mock.MagicMock()
            mock_nova_response.status_code = 200
            mock_flavor_content = {
                'flavors': [{
                    'name': 'm1.mock_flavor',
                    'ram': 1024,
                    'disk': 1,
                    'vcpus': 1
                }]
            }
            mock_nova_response.content = \
                json.dumps(mock_flavor_content)
            mock_post.return_value = mock_ks_response
            mock_get.return_value = mock_nova_response
            expectedprops = {'flavor': 'm1.mock_flavor'}
            self._tosca_compute_test(
                tpl_snippet,
                expectedprops)

    @patch('requests.post')
    @patch('requests.get')
    @patch('os.getenv')
    def test_node_compute_without_nova_flavor(self, mock_os_getenv,
                                              mock_get, mock_post):
        tpl_snippet = '''
        node_templates:
          server:
            type: tosca.nodes.Compute
            capabilities:
              host:
                properties:
                  num_cpus: 1
                  disk_size: 1 GB
                  mem_size: 1 GB
        '''
        with patch('translator.common.utils.'
                   'check_for_env_variables') as mock_check_env:
            mock_check_env.return_value = True
            mock_os_getenv.side_effect = ['demo', 'demo',
                                          'demo', 'http://abc.com/5000/']
            mock_ks_response = mock.MagicMock()
            mock_ks_content = {}
            mock_ks_response.content = json.dumps(mock_ks_content)
            expectedprops = {'flavor': 'm1.small',
                             'user_data_format': 'SOFTWARE_CONFIG',
                             'image': None}
            self._tosca_compute_test(
                tpl_snippet,
                expectedprops)
