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

from toscaparser.utils.gettextutils import _
from translator.hot.syntax.hot_output import HotOutput

log = logging.getLogger('heat-translator')


class TranslateOutputs(object):
    '''Translate TOSCA Outputs to Heat Outputs.'''

    def __init__(self, outputs, node_translator):
        log.debug(_('Translating TOSCA outputs to HOT outputs.'))
        self.outputs = outputs
        self.nodes = node_translator

    def translate(self):
        return self._translate_outputs()

    def _translate_outputs(self):
        hot_outputs = []
        for output in self.outputs:
            hot_value = self.nodes.translate_param_value(output.value, None)
            if hot_value is not None:
                hot_outputs.append(HotOutput(output.name, hot_value,
                                             output.description))
        return hot_outputs
