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

from translator.hot.tosca.etsi_nfv.common_affinityrule.\
    tosca_policies_nfv_common_affinityrule import ToscaNfvCommonAffinityRule

# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaNfvAntiAffinityRule'


class ToscaNfvAntiAffinityRule(ToscaNfvCommonAffinityRule):
    """Translate TOSCA policy type tosca.policies.nfv.AntiAffinityRule."""

    toscatype = 'tosca.policies.nfv.AntiAffinityRule'

    def __init__(self, policy, csar_dir=None):
        super(ToscaNfvAntiAffinityRule, self).__init__(
            policy,
            csar_dir=csar_dir)
        self.is_anti = True

    def handle_properties(self, resources):
        super().handle_properties(resources)
