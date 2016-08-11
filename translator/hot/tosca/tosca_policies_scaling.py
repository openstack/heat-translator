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
TARGET_CLASS_NAME = 'ToscaAutoscaling'


class ToscaAutoscaling(HotResource):
    '''Translate TOSCA node type tosca.policies.Scaling'''

    toscatype = 'tosca.policies.Scaling'

    def __init__(self, policy):
        hot_type = "OS::Heat::ScalingPolicy"
        super(ToscaAutoscaling, self).__init__(policy,
                                               type=hot_type)
        self.policy = policy

    def handle_expansion(self):
        sample = self.policy.\
            entity_tpl["triggers"]["resize_compute"]["condition"]
        prop = {}
        prop["description"] = self.policy.entity_tpl['description']
        prop["meter_name"] = "cpu_util"
        prop["statistic"] = sample["method"]
        prop["period"] = sample["period"]
        prop["threshold"] = sample["evaluations"]
        prop["comparison_operator"] = "gt"
        ceilometer_resources = HotResource(self.nodetemplate,
                                           type='OS::Ceilometer::Alarm',
                                           name=self.name + '_alarm',
                                           properties=prop)
        hot_resources = [ceilometer_resources]
        return hot_resources

    def handle_properties(self, resources):
        for node in self.policy.targets:
            self.properties = {}
            self.properties["auto_scaling_group_id"] = {'get_resource': node}
            self.properties["adjustment_type"] = "change_in_capacity "
            self.properties["scaling_adjustment"] = self.\
                policy.entity_tpl["properties"]["increment"]
        for index, resource in enumerate(resources):
            if resource.name in self.policy.targets and \
                resource.type != 'OS::Heat::AutoScalingGroup':
                temp = self.policy.entity_tpl["properties"]
                props = {}
                res = {}
                res["min_size"] = temp["min_instances"]
                res["max_size"] = temp["max_instances"]
                res["default_instances"] = temp["default_instances"]
                props['type'] = resource.type
                props['properties'] = resource.properties
                res['resources'] = props
                scaling_resources = \
                    HotResource(resource,
                                type='OS::Heat::AutoScalingGroup',
                                name=resource.name,
                                properties=res)
                resources.pop(index)
                resources.insert(index, scaling_resources)
        return resources
