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


import ast
import json
import logging
import logging.config
import os
import prettytable
import requests
import sys
import uuid
import yaml

from toscaparser.tosca_template import ToscaTemplate
from toscaparser.utils.gettextutils import _
from toscaparser.utils.urlutils import UrlUtils
from translator.common import utils
from translator.conf.config import ConfigProvider
from translator.hot.tosca_translator import TOSCATranslator

"""
Test the heat-translator translation from command line as:
#heat-translator
  --template-file=<path to the YAML template>
  --template-type=<type of template e.g. tosca>
  --parameters="purpose=test"
Takes three user arguments,
1. type of translation (e.g. tosca) (required)
2. Path to the file that needs to be translated (required)
3. Input parameters (optional)

In order to use heat-translator to only validate template,
without actual translation, pass --validate-only=true along with
other required arguments.

"""
conf_file = ConfigProvider.get_translator_logging_file()
logging.config.fileConfig(conf_file)
log = logging.getLogger("heat-translator")


class TranslatorShell(object):

    SUPPORTED_TYPES = ['tosca']

    def _validate(self, args):
        if len(args) < 2:
            msg = _("The program requires minimum two arguments. "
                    "Please refer to the usage documentation.")
            log.error(msg)
            raise ValueError(msg)
        if "--template-file=" not in args[0]:
            msg = _("The program expects --template-file as first argument. "
                    "Please refer to the usage documentation.")
            log.error(msg)
            raise ValueError(msg)
        if "--template-type=" not in args[1]:
            msg = _("The program expects --template-type as second argument. "
                    "Please refer to the usage documentation.")
            log.error(msg)
            raise ValueError(msg)

    def main(self, args):
        # TODO(spzala): set self.deploy based on passed args once support for
        # --deploy argument is enabled.
        self.deploy = False
        self._validate(args)
        path = args[0].split('--template-file=')[1]
        # e.g. --template_file=translator/tests/data/tosca_helloworld.yaml
        template_type = args[1].split('--template-type=')[1]
        # e.g. --template_type=tosca
        if not template_type:
            msg = _("Template type is needed. For example, 'tosca'")
            log.error(msg)
            raise ValueError(msg)
        elif template_type not in self.SUPPORTED_TYPES:
            msg = _("%(value)s is not a valid template type.") % {
                'value': template_type}
            log.error(msg)
            raise ValueError(msg)
        parsed_params = {}
        validate_only = None
        output_file = None
        if len(args) > 2:
            parameters = None
            for arg in args:
                if "--validate-only=" in arg:
                    validate_only = arg
                if "--parameters=" in arg:
                    parameters = arg
                if "--output-file=" in arg:
                    output = arg
                    output_file = output.split('--output-file=')[1]
                if "--deploy" in arg:
                    self.deploy = True
            if parameters:
                parsed_params = self._parse_parameters(parameters)
        a_file = os.path.isfile(path)
        a_url = UrlUtils.validate_url(path) if not a_file else False
        if a_file or a_url:
            run_only_validation = False
            if validate_only:
                value = validate_only.split('-validate-only=')[1].lower()
                if template_type == 'tosca' and value == 'true':
                    run_only_validation = True
            if run_only_validation:
                ToscaTemplate(path, parsed_params, a_file)
                msg = (_('The input "%(path)s" successfully passed '
                         'validation.') % {'path': path})
                print(msg)
            else:
                log.info(
                    _('Checked whether template path is a file or url path.'))
                heat_tpl = self._translate(template_type, path, parsed_params,
                                           a_file)
                if heat_tpl:
                    if utils.check_for_env_variables() and self.deploy:
                        try:
                            heatclient(heat_tpl, parsed_params)
                        except Exception:
                            log.error(_("Unable to launch the heat stack"))

                    self._write_output(heat_tpl, output_file)
        else:
            msg = _("The path %(path)s is not a valid file or URL.") % {
                'path': path}
            log.error(msg)
            raise ValueError(msg)

    def _parse_parameters(self, parameter_list):
        parsed_inputs = {}
        if parameter_list.startswith('--parameters'):
            # Parameters are semi-colon separated
            inputs = parameter_list.split('--parameters=')[1].\
                replace('"', '').split(';')
            # Each parameter should be an assignment
            for param in inputs:
                keyvalue = param.split('=')
                # Validate the parameter has both a name and value
                msg = _("'%(param)s' is not a well-formed parameter.") % {
                    'param': param}
                if keyvalue.__len__() is 2:
                    # Assure parameter name is not zero-length or whitespace
                    stripped_name = keyvalue[0].strip()
                    if not stripped_name:
                        log.error(msg)
                        raise ValueError(msg)
                    # Add the valid parameter to the dictionary
                    parsed_inputs[keyvalue[0]] = keyvalue[1]
                else:
                    log.error(msg)
                    raise ValueError(msg)
        else:
            msg = _("'%(list)s' is not a valid parameter list.") % {
                'list': parameter_list}
            log.error(msg)
            raise ValueError(msg)
        return parsed_inputs

    def _translate(self, sourcetype, path, parsed_params, a_file):
        output = None
        if sourcetype == "tosca":
            log.debug(_('Loading the tosca template.'))
            tosca = ToscaTemplate(path, parsed_params, a_file)
            translator = TOSCATranslator(tosca, parsed_params, self.deploy)
            log.debug(_('Translating the tosca template.'))
            output = translator.translate()
        return output

    def _write_output(self, output, output_file=None):
        if output:
            if output_file:
                with open(output_file, 'w+') as f:
                    f.write(output)
            else:
                print(output)


def heatclient(output, params):
    try:
        access_dict = utils.get_ks_access_dict()
        endpoint = utils.get_url_for(access_dict, 'orchestration')
        token = utils.get_token_id(access_dict)
    except Exception as e:
        log.error(e)
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': token
    }
    heat_stack_name = "heat_" + str(uuid.uuid4()).split("-")[0]
    output = yaml.load(output)
    output['heat_template_version'] = str(output['heat_template_version'])
    data = {
        'stack_name': heat_stack_name,
        'template': output,
        'parameters': params
    }
    response = requests.post(endpoint + '/stacks',
                             data=json.dumps(data),
                             headers=headers)
    content = ast.literal_eval(response._content)
    if response.status_code == 201:
        stack_id = content["stack"]["id"]
        get_url = endpoint + '/stacks/' + heat_stack_name + '/' + stack_id
        get_stack_response = requests.get(get_url,
                                          headers=headers)
        stack_details = json.loads(get_stack_response.content)["stack"]
        col_names = ["id", "stack_name", "stack_status", "creation_time",
                     "updated_time"]
        pt = prettytable.PrettyTable(col_names)
        stack_list = []
        for col in col_names:
            stack_list.append(stack_details[col])
        pt.add_row(stack_list)
        print(pt)
    else:
        err_msg = content["error"]["message"]
        log(_("Unable to deploy to Heat\n%s\n") % err_msg)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    TranslatorShell().main(args)


if __name__ == '__main__':
    main()
