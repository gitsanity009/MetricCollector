"""VMware vCenter metrics collector using pyVmomi."""

from __future__ import annotations

import ssl
from datetime import datetime, timezone
from typing import Any

from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim


<<<<<<< HEAD
def _connect(host: str, user: str, password: str, disable_ssl: bool = True):
=======

def _connect(username: str | None = None, password: str | None = None):
>>>>>>> main
    context = None
    if disable_ssl:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    si = SmartConnect(
<<<<<<< HEAD
        host=host,
        user=user,
        pwd=password,
=======
        host=settings.vcenter_host,
        user=username or settings.vcenter_user,
        pwd=password or settings.vcenter_password,
>>>>>>> main
        sslContext=context,
    )
    return si


def _count_objects(content, obj_type):
    view = content.viewManager.CreateContainerView(content.rootFolder, [obj_type], True)
    count = len(view.view)
    view.Destroy()
    return count


def _get_vm_details(content) -> list[dict]:
    view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    vms = []
    for vm in view.view:
        summary = vm.summary
        vms.append({
            "name": summary.config.name,
            "power_state": str(summary.runtime.powerState),
            "cpu_count": summary.config.numCpu,
            "memory_mb": summary.config.memorySizeMB,
            "guest_os": summary.config.guestFullName or "Unknown",
            "ip_address": summary.guest.ipAddress,
        })
    view.Destroy()
    return vms


def _get_host_details(content) -> list[dict]:
    view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    hosts = []
    for host in view.view:
        summary = host.summary
        hardware = summary.hardware
        hosts.append({
            "name": summary.config.name,
            "cpu_model": hardware.cpuModel,
            "cpu_cores": hardware.numCpuCores,
            "memory_gb": round(hardware.memorySize / (1024 ** 3), 1),
            "connection_state": str(summary.runtime.connectionState),
            "vms_running": summary.quickStats.overallCpuUsage is not None,
        })
    view.Destroy()
    return hosts


def _get_datastore_details(content) -> list[dict]:
    view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True)
    datastores = []
    for ds in view.view:
        summary = ds.summary
        capacity_gb = round(summary.capacity / (1024 ** 3), 1) if summary.capacity else 0
        free_gb = round(summary.freeSpace / (1024 ** 3), 1) if summary.freeSpace else 0
        datastores.append({
            "name": summary.name,
            "type": summary.type,
            "capacity_gb": capacity_gb,
            "free_gb": free_gb,
            "used_gb": round(capacity_gb - free_gb, 1),
            "usage_pct": round(((capacity_gb - free_gb) / capacity_gb) * 100, 1) if capacity_gb else 0,
        })
    view.Destroy()
    return datastores


<<<<<<< HEAD
def collect(host: str, user: str, password: str, disable_ssl: bool = True) -> dict[str, Any]:
    """Return vCenter metrics: VM/host/datastore counts and details."""
    si = _connect(host, user, password, disable_ssl)
    content = si.RetrieveContent()
=======
def collect(username: str | None = None, password: str | None = None) -> dict[str, Any]:
    """Return vCenter metrics: VM/host/datastore counts and details."""
>>>>>>> main
    metrics: dict[str, Any] = {"source": "vcenter", "collected_at": datetime.now(timezone.utc).isoformat()}

    try:
        si = _connect(username=username, password=password)
    except Exception as exc:
        metrics["error"] = f"vCenter authentication failed: {exc}"
        return metrics

    content = si.RetrieveContent()

    try:
        metrics["total_vms"] = _count_objects(content, vim.VirtualMachine)
        metrics["total_hosts"] = _count_objects(content, vim.HostSystem)
        metrics["total_datastores"] = _count_objects(content, vim.Datastore)
        metrics["total_clusters"] = _count_objects(content, vim.ClusterComputeResource)
        metrics["total_networks"] = _count_objects(content, vim.Network)

        vms = _get_vm_details(content)
        metrics["vms_powered_on"] = sum(1 for v in vms if v["power_state"] == "poweredOn")
        metrics["vms_powered_off"] = sum(1 for v in vms if v["power_state"] == "poweredOff")
        metrics["vm_details"] = vms

        metrics["host_details"] = _get_host_details(content)
        metrics["datastore_details"] = _get_datastore_details(content)

    except Exception as exc:
        metrics["error"] = str(exc)
    finally:
        Disconnect(si)

    return metrics
