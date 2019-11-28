#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from translator.hot.syntax.hot_resource import HotResource

# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaNfvVduScalingAspectDeltas'


class ToscaNfvVduScalingAspectDeltas(HotResource):
    """Translate TOSCA policy type

    tosca.policies.nfv.VduScalingAspectDeltas.
    """

    toscatype = 'tosca.policies.nfv.VduScalingAspectDeltas'

    def __init__(self, policy, csar_dir=None, hot_template_parameters=None):
        super(ToscaNfvVduScalingAspectDeltas, self).__init__(
            policy,
            csar_dir=csar_dir)
        self.policy = policy
        self.hot_template_parameters = hot_template_parameters

        # Extract aspect name and deltas
        tosca_props = self.get_tosca_props()
        self.aspect = tosca_props['aspect']
        self.deltas = {}
        for key, val in tosca_props['deltas'].items():
            self.deltas[key] = val['number_of_instances']

        # Extract target VDUs
        self.targets = self.policy.targets

    def handle_properties(self):
        pass
