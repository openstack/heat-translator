#!/bin/bash
test -d /root/.ssh || mkdir /root/.ssh
echo "$public_key" >> /root/.ssh/authorized_keys
