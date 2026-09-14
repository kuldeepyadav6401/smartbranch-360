"""
SmartBranch 360 - VLAN / IP plan checker
----------------------------------------
Reads a YAML plan and reports likely configuration mistakes.

Run (from this folder):
    pip install pyyaml
    python check_plan.py requirements.yaml
    python check_plan.py bad_plan.yaml
"""

import sys
import ipaddress

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is not installed. Run:  pip install pyyaml")
    sys.exit(1)


def load_plan(path):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "vlans" not in data:
        raise ValueError("YAML must contain a top-level 'vlans' list.")
    return data


def check_vlans(plan):
    errors = []
    warnings = []
    vlans = plan.get("vlans") or []
    required = set(plan.get("required_vlans") or [10, 20, 30, 99])

    seen_ids = {}
    seen_names = {}
    networks = []

    if not vlans:
        errors.append("No VLANs found in the plan.")
        return errors, warnings

    for v in vlans:
        vid = v.get("id")
        name = v.get("name")
        subnet = v.get("subnet")
        gateway = v.get("gateway")
        label = f"VLAN {vid} ({name})"

        # VLAN ID
        if vid is None:
            errors.append("A VLAN entry is missing 'id'.")
            continue
        if not isinstance(vid, int) or vid < 1 or vid > 4094:
            errors.append(f"{label}: VLAN id must be an integer 1-4094.")
        if vid in seen_ids:
            errors.append(
                f"ERROR: Duplicate VLAN id {vid}. "
                f"Also used by {seen_ids[vid]}. "
                "Symptom: devices land in the wrong broadcast domain. "
                "Fix: give each department a unique VLAN id."
            )
        else:
            seen_ids[vid] = name or str(vid)

        # Name
        if not name:
            warnings.append(f"VLAN {vid}: missing name.")
        elif name in seen_names:
            errors.append(f"Duplicate VLAN name '{name}' (ids {seen_names[name]} and {vid}).")
        else:
            seen_names[name] = vid

        # Subnet + gateway
        try:
            net = ipaddress.ip_network(subnet, strict=False)
        except Exception:
            errors.append(f"{label}: invalid subnet '{subnet}'. Use CIDR like 10.10.10.0/24.")
            continue

        for other_net, other_label in networks:
            if net.overlaps(other_net):
                errors.append(
                    f"ERROR: Overlapping subnets {net} ({label}) and "
                    f"{other_net} ({other_label}). "
                    "Symptom: routing and DHCP become unpredictable. "
                    "Fix: use one unique subnet per VLAN."
                )
        networks.append((net, label))

        if gateway is None:
            errors.append(f"{label}: missing gateway.")
            continue

        try:
            gw = ipaddress.ip_address(gateway)
        except Exception:
            errors.append(f"{label}: invalid gateway '{gateway}'.")
            continue

        if gw not in net:
            errors.append(
                f"ERROR: Gateway {gw} is not inside {net} ({label}). "
                "Symptom: PCs can ping the switch but not other VLANs or the internet. "
                "Fix: set default-router / gateway to an address in the same subnet "
                "(this design uses .1)."
            )
        else:
            if gw == net.network_address:
                errors.append(f"{label}: gateway {gw} is the network address, not a host.")
            if gw == net.broadcast_address:
                errors.append(f"{label}: gateway {gw} is the broadcast address, not a host.")

    found_ids = set(seen_ids.keys())
    missing = sorted(required - found_ids)
    if missing:
        errors.append(
            f"ERROR: Required VLAN(s) missing from the plan: {missing}. "
            "This project needs 10 EMPLOYEES, 20 GUESTS, 30 SERVER, 99 MGMT."
        )

    # Optional device IP checks
    vlan_by_id = {v.get("id"): v for v in vlans if v.get("id") is not None}
    for dev in plan.get("devices") or []:
        dname = dev.get("name", "?")
        dvlan = dev.get("vlan")
        dip = dev.get("ip")
        if dvlan not in vlan_by_id:
            errors.append(f"Device {dname}: VLAN {dvlan} is not defined in the plan.")
            continue
        try:
            net = ipaddress.ip_network(vlan_by_id[dvlan]["subnet"], strict=False)
            addr = ipaddress.ip_address(dip)
        except Exception:
            errors.append(f"Device {dname}: invalid IP '{dip}'.")
            continue
        if addr not in net:
            errors.append(
                f"ERROR: Device {dname} IP {dip} is not in VLAN {dvlan} subnet {net}. "
                "Symptom: the host cannot use the VLAN gateway. "
                "Fix: pick an address inside that subnet."
            )

    return errors, warnings


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "requirements.yaml"
    print(f"SmartBranch 360 plan checker")
    print(f"Checking: {path}")
    print("-" * 50)

    try:
        plan = load_plan(path)
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: Cannot read YAML: {exc}")
        sys.exit(1)

    print(f"Site: {plan.get('site', '(not set)')}")
    print(f"VLAN count: {len(plan.get('vlans') or [])}")
    print("-" * 50)

    errors, warnings = check_vlans(plan)

    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(e if str(e).startswith("ERROR:") else f"ERROR: {e}")

    print("-" * 50)
    if errors:
        print(f"RESULT: FAIL  ({len(errors)} error(s), {len(warnings)} warning(s))")
        sys.exit(1)

    print(f"RESULT: PASS  (0 errors, {len(warnings)} warning(s))")
    print("Plan looks consistent: unique VLANs, valid subnets, gateways inside subnets.")
    sys.exit(0)


if __name__ == "__main__":
    main()
