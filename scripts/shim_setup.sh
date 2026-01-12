#!/bin/bash
# HOST SHIM SETUP
# Solves Docker Macvlan isolation by creating a bridge interface on the host.

SHIM_IP="192.168.1.XXX/32" # Replace with your designated host shim IP
GW="br0"

# Create the shim interface
/usr/sbin/ip link add link $GW name shim0 type macvlan mode bridge
/usr/sbin/ip addr add $SHIM_IP dev shim0
/usr/sbin/ip link set shim0 up

# Routes for Container Access
# Add the specific IPs of your containers here
/usr/sbin/ip route add 192.168.1.140/32 dev shim0 # Postgres
/usr/sbin/ip route add 192.168.1.141/32 dev shim0 # ETL Worker