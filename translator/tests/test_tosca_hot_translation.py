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

from toscaparser.common.exception import ExceptionCollector
from toscaparser.common.exception import URLException
from toscaparser.common.exception import ValidationError
from toscaparser.tosca_template import ToscaTemplate
from toscaparser.utils.gettextutils import _
from translator.common.exception import UnsupportedTypeError
from translator.common.utils import TranslationUtils
from translator.hot.tosca_translator import TOSCATranslator
from translator.tests.base import TestCase


class ToscaHotTranslationTest(TestCase):

    def _test_successful_translation(self, tosca_file, hot_files, params=None):
        if not params:
            params = {}
        if not isinstance(hot_files, list):
            hot_files = [hot_files]
        diff = TranslationUtils.compare_tosca_translation_with_hot(tosca_file,
                                                                   hot_files,
                                                                   params)
        self.assertEqual({}, diff, '<difference> : ' +
                         json.dumps(diff, indent=4, separators=(', ', ': ')))

    def _test_failed_translation(self, tosca_file, hot_file, params, msg,
                                 msg_path, error_raise, error_collect):
        if msg_path:
            path = os.path.normpath(os.path.join(
                os.path.dirname(os.path.realpath(__file__)), tosca_file))
            msg = msg % path
        self.assertRaises(
            error_raise,
            TranslationUtils.compare_tosca_translation_with_hot,
            tosca_file, hot_file, params)
        ExceptionCollector.assertExceptionMessage(error_collect, msg)

    def test_hot_translate_single_server(self):
        tosca_file = '../tests/data/tosca_single_server.yaml'
        hot_file = '../tests/data/hot_output/hot_single_server.yaml'
        params = {'cpus': 1}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_single_server_with_defaults(self):
        tosca_file = \
            '../tests/data/tosca_single_server_with_defaults.yaml'

        hot_file_with_input = '../tests/data/hot_output/' \
            'hot_single_server_with_defaults_with_input.yaml'
        params1 = {'cpus': '1'}
        self._test_successful_translation(tosca_file, hot_file_with_input,
                                          params1)

        hot_file_without_input = '../tests/data/hot_output/' \
            'hot_single_server_with_defaults_without_input.yaml'
        params2 = {}
        self._test_successful_translation(tosca_file, hot_file_without_input,
                                          params2)

    def test_hot_translate_wordpress_single_instance(self):
        tosca_file = '../tests/data/tosca_single_instance_wordpress.yaml'
        hot_file = '../tests/data/hot_output/' \
            'hot_single_instance_wordpress.yaml'
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_helloworld(self):
        tosca_file = '../tests/data/tosca_helloworld.yaml'
        hot_file = '../tests/data/hot_output/hot_hello_world.yaml'
        self._test_successful_translation(tosca_file, hot_file)

    def test_hot_translate_host_assignment(self):
        tosca_file = '../tests/data/test_host_assignment.yaml'
        hot_file = '../tests/data/hot_output/hot_host_assignment.yaml'
        self._test_successful_translation(tosca_file, hot_file)

    def test_hot_translate_elk(self):
        tosca_file = '../tests/data/tosca_elk.yaml'
        hot_file = '../tests/data/hot_output/hot_elk.yaml'
        params = {'github_url':
                  'http://github.com/paypal/rest-api-sample-app-nodejs.git',
                  'my_cpus': 4}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_nodejs_mongodb_two_instances(self):
        tosca_file = '../tests/data/tosca_nodejs_mongodb_two_instances.yaml'
        hot_file = '../tests/data/hot_output/' \
                   'hot_nodejs_mongodb_two_instances.yaml'
        params = {'github_url':
                  'http://github.com/paypal/rest-api-sample-app-nodejs.git',
                  'my_cpus': 4}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_blockstorage_with_attachment(self):
        tosca_file = '../tests/data/storage/' \
                     'tosca_blockstorage_with_attachment.yaml'
        hot_file = '../tests/data/hot_output/storage/' \
                   'hot_blockstorage_with_attachment.yaml'
        params = {'cpus': 1,
                  'storage_location': '/dev/vdc',
                  'storage_size': '2000 MB',
                  'storage_snapshot_id': 'ssid'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_blockstorage_with_custom_relationship_type(self):
        tosca_file = '../tests/data/storage/' \
                     'tosca_blockstorage_with_custom_relationship_type.yaml'
        hot_file = '../tests/data/hot_output/storage/' \
                   'hot_blockstorage_with_custom_relationship_type.yaml'
        params = {'cpus': 1,
                  'storage_location': '/dev/vdc',
                  'storage_size': '1 GB',
                  'storage_snapshot_id': 'ssid'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_blockstorage_with_relationship_template(self):
        tosca_file = '../tests/data/storage/' \
                     'tosca_blockstorage_with_relationship_template.yaml'
        hot_file = '../tests/data/hot_output/storage/' \
                   'hot_blockstorage_with_relationship_template.yaml'
        params = {'cpus': 1,
                  'storage_location': '/dev/vdc',
                  'storage_size': '1 GB'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_blockstorage_with_attachment_notation1(self):
        tosca_file = '../tests/data/storage/' \
                     'tosca_blockstorage_with_attachment_notation1.yaml'
        hot_file1 = '../tests/data/hot_output/storage/' \
                    'hot_blockstorage_with_attachment_notation1_alt1.yaml'
        hot_file2 = '../tests/data/hot_output/storage/' \
                    'hot_blockstorage_with_attachment_notation1_alt2.yaml'
        params = {'cpus': 1,
                  'storage_location': 'some_folder',
                  'storage_size': '1 GB',
                  'storage_snapshot_id': 'ssid'}

        try:
            self._test_successful_translation(tosca_file, hot_file1, params)
        except Exception:
            self._test_successful_translation(tosca_file, hot_file2, params)

    def test_hot_translate_blockstorage_with_attachment_notation2(self):
        tosca_file = '../tests/data/storage/' \
                     'tosca_blockstorage_with_attachment_notation2.yaml'
        hot_file1 = '../tests/data/hot_output/storage/' \
                    'hot_blockstorage_with_attachment_notation2_alt1.yaml'
        hot_file2 = '../tests/data/hot_output/storage/' \
                    'hot_blockstorage_with_attachment_notation2_alt2.yaml'
        params = {'cpus': 1,
                  'storage_location': '/dev/vdc',
                  'storage_size': '1 GB',
                  'storage_snapshot_id': 'ssid'}
        try:
            self._test_successful_translation(tosca_file, hot_file1, params)
        except Exception:
            self._test_successful_translation(tosca_file, hot_file2, params)

    def test_hot_translate_multiple_blockstorage_with_attachment(self):
        tosca_file = '../tests/data/storage/' \
                     'tosca_multiple_blockstorage_with_attachment.yaml'
        hot_file1 = '../tests/data/hot_output/storage/' \
                    'hot_multiple_blockstorage_with_attachment_alt1.yaml'
        hot_file2 = '../tests/data/hot_output/storage/' \
                    'hot_multiple_blockstorage_with_attachment_alt2.yaml'
        params = {'cpus': 1,
                  'storage_location': '/dev/vdc',
                  'storage_size': '1 GB',
                  'storage_snapshot_id': 'ssid'}
        try:
            self._test_successful_translation(tosca_file, hot_file1, params)
        except Exception:
            self._test_successful_translation(tosca_file, hot_file2, params)

    def test_hot_translate_multiple_blockstorage_w_multiple_attachment(self):
        tosca_file = '../tests/data/storage/' \
                     'tosca_multiple_blockstorage_w_multiple_attachment.yaml'
        hot_file = '../tests/data/hot_output/storage/' \
                   'hot_multiple_blockstorage_w_multiple_attachment.yaml'
        params = {'cpus': 1,
                  'storage_location1': '/dev/vdb',
                  'storage_location2': '/dev/vdc',
                  'storage_size': '1 GB',
                  'storage_snapshot_id': 'ssid'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_single_object_store(self):
        tosca_file = '../tests/data/storage/tosca_single_object_store.yaml'
        hot_file = '../tests/data/hot_output/hot_single_object_store.yaml'
        params = {'objectstore_name': 'myobjstore'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_one_server_one_network(self):
        tosca_file = '../tests/data/network/tosca_one_server_one_network.yaml'
        hot_file = '../tests/data/hot_output/network/' \
                   'hot_one_server_one_network.yaml'
        params = {'network_name': 'private_net'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_server_on_existing_network(self):
        tosca_file = '../tests/data/network/' \
                     'tosca_server_on_existing_network.yaml'
        hot_file = '../tests/data/hot_output/network/' \
                   'hot_server_on_existing_network.yaml'
        params = {'network_name': 'private_net'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_two_servers_one_network(self):
        tosca_file = '../tests/data/network/tosca_two_servers_one_network.yaml'
        hot_file = '../tests/data/hot_output/network/' \
                   'hot_two_servers_one_network.yaml'
        params = {'network_name': 'my_private_net',
                  'network_cidr': '10.0.0.0/24',
                  'network_start_ip': '10.0.0.100',
                  'network_end_ip': '10.0.0.150'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_one_server_three_networks(self):
        tosca_file = '../tests/data/network/' \
                     'tosca_one_server_three_networks.yaml'
        hot_file = '../tests/data/hot_output/network/' \
                   'hot_one_server_three_networks.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_software_component(self):
        tosca_file = '../tests/data/tosca_software_component.yaml'
        hot_file = '../tests/data/hot_output/hot_software_component.yaml'
        params = {'cpus': '1',
                  'download_url': 'http://www.software.com/download'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_software_component_multiple_hosts(self):
        tosca_file = '../tests/data/tosca_software_component'\
            '_multiple_hosts.yaml'
        hot_file = '../tests/data/hot_output/hot_software_component'\
            '_multiple_hosts.yaml'
        params = {'cpus': '1',
                  'download_url': 'http://www.software.com/download'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_web_application(self):
        tosca_file = '../tests/data/tosca_web_application.yaml'
        hot_file = '../tests/data/hot_output/hot_web_application.yaml'
        params = {'cpus': '2', 'context_root': 'my_web_app'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_template_with_url_import(self):
        tosca_file = '../tests/data/' \
                     'tosca_single_instance_wordpress_with_url_import.yaml'
        hot_file = '../tests/data/hot_output/' \
                   'hot_single_instance_wordpress.yaml'
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_template_by_url_with_local_import(self):
        tosca_file = 'https://raw.githubusercontent.com/openstack/' \
                     'heat-translator/master/translator/tests/data/' \
                     'tosca_single_instance_wordpress.yaml'
        hot_file = '../tests/data/hot_output/' \
                   'hot_single_instance_wordpress.yaml'
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_template_by_url_with_local_abspath_import(self):
        tosca_file = 'https://raw.githubusercontent.com/openstack/' \
                     'heat-translator/master/translator/tests/data/' \
                     'tosca_single_instance_wordpress_with_local_abspath' \
                     '_import.yaml'
        hot_file = '../tests/data/hot_output/' \
                   'hot_single_instance_wordpress.yaml'
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        expected_msg = _('Absolute file name "/tmp/wordpress.yaml" cannot be '
                         'used in a URL-based input template "https://raw.'
                         'githubusercontent.com/openstack/heat-translator/'
                         'master/translator/tests/data/tosca_single_instance_'
                         'wordpress_with_local_abspath_import.yaml".')
        msg_path = False
        self._test_failed_translation(tosca_file, hot_file, params,
                                      expected_msg, msg_path, ValidationError,
                                      ImportError)

    def test_hot_translate_template_by_url_with_url_import(self):
        tosca_url = 'https://raw.githubusercontent.com/openstack/' \
                    'heat-translator/master/translator/tests/data/' \
                    'tosca_single_instance_wordpress_with_url_import.yaml'
        hot_file = '../tests/data/hot_output/' \
                   'hot_single_instance_wordpress.yaml'
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        self._test_successful_translation(tosca_url, hot_file, params)

    def test_translate_hello_world_csar(self):
        tosca_file = '../tests/data/csar_hello_world.zip'
        hot_file = '../tests/data/hot_output/hot_hello_world.yaml'
        self._test_successful_translation(tosca_file, hot_file)

    def test_translate_single_instance_wordpress_csar(self):
        tosca_file = '../tests/data/csar_single_instance_wordpress.zip'
        hot_file = '../tests/data/hot_output/' \
                   'hot_single_instance_wordpress_from_csar.yaml'
        params = {'db_name': 'wordpress',
                  'db_user': 'wp_user',
                  'db_pwd': 'wp_pass',
                  'db_root_pwd': 'passw0rd',
                  'db_port': 3366,
                  'cpus': 8}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_translate_elk_csar_from_url(self):
        tosca_file = 'https://github.com/openstack/heat-translator/raw/' \
                     'master/translator/tests/data/csar_elk.zip'
        hot_file = '../tests/data/hot_output/hot_elk_from_csar.yaml'
        params = {'github_url':
                  'http://github.com/paypal/rest-api-sample-app-nodejs.git',
                  'my_cpus': 4}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_translate_csar_not_zip(self):
        tosca_file = '../tests/data/csar_not_zip.zip'
        hot_file = ''
        params = {}
        expected_msg = _('"%s" is not a valid zip file.')
        msg_path = True
        self._test_failed_translation(tosca_file, hot_file, params,
                                      expected_msg, msg_path, ValidationError,
                                      ValidationError)

    def test_translate_csar_metadata_not_yaml(self):
        tosca_file = '../tests/data/csar_metadata_not_yaml.zip'
        hot_file = ''
        params = {}
        expected_msg = _('The file "TOSCA-Metadata/TOSCA.meta" in the CSAR '
                         '"%s" does not contain valid YAML content.')
        msg_path = True
        self._test_failed_translation(tosca_file, hot_file, params,
                                      expected_msg, msg_path, ValidationError,
                                      ValidationError)

    def test_translate_csar_wrong_metadata_file(self):
        tosca_file = '../tests/data/csar_wrong_metadata_file.zip'
        hot_file = ''
        params = {}
        expected_msg = _('"%s" is not a valid CSAR as it does not contain the '
                         'required file "TOSCA.meta" in the folder '
                         '"TOSCA-Metadata".')
        msg_path = True
        self._test_failed_translation(tosca_file, hot_file, params,
                                      expected_msg, msg_path, ValidationError,
                                      ValidationError)

    def test_translate_csar_wordpress_invalid_import_path(self):
        tosca_file = '../tests/data/csar_wordpress_invalid_import_path.zip'
        hot_file = ''
        params = {}
        expected_msg = _('Import '
                         '"Invalid_import_path/wordpress.yaml" is not valid.')
        msg_path = False
        self._test_failed_translation(tosca_file, hot_file, params,
                                      expected_msg, msg_path, ValidationError,
                                      ImportError)

    def test_translate_csar_wordpress_invalid_script_url(self):
        tosca_file = '../tests/data/csar_wordpress_invalid_script_url.zip'
        hot_file = ''
        params = {}
        expected_msg = _('The resource at '
                         '"https://raw.githubusercontent.com/openstack/'
                         'heat-translator/master/translator/tests/data/'
                         'custom_types/wordpress1.yaml" cannot be accessed.')
        msg_path = False
        self._test_failed_translation(tosca_file, hot_file, params,
                                      expected_msg, msg_path, ValidationError,
                                      URLException)

    def test_hot_translate_flavor_image(self):
        tosca_file = '../tests/data/test_tosca_flavor_and_image.yaml'
        hot_file = '../tests/data/hot_output/hot_flavor_and_image.yaml'
        self._test_successful_translation(tosca_file, hot_file)

    def test_hot_translate_flavor_image_params(self):
        tosca_file = '../tests/data/test_tosca_flavor_and_image.yaml'
        hot_file = '../tests/data/hot_output/hot_flavor_and_image_params.yaml'
        params = {'key_name': 'paramkey'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_custom_type(self):
        tosca_file = '../tests/data/test_tosca_custom_type.yaml'
        hot_file = '../tests/data/hot_output/' \
            'hot_custom_type.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_custom_type_with_override(self):
        tosca_file = '../tests/data/test_tosca_custom_type_with_override.yaml'
        hot_file = '../tests/data/hot_output/' \
            'hot_custom_type_with_override.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_custom_type_with_param_override(self):
        tosca_file = '../tests/data/test_tosca_custom_type_with_override.yaml'
        hot_file = '../tests/data/hot_output/' \
            'hot_custom_type_with_param_override.yaml'
        params = {'install_path': '/home/custom/from/cli'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_artifact(self):
        tosca_file = '../tests/data/test_tosca_artifact.yaml'
        hot_file = '../tests/data/hot_output/' \
            'hot_artifact.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_without_tosca_os_version(self):
        tosca_file = '../tests/data/' \
            'test_single_server_without_optional_version_prop.yaml'
        hot_file = '../tests/data/hot_output/' \
            'hot_single_server_without_tosca_os_version.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_helloworld_with_userkey(self):
        tosca_file = '../tests/data/tosca_helloworld.yaml'
        hot_file = '../tests/data/hot_output/hot_hello_world_userkey.yaml'
        params = {'key_name': 'userkey'}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_custom_networks_nodes_inline(self):
        tosca_file = '../tests/data/network/' \
                     'test_tosca_custom_network_nodes_inline.yaml'
        hot_file = '../tests/data/hot_output/network/' \
                   'hot_custom_network_nodes.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_custom_networks_nodes_imports(self):
        tosca_file = '../tests/data/network/' \
                     'test_tosca_custom_network_nodes_imports.yaml'
        hot_file = '../tests/data/hot_output/network/' \
                   'hot_custom_network_nodes.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_nfv_sample(self):
        tosca_file = '../tests/data/nfv/test_tosca_nfv_sample.yaml'
        hot_file = '../tests/data/hot_output/nfv/hot_nfv_sample.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_placement_policy_default_affinity(self):
        tosca_file = '../tests/data/policies/tosca_policies.yaml'
        hot_file = '../tests/data/hot_output/policies/hot_policies.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_placement_policy_affinity(self):
        tosca_file = ('../tests/data/nfv/'
                      'tosca_placement_policy_affinity.yaml')
        hot_file = '../tests/data/hot_output/policies/hot_policies.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_placement_policy_anti_affinity(self):
        tosca_file = ('../tests/data/nfv/'
                      'tosca_placement_policy_anti_affinity.yaml')
        hot_file = ('../tests/data/hot_output/nfv/'
                    'hot_policy_anti_affinity.yaml')
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_placement_policy_soft_affinity(self):
        tosca_file = ('../tests/data/nfv/'
                      'tosca_placement_policy_soft_affinity.yaml')
        hot_file = ('../tests/data/hot_output/nfv/'
                    'hot_policy_soft_affinity.yaml')
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_script_types(self):
        tosca_file = '../tests/data/interfaces/test_tosca_script_types.yaml'
        hot_file = '../tests/data/hot_output/hot_script_types.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_interface_on_compute(self):
        tosca_file = '../tests/data/interfaces/' \
                     'test_tosca_interface_on_compute.yaml'
        hot_file = '../tests/data/hot_output/interfaces/' \
                   'hot_interface_on_compute.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_get_functions_semantic(self):
        tosca_file = '../tests/data/test_tosca_get_functions_semantic.yaml'
        hot_file = '../tests/data/hot_output/hot_get_functions_semantic.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_exchange_public_ssh_key(self):
        tosca_file = '../tests/data/tosca_exchange_public_ssh_key.yaml'
        hot_file = '../tests/data/hot_output/hot_exchange_public_ssh_key.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_scaling_policy(self):
        tosca_file = '../tests/data/autoscaling/tosca_autoscaling.yaml'
        hot_files = [
            '../tests/data/hot_output/autoscaling/hot_autoscaling.yaml',
            '../tests/data/hot_output/autoscaling/asg_res.yaml',
            ]
        params = {}
        self._test_successful_translation(tosca_file, hot_files, params)

    def test_translate_unsupported_tosca_type(self):
        tosca_file = '../tests/data/test_tosca_unsupported_type.yaml'
        tosca_tpl = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), tosca_file))
        params = {}
        expected_msg = _('Type "tosca.nodes.LoadBalancer" is valid TOSCA '
                         'type but translation support is not yet available.')
        tosca = ToscaTemplate(tosca_tpl, params, True)
        err = self.assertRaises(UnsupportedTypeError,
                                TOSCATranslator(tosca, params)
                                .translate)
        self.assertEqual(expected_msg, err.__str__())

    def test_translate_unsupported_tosca_policy_type(self):
        tosca_file = ('../tests/data/nfv/'
                      'test_tosca_unsupported_policy_type.yaml')
        tosca_tpl = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), tosca_file))
        params = {}
        expected_msg = _('Type "tosca.policies.tacker.ABC" is valid TOSCA '
                         'type but translation support is not yet available.')
        tosca = ToscaTemplate(tosca_tpl, params, True)
        err = self.assertRaises(UnsupportedTypeError,
                                TOSCATranslator(tosca, params)
                                .translate)
        self.assertEqual(expected_msg, err.__str__())

    def test_hot_translate_cluster_scaling_policy(self):
        tosca_file = '../tests/data/autoscaling/tosca_cluster_autoscaling.yaml'
        hot_file = '../tests/data/hot_output/autoscaling/' \
                   'hot_cluster_autoscaling.yaml'
        params = {}
        self._test_successful_translation(tosca_file, hot_file, params)

    def test_hot_translate_nfv_scaling(self):
        tosca_file = '../tests/data/nfv/test_tosca_nfv_autoscaling.yaml'
        hot_files = [
            '../tests/data/hot_output/nfv/hot_tosca_nfv_autoscaling.yaml',
            '../tests/data/hot_output/nfv/SP1_res.yaml',
            ]
        params = {}
        self._test_successful_translation(tosca_file, hot_files, params)

    def test_hot_translate_nfv_scaling_with_params(self):
        tosca_file = '../tests/data/nfv/test_tosca_nfv_autoscaling_with_' \
                     'params.yaml'
        hot_files = [
            '../tests/data/hot_output/nfv/hot_tosca_nfv_autoscaling_with_'
            'param.yaml',
            '../tests/data/hot_output/nfv/SP_res.yaml',
        ]
        params = {'image_name': 'cirros-0.3.5-x86_64-disk',
                  'flavor': 'm1.tiny'}
        self._test_successful_translation(tosca_file, hot_files, params)

    def test_hot_translate_mon_scaling_policy(self):
        tosca_file = '../tests/data/monitoring/tosca_monitoring_scaling.yaml'
        hot_files = [
            '../tests/data/hot_output/monitoring/hot_monitoring_scaling.yaml',
            '../tests/data/hot_output/monitoring/asg_res.yaml',
        ]
        params = {}
        self._test_successful_translation(tosca_file, hot_files, params)

    def test_hot_translate_reservation_policy(self):
        tosca_file = '../tests/data/reservation/tosca-vnfd-reservation-id.yaml'
        hot_files = [
            '../tests/data/hot_output/reservation/'
            'hot_reservation_scaling.yaml',
            '../tests/data/hot_output/reservation/SP_RSV_res.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})
