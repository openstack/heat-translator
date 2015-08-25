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
TARGET_CLASS_NAME = 'ToscaElasticsearch'


class ToscaElasticsearch(HotResource):
    '''Translate TOSCA type tosca.nodes.SoftwareComponent.Elasticsearch.'''

    toscatype = 'tosca.nodes.SoftwareComponent.Elasticsearch'

    def __init__(self, nodetemplate):
        super(ToscaElasticsearch, self).__init__(nodetemplate)
        pass

    def handle_properties(self):
        pass
