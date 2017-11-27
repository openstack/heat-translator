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

import logging
from toscaparser.common.exception import InvalidPropertyValueError
from translator.hot.syntax.hot_resource import HotResource

# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaMonitoring'

log = logging.getLogger('heat-translator')

ALARM_STATISTIC = {'mean': 'mean', 'median': 'median', 'summary': 'sum',
                   'maximum': 'max', 'minimum': 'min', 'last': 'last',
                   'std': 'std', 'first': 'first', 'count': 'count'}


class ToscaMonitoring(HotResource):
    '''Translate TOSCA node type tosca.policies.Monitoring'''

    toscatype = 'tosca.policies.Monitoring'

    def __init__(self, policy, csar_dir=None):
        hot_type = "OS::Aodh::GnocchiAggregationByResourcesAlarm"
        super(ToscaMonitoring, self).__init__(policy,
                                              type=hot_type,
                                              csar_dir=csar_dir)
        self.policy = policy
        self.filter = list()

    def handle_expansion(self):
        '''handle monitoring resources in case of multiple triggers'''
        hot_type = 'OS::Aodh::GnocchiAggregationByResourcesAlarm'
        extra_resources = list()
        extra_triggers = self.policy.entity_tpl["triggers"]
        for trigger_name, trigger_dict in extra_triggers.items():
            if trigger_name not in self.filter:
                self.filter.append(trigger_name)
                prop = self._get_monitoring_prop(trigger_dict)
                mon_resources = HotResource(self.nodetemplate,
                                            type=hot_type,
                                            name=trigger_name,
                                            properties=prop)
                extra_resources.append(mon_resources)
        return extra_resources

    def handle_properties(self):
        self.properties = {}
        if self.policy.entity_tpl.get('triggers'):
            triggers = self.policy.entity_tpl["triggers"]
            trigger_name, trigger_dict = list(triggers.items())[0]
            self.filter.append(trigger_name)
            self.properties = self._get_monitoring_prop(trigger_dict)
            self.name = trigger_name
        return self.properties

    def _get_monitoring_prop(self, trigger):
        sample = trigger.get('condition')
        prop = dict()
        prop["description"] = sample.get('constraint')
        prop["metric"] = trigger.get('metric')
        if sample.get('aggregation_method') not in ALARM_STATISTIC:
            msg = _('method should be one of given statistics')
            log.error(msg)
            raise InvalidPropertyValueError(what=msg)
        prop["aggregation_method"] = \
            ALARM_STATISTIC[sample["aggregation_method"]]
        prop["granularity"] = sample.get("granularity")
        prop["threshold"] = sample.get("threshold")
        prop["resource_type"] = sample.get("resource_type", "instance")
        prop["comparison_operator"] = sample.get('comparison_operator')
        prop['evaluation_periods'] = sample.get('evaluations')
        return prop

    def embed_substack_templates(self, hot_template_version):
        pass
