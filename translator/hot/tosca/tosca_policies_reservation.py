# Copyright (C) 2018 NTT DATA
# All Rights Reserved.
#
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

import logging
from translator.hot.syntax.hot_resource import HotResource

# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaReservation'

log = logging.getLogger('heat-translator')


class ToscaReservation(HotResource):
    '''Translate TOSCA node type tosca.policies.Reservation'''

    toscatype = 'tosca.policies.Reservation'

    def __init__(self, policy, csar_dir=None):
        hot_type = "OS::Aodh::EventAlarm"
        super(ToscaReservation, self).__init__(policy,
                                               type=hot_type,
                                               csar_dir=csar_dir)
        self.policy = policy
        self.filter = list()

    def handle_expansion(self):
        extra_resources = list()
        hot_type = 'OS::Aodh::EventAlarm'
        for action_name in self.filter:
            prop = self._get_event_type(action_name)
            resrv_resources = HotResource(self.nodetemplate,
                                          type=hot_type,
                                          name=action_name,
                                          properties=prop)
            extra_resources.append(resrv_resources)
        return extra_resources

    def handle_properties(self):
        if self.policy.entity_tpl.get('reservation'):
            reservation_prop = self.policy.entity_tpl["reservation"].items()
            for action_name, action_dict in reservation_prop:
                if action_name != 'properties':
                    self.filter.append(action_name)
            self.name = self.filter[0]

    def _get_event_type(self, action):
        if action == 'start_actions':
            return {'event_type': 'lease.event.start_lease'}
        if action == 'before_end_actions':
            return {'event_type': 'lease.event.before_end_lease'}
        if action == 'end_actions':
            return {'event_type': 'lease.event.end_lease'}
