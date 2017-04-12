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

from toscaparser.nodetemplate import NodeTemplate
from toscaparser.tests.base import TestCase
import toscaparser.utils.yamlparser
from translator.hot.tosca.tosca_floating import ToscaFloatingIP


class ToscaFloatingIPTest(TestCase):

    def _tosca_floatingip_test(self, tpl_snippet, expectedprops, name=None):
        nodetemplates = (toscaparser.utils.yamlparser.
                         simple_parse(tpl_snippet)['node_templates'])
        if not name:
            name = list(nodetemplates.keys())[0]
        nodetemplate = NodeTemplate(name, nodetemplates, custom_def=[])
        nodetemplate.validate()
        tosca_floatingip = ToscaFloatingIP(nodetemplate)
        tosca_floatingip.handle_properties()
        self.assertEqual(expectedprops, tosca_floatingip.properties)

    def test_node_floatingip_with_properties(self):
        tpl_snippet = '''
        node_templates:
          floating_ip:
            type: tosca.nodes.network.FloatingIP
            properties:
              floating_network: public
              floating_ip_address: 192.168.56.8
              port_id: abcd
        '''
        expectedprops = {'floating_network': 'public',
                         'floating_ip_address': '192.168.56.8',
                         'port_id': 'abcd'}
        self._tosca_floatingip_test(
            tpl_snippet,
            expectedprops)

    def test_node_floatingip_with_properties_and_link_requirements(self):
        tpl_snippet = '''
        node_templates:
          floating_ip:
            type: tosca.nodes.network.FloatingIP
            properties:
              floating_network: public
              floating_ip_address: 192.168.56.8
            requirements:
              - link:
                  node: port1
          port1:
            type: tosca.nodes.network.Port
            properties:
              ip_address: 10.0.0.6
        '''
        expectedprops = {'floating_network': 'public',
                         'floating_ip_address': '192.168.56.8',
                         'port_id': '{ get_resource: port1 }'}
        self._tosca_floatingip_test(
            tpl_snippet,
            expectedprops,
            name='floating_ip')
