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

import os
import shutil
import tempfile

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
