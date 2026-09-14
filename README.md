# SmartBranch 360

Secure branch-office network built in **Cisco Packet Tracer**, plus a small **Python** checker for the VLAN/IP plan.

Cisco Networking Essentials (NetAcad) — NIIT University, 2026.

## What it does

- Employees (VLAN 10) reach the internal server and the internet  
- Guests (VLAN 20, Wi-Fi) reach **internet only**  
- Server (VLAN 30) at `10.10.30.10` with DNS/HTTP  
- Management (VLAN 99) is the only VLAN allowed to **SSH** to the router  
- Five lab faults documented and repaired  
- `check_plan.py` validates a YAML addressing plan  

## Topology

```
Cloud / ISP (fake internet 8.8.8.8)
        |
       R1   NAT + DHCP + ACL + SSH
        |   802.1Q trunk (10,20,30,99)
       SW1 -------- trunk -------- SW2
        |                           |
   SRV1, PC-M1, PC-E*          PC-E*, AP1 ))) guests
```

R1 is the **office** router. The extra ISP router only simulates the internet because Packet Tracer Cloud does not answer `ping 8.8.8.8`.

## Addressing

| VLAN | Name | Subnet | Gateway |
|------|------|--------|---------|
| 10 | EMPLOYEES | 10.10.10.0/24 | 10.10.10.1 |
| 20 | GUESTS | 10.10.20.0/24 | 10.10.20.1 |
| 30 | SERVER | 10.10.30.0/24 | 10.10.30.1 |
| 99 | MGMT | 10.10.99.0/24 | 10.10.99.1 |

## Repo layout

```
python_checker/
  check_plan.py
  requirements.yaml      # valid plan (PASS)
  bad_plan.yaml          # broken plan (FAIL)
packet_tracer/
  README.md              # how to open the .pkt (file may be in Releases if too large)
```

## Python checker

```bash
cd python_checker
pip install pyyaml
python check_plan.py requirements.yaml
python check_plan.py bad_plan.yaml
```

Checks: unique VLAN IDs, valid CIDR, gateway inside subnet, no overlapping subnets, required VLANs 10/20/30/99.

## Packet Tracer

Open the `.pkt` in Cisco Packet Tracer (NetAcad).  
Use **Realtime** mode. Guest PCs need the **WPC300N** wireless module.

## Skills

Cisco Packet Tracer · VLANs · 802.1Q trunks · Router-on-a-stick · DHCP · NAT · ACLs · SSH · DNS · Python

## Author

Kuldeep Yadav  
NIIT University
