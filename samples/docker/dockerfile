# Sample Dockerfile that can be use to build heat-translator docker container
FROM ubuntu

MAINTAINER Heat Translator contributors

RUN apt-get -y update && apt-get install -y \
    python-pip

RUN pip install heat-translator

COPY heat_translator_logging.conf /usr/local/lib/python2.7/dist-packages/translator/conf/

# Have some test TOSCA templates in my_tosca directory to copy to the container as an example.
# This is an optional step and can be removed.
COPY my_tosca /tmp/my_tosca

ENTRYPOINT ["heat-translator"]

