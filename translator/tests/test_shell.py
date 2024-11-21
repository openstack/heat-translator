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


import json
import os
import shutil
import tempfile
from unittest import mock

from toscaparser.common import exception
from toscaparser.utils.gettextutils import _
import translator.shell as shell
from translator.tests.base import TestCase
from translator.tests import utils


class ShellTest(TestCase):
    tosca_helloworld = utils.test_sample("tosca_helloworld.yaml")
    template_file = '--template-file=' + tosca_helloworld
    template_type = '--template-type=tosca'
    template_validation = "--validate-only"
    failure_msg = _('The program raised an exception unexpectedly.')

    def test_invalid_file_value(self):
        error = self.assertRaises(ValueError,
                                  shell.main, ('--template-file=template.txt',
                                               self.template_type))
        err_msg = _('The path template.txt is not a valid file or URL.')
        self.assertEqual(err_msg, str(error))

    def test_invalid_type_value(self):
        self.assertRaises(SystemExit, shell.main,
                          (self.template_file, '--template-type=xyz'))

    def test_invalid_parameters(self):
        self.assertRaises(ValueError, shell.main,
                          (self.template_file, self.template_type,
                           '--parameters=key'))

    def test_valid_template(self):
        shell.main([self.template_file, self.template_type])

    def test_valid_template_without_type(self):
        try:
            shell.main([self.template_file])
        except Exception:
            self.fail(self.failure_msg)

    def test_valid_template_with_parameters(self):
        tosca_single_instance_wordpress = utils.test_sample(
            "tosca_single_instance_wordpress.yaml")
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

        template = utils.test_sample("tosca_helloworld_invalid.yaml")
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

    @mock.patch('uuid.uuid4')
    @mock.patch.object(shell.TranslatorShell, '_create_stack')
    @mock.patch('keystoneauth1.loading.load_auth_from_argparse_arguments')
    @mock.patch('keystoneauth1.loading.load_session_from_argparse_arguments')
    @mock.patch('translator.common.flavors.get_flavors')
    @mock.patch('translator.common.images.get_images')
    def test_template_deploy(self, mock_populate_image_dict,
                             mock_flavor_dict,
                             mock_keystone_session,
                             mock_keystone_auth,
                             mock_client,
                             mock_uuid):
        mock_uuid.return_value = 'abcXXX-abcXXX'
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

        try:
            data = {
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

            mock_heat_res = {
                "stacks": [
                    {
                        "id": "d648ad27-fb9c-44d1-b293-646ea6c4f8da",
                        "stack_status": "CREATE_IN_PROGRESS",
                    }
                ]
            }

            class mock_response(object):
                def __init__(self, status_code, _content):
                    self.status_code = status_code
                    self._content = _content

            mock_response_obj = mock_response(201, json.dumps(mock_heat_res))
            mock_client.return_value = mock_response_obj
            shell.main([self.template_file, self.template_type, "--deploy"])
            args, kwargs = mock_client.call_args
            self.assertEqual(kwargs["stack_name"],
                             'heat_tosca_helloworld_abcXXX')
            self.assertEqual(kwargs["template"], data)
        except Exception as e:
            self.fail(e)
