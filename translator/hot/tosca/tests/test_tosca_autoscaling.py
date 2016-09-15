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
from translator.hot.tosca.tosca_policies_scaling import ToscaAutoscaling


class AutoscalingTest(TestCase):

    def _tosca_scaling_test(self, tpl_snippet, expectedprops):
        nodetemplates = (toscaparser.utils.yamlparser.
                         simple_parse(tpl_snippet)['node_templates'])
        policies = (toscaparser.utils.yamlparser.
                    simple_parse(tpl_snippet)['policies'])
        name = list(nodetemplates.keys())[0]
        policy_name = list(policies[0].keys())[0]
        for policy in policies:
            tpl = policy[policy_name]
            targets = tpl["targets"]
            properties = tpl["properties"]
        try:
            nodetemplate = NodeTemplate(name, nodetemplates)
            toscacompute = ToscaCompute(nodetemplate)
            toscacompute.handle_properties()
            policy = Policy(policy_name, tpl, targets,
                            properties, "node_templates")
            toscascaling = ToscaAutoscaling(policy)
            parameters = toscascaling.handle_properties([toscacompute])
            self.assertEqual(parameters[0].properties, expectedprops)
        except Exception:
            raise

    def test_compute_with_scaling(self):
        tpl_snippet = '''
        node_templates:
          my_server_1:
            type: tosca.nodes.Compute
            capabilities:
              host:
               properties:
                num_cpus: 2
                disk_size: 10 GB
                mem_size: 512 MB
              os:
               properties:
           # host Operating System image properties
                  architecture: x86_64
                  type: Linux
                  distribution: RHEL
                  version: 6.5
        policies:
          - asg:
              type: tosca.policies.Scaling
              description: Simple node autoscaling
              targets: [my_server_1]
              triggers:
                resize_compute:
                  description: trigger
                  condition:
                    constraint: utilization greater_than 50%
                    period: 60
                    evaluations: 1
                    method: average
              properties:
                min_instances: 2
                max_instances: 10
                default_instances: 3
                increment: 1
              '''

        expectedprops = {'desired_capacity': 3,
                         'max_size': 10,
                         'min_size': 2,
                         'resource': {'type': 'asg_res.yaml'}}

        self._tosca_scaling_test(
            tpl_snippet,
            expectedprops)
