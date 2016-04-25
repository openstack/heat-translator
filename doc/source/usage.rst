=====
Usage
=====

Use Heat-Translator with OpenStackClient (OSC)
----------------------------------------------
Assuming that OpenStackClient (OSC) is available in your environment, you can easily install Heat-Translator to use with OSC by following three steps::

    git clone https://github.com/openstack/heat-translator
    cd heat-translator
    sudo python setup.py install

Alternatively, you can install a particular release of Heat-Translator as available at https://pypi.python.org/pypi/heat-translator.

Once installation is complete, Heat-Translator is ready to use. Currently you can use it in following three ways.

Translate and get output on command line. For example: ::

    openstack translate template --template-file /home/openstack/heat-translator/translator/tests/data/tosca_helloworld.yaml --template-type tosca

Translate and save output of translated file to a desired destination. For example: ::

    openstack translate template --template-file /home/openstack/heat-translator/translator/tests/data/tosca_helloworld.yaml --template-type tosca --output-file /tmp/hot_hello_world.yaml

Do not translate but only validate template file. For example: ::

    openstack translate template --template-file /home/openstack/heat-translator/translator/tests/data/tosca_helloworld.yaml --template-type tosca --validate-only=true

You can learn more about available options by running following help command::

    openstack help translate template


Use Heat-Translator on its own
------------------------------
Heat-Translator can be used without any specific OpenStack environment set up as below::

    git clone https://github.com/openstack/heat-translator
    python heat_translator.py --template-file==<path to the YAML template> --template-type=<type of template e.g. tosca> --parameters="purpose=test"

The heat_translator.py test program is at the root level of the project. The program has currently tested with TOSCA templates.
It requires two arguments::

1. Path to the file that needs to be translated. The file, flat yaml template or CSAR, can be specified as a local file in your
system or via URL.
2. Type of translation (e.g. tosca)

For example, a TOSCA hello world template can be translated by running the following command from the project location::

    python heat_translator.py --template-file=translator/tests/data/tosca_helloworld.yaml --template-type=tosca

This should produce a translated Heat Orchestration Template on the command line. The translated content can be saved to a desired file by setting --output-file=<path>.
For example: ::

    python heat_translator.py --template-file=translator/tests/data/tosca_helloworld.yaml --template-type=tosca --output-file=/tmp/hot_helloworld.yaml

An optional argument can be provided to handle user inputs parameters. Also, a template file can only be validated instead of translation by using --validate-only=true
optional argument. The command below shows an example usage::

    python heat_translator.py --template-file==<path to the YAML template> --template-type=<type of template e.g. tosca> --validate-only=true

Alternatively, you can install a particular release of Heat-Translator as available at https://pypi.python.org/pypi/heat-translator.
In this case, you can simply run translation via CLI entry point::
    heat-translator --template-file=translator/tests/data/tosca_helloworld.yaml --template-type=tosca

Things To Consider
------------------
* When use Heat-Translator in an OpenStack environment, please ensure that you have one or more preferred flavors and images available in your OpenStack
  environment. To find an appropriate flavor and image, that meets constraints defined in the TOSCA template for the HOST and OS capabilities of TOSCA Compute node,
  the Heat-Translator project first runs a query against Nova flavors and Glance images. During the query call, it uses the metadata of flavors and images.
  If call to Nova or Glance can not be made or no flavor or image is found, the Heat-Translator project will set flavor and image from a pre-defined set of values (as listed in /home/openstack/heat-translator/translator/hot/tosca/tosca_compute.py)
  with the best possible match to the constraints defined in the TOSCA template.
* The ``key_name`` property of Nova server is irrelevant to the TOSCA specification and can not be used in TOSCA template. In order to use it in
  the translated templates, the user must provide it via parameters, and the heat-translator will set it to all resources of ``OS::Nova::Server`` type.
* Since properties of TOSCA Compute OS and HOST capabilities are optional, the user should make sure that either they set these properties correctly
  in the TOSCA template or provide them via CLI parameters in order to find best match of flavor and image.
* The ``flavor`` and ``image`` properties of ``OS::Nova::Server`` resource is irrelevant to the TOSCA specification and can not be used in the TOSCA
  template as such. Heat-Translator sets these properties in the translated template based on constraints defined per TOSCA Compute OS and HOST
  capabilities. However, user may required to use these properties in template in certain circumstances, so in that case, TOSCA Compute can be extended
  with these properties and later used in the node template. For a good example, refer to the ``translator/tests/data/test_tosca_flavor_and_image.yaml`` test
  template.

