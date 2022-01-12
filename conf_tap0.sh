#!/usr/bin/env bash

IP_ADDR="10.0.0.254/24"

ip tuntap add tap0 mode tap
ip add add ${IP_ADDR} dev tap0
ip link set tun0 up