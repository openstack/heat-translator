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

import datetime
import yaml

from toscaparser.nodetemplate import NodeTemplate
from toscaparser.policy import Policy
from toscaparser.tests.base import TestCase
import toscaparser.utils.yamlparser

from translator.hot.syntax.hot_parameter import HotParameter
from translator.hot.tosca.tosca_compute import ToscaCompute
from translator.hot.tosca.tosca_policies_scaling import ToscaAutoscaling

HOT_TEMPLATE_VERSION = '2013-05-23'


class AutoscalingTest(TestCase):

    def _tosca_scaling_test(self, tpl_snippet, expectedprops,
                            hot_template_parameters=None):
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
            toscascaling = ToscaAutoscaling(
                policy, hot_template_parameters=hot_template_parameters)
            parameters = toscascaling.handle_properties([toscacompute])
            if hot_template_parameters:
                substack_template = toscascaling.extract_substack_templates(
                    "output.yaml", HOT_TEMPLATE_VERSION)
                actual_nested_resource = yaml.load(
                    substack_template['SP1_res.yaml'])
                self.assertEqual(expectedprops,
                                 actual_nested_resource)
            else:
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
                    granularity: 60
                    evaluations: 1
                    aggregation_method: mean
                    resource_type: instance
                    comparison_operator: gt
              properties:
                min_instances: 2
                max_instances: 10
                default_instances: 3
                increment: 1
                cooldown: 60
              '''

        expectedprops = {'desired_capacity': 3,
                         'max_size': 10,
                         'min_size': 2,
                         'cooldown': 60,
                         'resource': {'type': 'asg_res.yaml'}}

        self._tosca_scaling_test(
            tpl_snippet,
            expectedprops)

    def test_scaling_nested_template_with_params(self):
        tpl_snippet = '''
        node_templates:
          VDU1:
            type: tosca.nodes.Compute
            properties:
              image: { get_input: image_name }
              flavor: { get_input: flavor }
              mgmt_driver: noop
              availability_zone: nova
              metadata: {metering.server_group: SG1}

        policies:
          - SP1:
              type: tosca.policies.Scaling
              targets: [VDU1]
              properties:
                increment: 1
                cooldown: 120
                min_instances: 1
                max_instances: 3
                default_instances: 1
            '''

        expected_nested_resource = {'heat_template_version':
                                    datetime.date(2013, 5, 23),
                                    'description':
                                        'Tacker Scaling template',
                                    'parameters':
                                        {'flavor':
                                         {'default': 'm1.tiny',
                                          'type': 'string',
                                          'description':
                                              'Flavor Information'
                                          },
                                         'image_name':
                                             {'default':
                                              'cirros-0.3.5-x86_64-disk',
                                              'type': 'string',
                                              'description': 'Image Name'
                                              }
                                         },
                                    'resources':
                                        {'VDU1':
                                             {'type':
                                              'OS::Nova::Server',
                                              'properties':
                                                  {'flavor': None,
                                                   'user_data_format':
                                                       'SOFTWARE_CONFIG'
                                                   }
                                              }
                                         }
                                    }

        flavor = HotParameter('flavor', 'string',
                              label=None,
                              description='Flavor Information',
                              default='m1.tiny',
                              hidden=None,
                              constraints=[])
        image = HotParameter('image_name', 'string',
                             label=None,
                             description='Image Name',
                             default='cirros-0.3.5-x86_64-disk',
                             hidden=None,
                             constraints=[])
        hot_template_parameters = [flavor, image]
        self._tosca_scaling_test(tpl_snippet,
                                 expected_nested_resource,
                                 hot_template_parameters)
