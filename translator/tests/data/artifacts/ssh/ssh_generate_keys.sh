#!/bin/bash
test -d /root/.ssh || mkdir /root/.ssh
test -f /root/.ssh/id_rsa.pub || ssh-keygen -q -t rsa -N "" -f /root/.ssh/id_rsa
cat /root/.ssh/id_rsa.pub > ${heat_outputs_path}.public_key
