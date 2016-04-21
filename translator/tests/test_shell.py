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
import os
import shutil
import tempfile

from mock import patch
from toscaparser.common import exception
from toscaparser.utils.gettextutils import _
import translator.shell as shell
from translator.tests.base import TestCase


class ShellTest(TestCase):
    tosca_helloworld = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data/tosca_helloworld.yaml")
    template_file = '--template-file=' + tosca_helloworld
    template_type = '--template-type=tosca'
    template_validation = "--validate-only=true"
    failure_msg = _('The program raised an exception unexpectedly.')

    def test_missing_arg(self):
        error = self.assertRaises(ValueError, shell.main, '')
        err_msg = _('The program requires minimum two arguments. '
                    'Please refer to the usage documentation.')
        self.assertEqual(err_msg, str(error))

    def test_invalid_file_arg(self):
        error = self.assertRaises(ValueError, shell.main, 'translate me')
        err_msg = _('The program expects --template-file as first '
                    'argument. Please refer to the usage documentation.')
        self.assertEqual(err_msg, str(error))

    def test_invalid_type_arg(self):
        error = self.assertRaises(ValueError,
                                  shell.main, ('--template-file=', 'xyz'))
        err_msg = _('The program expects --template-type as second argument. '
                    'Please refer to the usage documentation.')
        self.assertEqual(err_msg, str(error))

    def test_invalid_file_value(self):
        error = self.assertRaises(ValueError,
                                  shell.main, ('--template-file=template.txt',
                                               self.template_type))
        err_msg = _('The path template.txt is not a valid file or URL.')
        self.assertEqual(err_msg, str(error))

    def test_invalid_type_value(self):
        error = self.assertRaises(ValueError, shell.main,
                                  (self.template_file, '--template-type=xyz'))
        err_msg = _('xyz is not a valid template type.')
        self.assertEqual(err_msg, str(error))

    def test_invalid_parameters(self):
        error = self.assertRaises(ValueError, shell.main,
                                  (self.template_file, self.template_type,
                                   '--parameters=key'))
        err_msg = _("'key' is not a well-formed parameter.")
        self.assertEqual(err_msg, str(error))

    def test_valid_template(self):
        try:
            shell.main([self.template_file, self.template_type])
        except Exception:
            self.fail(self.failure_msg)

    def test_valid_template_with_parameters(self):
        tosca_single_instance_wordpress = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data/tosca_single_instance_wordpress.yaml")
        parameters = '--parameters="cpus=2;db_name=wpdb;db_user=test;'\
                     'db_port=2000;db_root_pwd=fun2test;db_pwd=fun2test"'
        template = '--template-file=' + tosca_single_instance_wordpress
        try:
            shell.main([template, self.template_type, parameters])
        except Exception:
            self.fail(self.failure_msg)

    def test_validate_only(self):
        try:
            shell.main([self.template_file, self.template_type,
                        self.template_validation])
        except Exception:
            self.fail(self.failure_msg)

        template = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data/tosca_helloworld_invalid.yaml")
        invalid_template = '--template-file=' + template
        self.assertRaises(exception.ValidationError, shell.main,
                          [invalid_template, self.template_type,
                           self.template_validation])

    def test_output_file(self):
        temp_dir = tempfile.mkdtemp()
        temp_file = "/test_translation_output.txt"
        output_file = "--output-file=" + temp_dir + temp_file
        try:
            shell.main([self.template_file, self.template_type, output_file])
        except Exception:
            self.fail(self.failure_msg)
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir)
                self.assertTrue(temp_dir is None or
                                not os.path.exists(temp_dir))

    @patch('uuid.uuid4')
    @patch('translator.common.utils.check_for_env_variables')
    @patch('requests.post')
    @patch('translator.common.utils.get_url_for')
    @patch('translator.common.utils.get_token_id')
    @patch('os.getenv')
    @patch('translator.hot.tosca.tosca_compute.'
           'ToscaCompute._create_nova_flavor_dict')
    @patch('translator.hot.tosca.tosca_compute.'
           'ToscaCompute._populate_image_dict')
    def test_template_deploy_with_credentials(self, mock_populate_image_dict,
                                              mock_flavor_dict,
                                              mock_os_getenv,
                                              mock_token,
                                              mock_url, mock_post,
                                              mock_env,
                                              mock_uuid):
        mock_uuid.return_value = 'abcXXX-abcXXX'
        mock_env.return_value = True
        mock_flavor_dict.return_value = {
            'm1.medium': {'mem_size': 4096, 'disk_size': 40, 'num_cpus': 2}
        }
        mock_populate_image_dict.return_value = {
            "rhel-6.5-test-image": {
                "version": "6.5",
                "architecture": "x86_64",
                "distribution": "RHEL",
                "type": "Linux"
            }
        }
        mock_url.return_value = 'http://abc.com'
        mock_token.return_value = 'mock_token'
        mock_os_getenv.side_effect = ['demo', 'demo',
                                      'demo', 'http://www.abc.com']
        try:
            data = {
                'stack_name': 'heat_abcXXX',
                'parameters': {},
                'template': {
                    'outputs': {},
                    'heat_template_version': '2013-05-23',
                    'description': 'Template for deploying a single server '
                                   'with predefined properties.\n',
                    'parameters': {},
                    'resources': {
                        'my_server': {
                            'type': 'OS::Nova::Server',
                            'properties': {
                                'flavor': 'm1.medium',
                                'user_data_format': 'SOFTWARE_CONFIG',
                                'image': 'rhel-6.5-test-image'
                            }
                        }
                    }
                }
            }

            mock_heat_res = {
                "stack": {
                    "id": 1234
                }
            }
            headers = {
                'Content-Type': 'application/json',
                'X-Auth-Token': 'mock_token'
            }

            class mock_response(object):
                def __init__(self, status_code, _content):
                    self.status_code = status_code
                    self._content = _content

            mock_response_obj = mock_response(201, json.dumps(mock_heat_res))
            mock_post.return_value = mock_response_obj
            shell.main([self.template_file, self.template_type,
                        "--deploy"])
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], 'http://abc.com/stacks')
            self.assertEqual(ast.literal_eval(kwargs['data']), data)
            self.assertEqual(kwargs['headers'], headers)
        except Exception:
            self.fail(self.failure_msg)
