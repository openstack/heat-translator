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
TARGET_CLASS_NAME = 'ToscaNfvInstantiationLevels'


class ToscaNfvInstantiationLevels(HotResource):
    """Translate TOSCA policy type tosca.policies.nfv.InstantiationLevels."""

    toscatype = 'tosca.policies.nfv.InstantiationLevels'

    def __init__(self, policy, csar_dir=None, hot_template_parameters=None):
        super(ToscaNfvInstantiationLevels, self).__init__(
            policy,
            csar_dir=csar_dir)
        self.policy = policy
        self.hot_template_parameters = hot_template_parameters

    def handle_properties(self):
        pass
