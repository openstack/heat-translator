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


import logging.config
import os
import sys

from toscaparser.tosca_template import ToscaTemplate
from toscaparser.utils.gettextutils import _
from toscaparser.utils.urlutils import UrlUtils
from translator.hot.tosca_translator import TOSCATranslator

"""
Test the heat-translator from command line as:
#heat_translator
  --template-file=<path to the YAML template>
  --template-type=<type of template e.g. tosca>
  --parameters="purpose=test"
Takes three user arguments,
1. type of translation (e.g. tosca) (required)
2. Path to the file that needs to be translated (required)
3. Input parameters (optional)

This is an entry point for testing purpose on CLI.
"""

log = logging.getLogger("heat-translator")


def main():
    if len(sys.argv) < 3:
        msg = _("The program requires minimum two arguments. "
                "Please refer to the usage documentation.")
        raise ValueError(msg)
    if "--template-file=" not in sys.argv[1]:
        msg = _("The program expects --template-file as first argument. "
                "Please refer to the usage documentation.")
        raise ValueError(msg)
    if "--template-type=" not in sys.argv[2]:
        msg = _("The program expects --template-type as second argument. "
                "Please refer to the usage documentation.")
        raise ValueError(msg)
    path = sys.argv[1].split('--template-file=')[1]
    # e.g. --template_file=translator/tests/data/tosca_helloworld.yaml
    template_type = sys.argv[2].split('--template-type=')[1]
    # e.g. --template_type=tosca
    supported_types = ['tosca']
    if not template_type:
        raise ValueError(_("Template type is needed. For example, 'tosca'"))
    elif template_type not in supported_types:
        raise ValueError(_("%(value)s is not a valid template type.")
                         % {'value': template_type})
    parsed_params = {}
    if len(sys.argv) > 3:
        parsed_params = parse_parameters(sys.argv[3])

    a_file = os.path.isfile(path)
    a_url = UrlUtils.validate_url(path) if not a_file else False
    if a_file or a_url:
        heat_tpl = translate(template_type, path, parsed_params, a_file)
        if heat_tpl:
            write_output(heat_tpl)
    else:
        raise ValueError(_("The path %(path)s is not a valid file or URL.") %
                         {'path': path})


def parse_parameters(parameter_list):
    parsed_inputs = {}
    if parameter_list.startswith('--parameters'):
        inputs = parameter_list.split('--parameters=')[1].\
            replace('"', '').split(';')
        for param in inputs:
            keyvalue = param.split('=')
            parsed_inputs[keyvalue[0]] = keyvalue[1]
    else:
        raise ValueError(_("%(param) is not a valid parameter.")
                         % parameter_list)
    return parsed_inputs


def translate(sourcetype, path, parsed_params, a_file):
    output = None
    if sourcetype == "tosca":
        tosca = ToscaTemplate(path, parsed_params, a_file)
        translator = TOSCATranslator(tosca, parsed_params)
        output = translator.translate()
    return output


def write_output(output):
    print(output)

if __name__ == '__main__':
    main()
