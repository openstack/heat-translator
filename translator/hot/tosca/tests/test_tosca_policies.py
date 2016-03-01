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
from toscaparser.policy import Policy
from toscaparser.tests.base import TestCase
import toscaparser.utils.yamlparser
from translator.hot.tosca.tosca_compute import ToscaCompute
from translator.hot.tosca.tosca_policies import ToscaPolicies


class ToscaPoicyTest(TestCase):

    def _tosca_policy_test(self, tpl_snippet, expectedprops):
        nodetemplates = (toscaparser.utils.yamlparser.
                         simple_parse(tpl_snippet)['node_templates'])
        policies = (toscaparser.utils.yamlparser.
                    simple_parse(tpl_snippet)['policies'])
        name = list(nodetemplates.keys())[0]
        policy_name = list(policies[0].keys())[0]
        for policy in policies:
            tpl = policy[policy_name]
            targets = tpl["targets"]
        try:
            nodetemplate = NodeTemplate(name, nodetemplates)
            toscacompute = ToscaCompute(nodetemplate)
            toscacompute.handle_properties()

            policy = Policy(policy_name, tpl, targets,
                            "node_templates")
            toscapolicy = ToscaPolicies(policy)
            nodetemplate = [toscacompute]
            toscapolicy.handle_properties(nodetemplate)

            self.assertEqual(toscacompute.properties, expectedprops)
        except Exception:
            raise

    def test_compute_with_policies(self):
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
        policies:
          - my_compute_placement_policy:
              type: tosca.policies.Placement
              description: Apply my placement policy to my application servers
              targets: [ server ]
        '''
        expectedprops = {'flavor': 'm1.large',
                         'image': 'fedora-amd64-heat-config',
                         'scheduler_hints': {
                             'group': {
                                 'get_resource':
                                 'my_compute_placement_policy'}},
                         'user_data_format': 'SOFTWARE_CONFIG'}
        self._tosca_policy_test(
            tpl_snippet,
            expectedprops)
