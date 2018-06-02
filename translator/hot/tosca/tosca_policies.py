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
TARGET_CLASS_NAME = 'ToscaPolicies'


class ToscaPolicies(HotResource):
    '''Translate TOSCA policy type tosca.policies.Placement.'''

    toscatype = 'tosca.policies.Placement'

    def __init__(self, policy, csar_dir=None):
        super(ToscaPolicies, self).__init__(policy,
                                            type='OS::Nova::ServerGroup',
                                            csar_dir=csar_dir)
        self.policy = policy

    def handle_properties(self, resources):
        group_policy = "%(soft-prefix)s%(policy)s" % {
            "soft-prefix": "soft-" if not self.get_tosca_props().get(
                "strict", True) else "",
            "policy": self.get_tosca_props().get("policy", "affinity"),
        }
        self.properties["name"] = self.name
        self.properties["policies"] = [group_policy]
        for resource in resources:
            if resource.name in self.policy.targets:
                resource.properties["scheduler_hints"] = {
                    "group": {"get_resource": self.name}}
