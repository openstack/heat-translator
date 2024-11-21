#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import os
import testtools
from unittest import mock

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import toscaparser.utils.yamlparser

import toscaparser
from toscaparser.common.exception import ExceptionCollector
from toscaparser.common.exception import URLException
from toscaparser.common.exception import ValidationError
from toscaparser.tosca_template import ToscaTemplate
from toscaparser.utils.gettextutils import _
from translator.common.utils import CompareUtils
from translator.common.utils import YamlUtils
from translator.osc.v1.tests import fakes
from translator.osc.v1 import translate
from translator.tests import utils


class TestTranslateTemplate(testtools.TestCase):

    def setUp(self):
        super(TestTranslateTemplate, self).setUp()
        self.app = fakes.FakeApp()
        self.app.client_manager = fakes.FakeClientManager()
        self.app.client_manager.translator = None
        self.cmd = translate.TranslateTemplate(self.app, None)

    def check_parser(self, cmd, args, verify_args):
        cmd_parser = cmd.get_parser('check_parser')
        try:
            parsed_args = cmd_parser.parse_args(args)
        except SystemExit:
            raise Exception("Argument parse failed")
        for av in verify_args:
            attr, value = av
            if attr:
                self.assertIn(attr, parsed_args)
                self.assertEqual(getattr(parsed_args, attr), value)
        return parsed_args

    def _check_error(self, tosca_file, hot_file, params, assert_error,
                     expected_msg, c_error):
        arglist = ["--template-file", tosca_file,
                   "--template-type", "tosca"]
        parsed_args = self.check_parser(self.cmd, arglist, [])
        parsed_args.parameter = params
        self.assertRaises(assert_error, self.cmd.take_action,
                          parsed_args)
        ExceptionCollector.assertExceptionMessage(c_error, expected_msg)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def _check_success(self, tosca_file, hot_file, params, mock_stdout):
        arglist = ["--template-file", tosca_file,
                   "--template-type", "tosca"]
        parsed_args = self.check_parser(self.cmd, arglist, [])
        parsed_args.parameter = params
        self.cmd.take_action(parsed_args)
        expected_output = YamlUtils.get_dict(hot_file)
        mock_stdout_yaml = "\n".join(mock_stdout.getvalue().split("\n"))
        actual_output = toscaparser.utils.yamlparser.simple_parse(
            mock_stdout_yaml)
        self.assertEqual({}, CompareUtils.diff_dicts(
            actual_output, expected_output))

    def test_osc_translate_single_server(self):
        tosca_file = utils.test_sample("tosca_single_server.yaml")

        hot_file = utils.test_sample("hot_output/hot_single_server.yaml")

        params = {'cpus': 1}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_single_server_defaults_with_input(self):
        tosca_file = utils.test_sample(
            "tosca_single_server_with_defaults.yaml")

        hot_file = utils.test_sample(
            "hot_output/hot_single_server_with_defaults_with_input.yaml")

        params = {'cpus': '1'}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_single_server_defaults_without_input(self):
        tosca_file = utils.test_sample(
            "tosca_single_server_with_defaults.yaml")

        hot_file = utils.test_sample(
            "hot_output/hot_single_server_with_defaults_without_input.yaml")

        self._check_success(tosca_file, hot_file, {})

    def test_osc_translate_wordpress_single_instance(self):
        tosca_file = utils.test_sample(
            "tosca_single_instance_wordpress.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_single_instance_wordpress.yaml")
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_helloworld(self):
        tosca_file = utils.test_sample(
            "tosca_helloworld.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_hello_world.yaml")
        self._check_success(tosca_file, hot_file, {})

    def test_osc_translate_host_assignment(self):
        tosca_file = utils.test_sample(
            "test_host_assignment.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_host_assignment.yaml")
        self._check_success(tosca_file, hot_file, {})

    def test_osc_translate_elk(self):
        tosca_file = utils.test_sample(
            "tosca_elk.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_elk.yaml")
        params = {'github_url':
                  'http://github.com/paypal/rest-api-sample-app-nodejs.git',
                  'my_cpus': 4}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_nodejs_mongodb_two_instances(self):
        tosca_file = utils.test_sample(
            "tosca_nodejs_mongodb_two_instances.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_nodejs_mongodb_two_instances.yaml")
        params = {'github_url':
                  'http://github.com/paypal/rest-api-sample-app-nodejs.git',
                  'my_cpus': 4}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_blockstorage_with_attachment(self):
        tosca_file = utils.test_sample(
            "storage/tosca_blockstorage_with_attachment.yaml")
        hot_file = utils.test_sample(
            "hot_output/storage/hot_blockstorage_with_attachment.yaml")
        params = {'cpus': 1,
                  'storage_location': '/dev/vdc',
                  'storage_size': '2000 MB',
                  'storage_snapshot_id': 'ssid'}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_blockstorage_with_custom_relationship_type(self):
        tosca_file = utils.test_sample(
            "storage/tosca_blockstorage_with_custom_relationship_type.yaml")
        hot_file = utils.test_sample(
            "hot_output/storage/"
            "hot_blockstorage_with_custom_relationship_type.yaml")
        params = {'cpus': 1,
                  'storage_location': '/dev/vdc',
                  'storage_size': '1 GB',
                  'storage_snapshot_id': 'ssid'}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_blockstorage_with_relationship_template(self):
        tosca_file = utils.test_sample(
            "storage/" +
            "tosca_blockstorage_with_relationship_template.yaml")
        hot_file = utils.test_sample(
            "hot_output/storage/" +
            "hot_blockstorage_with_relationship_template.yaml")
        params = {'cpus': 1,
                  'storage_location': '/dev/vdc',
                  'storage_size': '1 GB'}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_blockstorage_with_attachment_notation1(self):
        tosca_file = utils.test_sample(
            "storage/" +
            "tosca_blockstorage_with_attachment_notation1.yaml")
        hot_file1 = utils.test_sample(
            "hot_output/storage/" +
            "hot_blockstorage_with_attachment_notation1_alt1.yaml")
        hot_file2 = utils.test_sample(
            "hot_output/storage/" +
            "hot_blockstorage_with_attachment_notation1_alt2.yaml")
        params = {'cpus': 1,
                  'storage_location': 'some_folder',
                  'storage_size': '1 GB',
                  'storage_snapshot_id': 'ssid'}
        try:
            self._check_success(tosca_file, hot_file1, params)
        except Exception:
            self._check_success(tosca_file, hot_file2, params)

    def test_osc_translate_blockstorage_with_attachment_notation2(self):
        tosca_file = utils.test_sample(
            "storage/" +
            "tosca_blockstorage_with_attachment_notation2.yaml")
        hot_file1 = utils.test_sample(
            "hot_output/storage/" +
            "hot_blockstorage_with_attachment_notation2_alt1.yaml")
        hot_file2 = utils.test_sample(
            "hot_output/storage/" +
            "hot_blockstorage_with_attachment_notation2_alt2.yaml")
        params = {'cpus': 1,
                  'storage_location': '/dev/vdc',
                  'storage_size': '1 GB',
                  'storage_snapshot_id': 'ssid'}
        try:
            self._check_success(tosca_file, hot_file1, params)
        except Exception:
            self._check_success(tosca_file, hot_file2, params)

    def test_osc_translate_multiple_blockstorage_with_attachment(self):
        tosca_file = utils.test_sample(
            "storage/" +
            "tosca_multiple_blockstorage_with_attachment.yaml")
        hot_file1 = utils.test_sample(
            "hot_output/storage/" +
            "hot_multiple_blockstorage_with_attachment_alt1.yaml")
        hot_file2 = utils.test_sample(
            "hot_output/storage/" +
            "hot_multiple_blockstorage_with_attachment_alt2.yaml")
        params = {'cpus': 1,
                  'storage_location': '/dev/vdc',
                  'storage_size': '1 GB',
                  'storage_snapshot_id': 'ssid'}
        try:
            self._check_success(tosca_file, hot_file1, params)
        except Exception:
            self._check_success(tosca_file, hot_file2, params)

    def test_osc_translate_single_object_store(self):
        tosca_file = utils.test_sample(
            "storage/tosca_single_object_store.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_single_object_store.yaml")
        params = {'objectstore_name': 'myobjstore'}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_one_server_one_network(self):
        tosca_file = utils.test_sample(
            "network/tosca_one_server_one_network.yaml")
        hot_file = utils.test_sample(
            "hot_output/network/" +
            "hot_one_server_one_network.yaml")
        params = {'network_name': 'private_net'}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_server_on_existing_network(self):
        tosca_file = utils.test_sample(
            "network/" +
            "tosca_server_on_existing_network.yaml")
        hot_file = utils.test_sample(
            "hot_output/network/" +
            "hot_server_on_existing_network.yaml")
        params = {'network_name': 'private_net'}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_two_servers_one_network(self):
        tosca_file = utils.test_sample(
            "network/tosca_two_servers_one_network.yaml")
        hot_file = utils.test_sample(
            "hot_output/network/" +
            "hot_two_servers_one_network.yaml")
        params = {'network_name': 'my_private_net',
                  'network_cidr': '10.0.0.0/24',
                  'network_start_ip': '10.0.0.100',
                  'network_end_ip': '10.0.0.150'}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_one_server_three_networks(self):
        tosca_file = utils.test_sample(
            "network/" +
            "tosca_one_server_three_networks.yaml")
        hot_file = utils.test_sample(
            "hot_output/network/" +
            "hot_one_server_three_networks.yaml")
        self._check_success(tosca_file, hot_file, {})

    def test_osc_translate_software_component(self):
        tosca_file = utils.test_sample("tosca_software_component.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_software_component.yaml")
        params = {'cpus': '1',
                  'download_url': 'http://www.software.com/download'}
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_web_application(self):
        tosca_file = utils.test_sample("tosca_web_application.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_web_application.yaml")
        params = {'cpus': '2', 'context_root': 'my_web_app'}
        self._check_success(tosca_file, hot_file, params)

    @mock.patch.object(translate.ToscaTemplate, '_tpl_imports')
    def test_osc_translate_template_with_url_import(self, mock_tpl_imports):
        tosca_file = utils.test_sample(
            "tosca_single_instance_wordpress_with_url_import.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_single_instance_wordpress.yaml")
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        import_file_path = utils.test_sample(
            "custom_types/wordpress.yaml")
        mock_tpl_imports.return_value = [import_file_path]
        self._check_success(tosca_file, hot_file, params)

    @mock.patch.object(translate, 'ToscaTemplate')
    def test_osc_translate_template_by_url_with_local_import(
        self, mock_tosca_template):
        tosca_file = "https://example.com/tosca_single_instance_wordpress.yaml"
        hot_file = utils.test_sample(
            "hot_output/hot_single_instance_wordpress.yaml")
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        file_path = utils.test_sample("tosca_single_instance_wordpress.yaml")
        mock_tosca_template.return_value = ToscaTemplate(
            file_path, params, True)
        self._check_success(tosca_file, hot_file, params)

    @mock.patch.object(toscaparser.utils.urlutils.UrlUtils, 'validate_url')
    @mock.patch.object(os.path, 'isfile')
    @mock.patch.object(ToscaTemplate, '_get_path')
    def test_osc_translate_template_by_url_with_local_abspath_import(
        self, mock_get_path, mock_isfile, mock_validate_url):
        tosca_file = ("https://example.com/tosca_single_instance_wordpress_"
                      "with_local_abspath_import.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_single_instance_wordpress.yaml")
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        file_path = utils.test_sample(
            'tosca_single_instance_wordpress_with_local_abspath_import.yaml')
        mock_get_path.return_value = file_path
        mock_isfile.return_value = True
        mock_validate_url.side_effect = [False, True, False, True]

        expected_msg = ('Absolute file name "/tmp/wordpress.yaml" cannot be '
                        f'used in a URL-based input template "{file_path}".')
        self._check_error(tosca_file, hot_file, params, ValidationError,
                          expected_msg, ImportError)

    @mock.patch.object(translate.ToscaTemplate, '_tpl_imports')
    @mock.patch.object(translate, 'ToscaTemplate')
    def test_osc_translate_template_by_url_with_url_import(
        self, mock_tosca_template, mock_tpl_imports):
        tosca_url = ("https://example.com/tosca_single_instance_wordpress_"
                     "with_url_import.yaml")
        hot_file = utils.test_sample(
            "hot_output/hot_single_instance_wordpress.yaml")
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        file_path = utils.test_sample(
            "tosca_single_instance_wordpress_with_url_import.yaml")
        import_file_path = utils.test_sample("custom_types/wordpress.yaml")
        mock_tpl_imports.return_value = [import_file_path]
        mock_tosca_template.return_value = ToscaTemplate(
            file_path, params, True)
        self._check_success(tosca_url, hot_file, params)

    def test_osc_translate_hello_world_csar(self):
        tosca_file = utils.test_sample("csar_hello_world.zip")
        hot_file = utils.test_sample(
            "hot_output/hot_hello_world.yaml")
        self._check_success(tosca_file, hot_file, {})

    def test_osc_single_instance_wordpress_csar(self):
        tosca_file = utils.test_sample(
            "csar_single_instance_wordpress.zip")
        hot_file = utils.test_sample(
            "hot_output/" +
            "hot_single_instance_wordpress_from_csar.yaml")
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        self._check_success(tosca_file, hot_file, params)

    @mock.patch.object(translate, 'ToscaTemplate')
    def test_osc_translate_elk_csar_from_url(
        self, mock_tosca_template):
        tosca_file = "https://example.com/csar_elk.zip"
        hot_file = utils.test_sample("hot_output/hot_elk_from_csar.yaml")
        params = {'github_url':
                  'http://github.com/paypal/rest-api-sample-app-nodejs.git',
                  'my_cpus': 4}
        zip_file_path = utils.test_sample("csar_elk.zip")
        mock_tosca_template.return_value = ToscaTemplate(
            zip_file_path, params, True)
        self._check_success(tosca_file, hot_file, params)

    def test_osc_translate_csar_not_zip(self):
        tosca_file = utils.test_sample("csar_not_zip.zip")
        hot_file = ''
        expected_msg = _('"%s" is not a valid zip file.') % tosca_file
        self._check_error(tosca_file, hot_file, {}, ValidationError,
                          expected_msg, ValidationError)

    def test_osc_translate_csar_metadata_not_yaml(self):
        tosca_file = utils.test_sample("csar_metadata_not_yaml.zip")
        hot_file = ''
        expected_msg = _('The file "TOSCA-Metadata/TOSCA.meta" in the CSAR '
                         '"%s" does not contain valid YAML'
                         ' content.') % tosca_file
        self._check_error(tosca_file, hot_file, {}, ValidationError,
                          expected_msg, ValidationError)

    def test_osc_translate_csar_wrong_metadata_file(self):
        tosca_file = utils.test_sample("csar_wrong_metadata_file.zip")
        hot_file = ''

        expected_msg = _('"%s" is not a valid CSAR as it does not contain the '
                         'required file "TOSCA.meta" in the folder '
                         '"TOSCA-Metadata".') % tosca_file
        self._check_error(tosca_file, hot_file, {}, ValidationError,
                          expected_msg, ValidationError)

    def test_osc_translate_csar_wordpress_invalid_import_path(self):
        tosca_file = utils.test_sample(
            "csar_wordpress_invalid_import_path.zip")
        hot_file = ''
        expected_msg = _('Import '
                         '"Invalid_import_path/wordpress.yaml" is not valid.')
        self._check_error(tosca_file, hot_file, {}, ValidationError,
                          expected_msg, ImportError)

    def test_osc_translate_csar_wordpress_invalid_script_url(self):
        tosca_file = utils.test_sample(
            "csar_wordpress_invalid_script_url.zip")
        hot_file = ''
        expected_msg = _('The resource at '
                         '"https://raw.githubusercontent.com/openstack/'
                         'heat-translator/master/translator/tests/data/'
                         'custom_types/wordpress1.yaml" cannot be accessed.')
        self._check_error(tosca_file, hot_file, {}, ValidationError,
                          expected_msg, URLException)
