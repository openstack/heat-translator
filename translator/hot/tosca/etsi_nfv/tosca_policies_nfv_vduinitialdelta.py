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
TARGET_CLASS_NAME = 'ToscaNfvVduInitialDelta'


class ToscaNfvVduInitialDelta(HotResource):
    """Translate TOSCA policy type tosca.policies.nfv.VduInitialDelta."""

    toscatype = 'tosca.policies.nfv.VduInitialDelta'

    def __init__(self, policy, csar_dir=None, hot_template_parameters=None):
        super(ToscaNfvVduInitialDelta, self).__init__(
            policy,
            csar_dir=csar_dir)
        self.policy = policy
        self.hot_template_parameters = hot_template_parameters

        # Extract number_of_instances
        tosca_props = self.get_tosca_props()
        self.num = tosca_props['initial_delta']['number_of_instances']

        # Extract targets
        self.targets = self.policy.targets

    def handle_properties(self):
        pass
