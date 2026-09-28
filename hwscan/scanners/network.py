"""Network Interfaces Scanner for Hardware Gauntlet."""

import os
import sys
import platform
import socket
from typing import List

try:
    import psutil
except ImportError:
    psutil = None

from hwscan.scanners.base import BaseScanner
from hwscan.core.models import NetworkInfo, NetworkInterface
from hwscan.core.utils import run_command


class NetworkScanner(BaseScanner):
    """Scans network adapters, MAC addresses, IPs, and link speeds."""

    def scan(self) -> NetworkInfo:
        info = NetworkInfo()
        info.hostname = socket.gethostname()

        if not psutil:
            return info

        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()

            for iface_name, addr_list in addrs.items():
                if "loopback" in iface_name.lower():
                    continue

                net_if = NetworkInterface(name=iface_name)

                # Check stats
                if iface_name in stats:
                    st = stats[iface_name]
                    net_if.is_up = st.isup
                    net_if.speed_mbps = st.speed if st.speed > 0 else 0

                # Detect wireless
                lower_name = iface_name.lower()
                net_if.is_wireless = any(x in lower_name for x in ["wi-fi", "wireless", "wlan", "802.11"])

                # Parse addresses
                for addr in addr_list:
                    # AF_INET for IPv4
                    if addr.family == socket.AF_INET:
                        net_if.ipv4.append(addr.address)
                    # AF_INET6 for IPv6
                    elif getattr(socket, "AF_INET6", None) and addr.family == socket.AF_INET6:
                        # strip interface scope if present
                        ip6 = addr.address.split("%")[0]
                        net_if.ipv6.append(ip6)
                    # MAC Address
                    elif hasattr(psutil, "AF_LINK") and addr.family == psutil.AF_LINK:
                        if addr.address and addr.address != "00:00:00:00:00:00":
                            net_if.mac_address = addr.address

                # Only include interfaces that have an IP or MAC or are UP
                if net_if.ipv4 or net_if.mac_address != "N/A" or net_if.is_up:
                    info.interfaces.append(net_if)
        except Exception:
            pass

        # Sort interfaces so active/connected ones come first
        info.interfaces.sort(key=lambda x: (not x.is_up, not bool(x.ipv4)))

        return info
