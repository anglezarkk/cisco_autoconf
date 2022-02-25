# Cisco autoconf
A project created for the 4TC-NAS class.

It allows to create a whole network, consiting in ASBR routers, CE routers and core routers, with MPLS/BGP/VPN setup, 
from a very simple json file, which briefly describes the network architecture.

### Features
- Automatic allocation of subnets
- Automatic peering between ASBRs and CEs
- Automatic setup of VRFs
- Complex VPN setups possibles (see example)

### Installation
Requirements : 
- Python 3.10 (older versions not tested)

Install dependencies with the following command :
``$ pip3 install -r requirements.txt``

### Usage

``$ python main.py --topology [path to json]``

### Example of a valid JSON description
```json
{
  "asn_core": 400,
  "internal_auto_allocation_prefix": "10.0.0.0/8",
  "border_auto_allocation_prefix": "172.16.0.0/16",
  "customer_auto_allocation_prefix": "192.168.0.0/16",
  "core_routers": {
    "R1": {
      "ip_loopback": "1.1.1.1",
      "Ethernet1/0": "R2",
      "Ethernet1/3": "R3",
      "FastEthernet0/0": "PE1"
    },
    "R2": {
      "ip_loopback": "2.2.2.2",
      "Ethernet1/0": "R1",
      "Ethernet1/1": "R4",
      "FastEthernet0/0": "PE2"
    },
    "R3": {
      "ip_loopback": "3.3.3.3",
      "Ethernet1/2": "R1",
      "Ethernet1/3": "R4",
      "FastEthernet0/1": "PE1"
    },
    "R4": {
      "ip_loopback": "4.4.4.4",
      "FastEthernet0/1": "PE2",
      "Ethernet1/1": "R2",
      "Ethernet1/2": "R3"
    }
  },
  "as_border_routers": {
    "PE1": {
      "ip_loopback": "9.9.9.9",
      "Ethernet1/0": "CE1",
      "Ethernet1/1": "CE3",
      "FastEthernet0/0": "R1",
      "FastEthernet0/1": "R3"
    },
    "PE2": {
      "ip_loopback": "10.10.10.10",
      "Ethernet1/0": "CE2",
      "Ethernet1/1": "CE4",
      "Ethernet1/2": "CE5",
      "FastEthernet0/0": "R2",
      "FastEthernet0/1": "R4"
    }
  },
  "customer_routers": {
    "CE1": {
      "ip_loopback": "1.0.0.1",
      "FastEthernet0/0": "PE1",
      "FastEthernet0/1": "lan",
      "vpn": [
        1, 2, 3
      ]
    },
    "CE2": {
      "ip_loopback": "1.0.0.2",
      "FastEthernet0/0": "PE2",
      "FastEthernet0/1": "lan",
      "vpn": [
        1
      ]
    },
    "CE3": {
      "ip_loopback": "2.0.0.1",
      "FastEthernet0/0": "PE1",
      "FastEthernet0/1": "lan",
      "vpn": [
        2
      ]
    },
    "CE4": {
      "ip_loopback": "2.0.0.2",
      "FastEthernet0/0": "PE2",
      "FastEthernet0/1": "lan",
      "vpn": [
        3
      ]
    },
    "CE5": {
      "ip_loopback": "2.0.0.3",
      "FastEthernet0/0": "PE2",
      "FastEthernet0/1": "lan",
      "vpn": [
        3
      ]
    }
  },
  "bgp_auto_peering_asbr": true,
  "mpls_bgp_vpn": true
}
```