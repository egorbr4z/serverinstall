import asyncio
import json
import os
import re
import time
import uuid
from collections import deque
from typing import Optional

import psutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config

app = FastAPI(title="VPN Monitor")

# ─── In-memory history for sparklines (30 samples) ───────────────────────────
_cpu_history: deque = deque(maxlen=30)
_mem_history: deque = deque(maxlen=30)
_net_prev: Optional[tuple] = None   # (bytes_sent, bytes_recv, timestamp)

# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _exec(*cmd: str) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    return proc.returncode, out.decode(errors="replace"), err.decode(errors="replace")


async def _docker_exec(container: str, *cmd: str) -> tuple[int, str, str]:
    return await _exec("docker", "exec", container, *cmd)


async def _docker_exec_input(container: str, stdin_data: bytes, *cmd: str) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        "docker", "exec", "-i", container, *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate(input=stdin_data)
    return proc.returncode, out.decode(errors="replace"), err.decode(errors="replace")


def _human(n: float, suffix: str = "B") -> str:
    for unit in ("", "K", "M", "G", "T"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}{suffix}"
        n /= 1024
    return f"{n:.1f} P{suffix}"


def _uptime_str(seconds: int) -> str:
    d, s = divmod(seconds, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    parts = []
    if d: parts.append(f"{d}д")
    if h: parts.append(f"{h}ч")
    if m: parts.append(f"{m}м")
    if not parts: parts.append(f"{s}с")
    return " ".join(parts)

# ─── System metrics ───────────────────────────────────────────────────────────

def get_system_stats() -> dict:
    global _net_prev
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    now = time.time()
    uptime = int(now - psutil.boot_time())

    _cpu_history.append(round(cpu, 1))
    _mem_history.append(round(mem.percent, 1))

    sent_rate = recv_rate = 0.0
    if _net_prev:
        ps, pr, pt = _net_prev
        dt = now - pt
        if dt > 0:
            sent_rate = max(0.0, (net.bytes_sent - ps) / dt)
            recv_rate = max(0.0, (net.bytes_recv - pr) / dt)
    _net_prev = (net.bytes_sent, net.bytes_recv, now)

    return {
        "cpu": {"percent": cpu, "count": psutil.cpu_count(), "history": list(_cpu_history)},
        "memory": {
            "total": mem.total, "used": mem.used,
            "percent": mem.percent, "history": list(_mem_history),
            "total_h": _human(mem.total), "used_h": _human(mem.used),
        },
        "disk": {
            "total": disk.total, "used": disk.used,
            "percent": disk.percent,
            "total_h": _human(disk.total), "used_h": _human(disk.used),
        },
        "network": {
            "sent_rate": sent_rate, "recv_rate": recv_rate,
            "sent_rate_h": _human(sent_rate, "B/s"),
            "recv_rate_h": _human(recv_rate, "B/s"),
            "total_sent_h": _human(net.bytes_sent),
            "total_recv_h": _human(net.bytes_recv),
        },
        "uptime": uptime,
        "uptime_h": _uptime_str(uptime),
        "load": list(os.getloadavg()),
    }

# ─── WireGuard / AmneziaWG ────────────────────────────────────────────────────

def _parse_wg_show(output: str) -> list[dict]:
    peers, cur = [], None
    for raw in output.splitlines():
        line = raw.strip()
        if line.startswith("peer:"):
            if cur:
                peers.append(cur)
            cur = {
                "public_key": line[5:].strip(),
                "endpoint": None, "allowed_ips": None,
                "latest_handshake": None, "connected": False,
                "transfer_rx": "—", "transfer_tx": "—",
            }
        elif cur:
            if line.startswith("endpoint:"):
                cur["endpoint"] = line[9:].strip()
            elif line.startswith("allowed ips:"):
                cur["allowed_ips"] = line[12:].strip()
            elif line.startswith("latest handshake:"):
                hs = line[17:].strip()
                cur["latest_handshake"] = hs
                cur["connected"] = _hs_recent(hs)
            elif line.startswith("transfer:"):
                parts = line[9:].strip()
                rx = re.search(r"([\d.]+ \w+) received", parts)
                tx = re.search(r"([\d.]+ \w+) sent", parts)
                if rx: cur["transfer_rx"] = rx.group(1)
                if tx: cur["transfer_tx"] = tx.group(1)
    if cur:
        peers.append(cur)
    return peers


def _hs_recent(s: str, threshold: int = 180) -> bool:
    if not s or s.lower() in ("never", ""):
        return False
    secs = 0
    for pat, mul in [(r"(\d+) day", 86400), (r"(\d+) hour", 3600),
                     (r"(\d+) minute", 60), (r"(\d+) second", 1)]:
        m = re.search(pat, s)
        if m:
            secs += int(m.group(1)) * mul
    return secs <= threshold


async def get_awg_status() -> dict:
    try:
        iface = config.AWG_INTERFACE
        rc, out, err = await _docker_exec(config.AWG_CONTAINER, "awg", "show", iface)
        if rc != 0:
            rc, out, err = await _docker_exec(config.AWG_CONTAINER, "wg", "show", iface)
        if rc != 0:
            return {"status": "error", "error": err.strip(), "peers": [], "connected": 0, "total": 0}
        peers = _parse_wg_show(out)
        connected = sum(1 for p in peers if p["connected"])
        return {"status": "running", "peers": peers, "connected": connected, "total": len(peers)}
    except Exception as e:
        return {"status": "error", "error": str(e), "peers": [], "connected": 0, "total": 0}

# ─── VLESS / xray ─────────────────────────────────────────────────────────────

async def _find_xray_config() -> Optional[str]:
    for path in config.XRAY_CONFIG_PATHS:
        rc, _, _ = await _docker_exec(config.XRAY_CONTAINER, "test", "-f", path)
        if rc == 0:
            return path
    return None


async def _read_xray_config() -> dict:
    path = await _find_xray_config()
    if not path:
        raise FileNotFoundError("xray config not found in container")
    rc, out, err = await _docker_exec(config.XRAY_CONTAINER, "cat", path)
    if rc != 0:
        raise RuntimeError(f"cat failed: {err}")
    return json.loads(out), path


async def _write_xray_config(data: dict, path: str) -> None:
    payload = json.dumps(data, indent=2, ensure_ascii=False).encode()
    rc, _, err = await _docker_exec_input(
        config.XRAY_CONTAINER, payload,
        "sh", "-c", f"cat > {path}",
    )
    if rc != 0:
        raise RuntimeError(f"write failed: {err}")


async def get_xray_status() -> dict:
    try:
        rc, out, _ = await _exec("docker", "inspect", "--format={{.State.Status}}", config.XRAY_CONTAINER)
        status = out.strip() if rc == 0 else "not_found"

        # Count established TCP connections inside container
        rc2, out2, _ = await _docker_exec(config.XRAY_CONTAINER, "ss", "-tnp")
        connected = 0
        if rc2 == 0:
            connected = sum(1 for ln in out2.splitlines() if "ESTAB" in ln)
        else:
            # fallback: /proc/net/tcp  state=01 means ESTABLISHED
            rc2, out2, _ = await _docker_exec(config.XRAY_CONTAINER, "cat", "/proc/net/tcp")
            if rc2 == 0:
                connected = sum(1 for ln in out2.splitlines()[1:] if ln.split()[3] == "01")

        return {"status": status, "connected": connected}
    except Exception as e:
        return {"status": "error", "error": str(e), "connected": 0}

# ─── Hysteria2 ────────────────────────────────────────────────────────────────

async def get_hysteria2_status() -> dict:
    try:
        rc, out, _ = await _exec("systemctl", "is-active", config.HYSTERIA2_SERVICE)
        active = rc == 0 and out.strip() == "active"

        # Try traffic API
        try:
            import aiohttp
            async with aiohttp.ClientSession() as sess:
                async with sess.get(
                    f"http://127.0.0.1:{config.HYSTERIA2_API_PORT}/traffic",
                    timeout=aiohttp.ClientTimeout(total=1),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "status": "running" if active else "stopped",
                            "connected": len(data) if isinstance(data, dict) else 0,
                            "api": True,
                        }
        except Exception:
            pass

        # Fallback: count UDP sessions (UNCONN lines with PEER addr set)
        rc2, out2, _ = await _exec("ss", "-unp")
        port_str = f":{config.HYSTERIA2_PORT}"
        connected = sum(
            1 for ln in out2.splitlines()
            if port_str in ln and not ln.startswith("Netid")
        )

        return {"status": "running" if active else "stopped", "connected": connected}
    except Exception as e:
        return {"status": "error", "error": str(e), "connected": 0}

# ─── Service management ────────────────────────────────────────────────────────

async def service_action(service: str, action: str) -> dict:
    if service in ("awg", "xray"):
        container = config.AWG_CONTAINER if service == "awg" else config.XRAY_CONTAINER
        rc, _, err = await _exec("docker", action, container)
    elif service == "hysteria2":
        rc, _, err = await _exec("systemctl", action, config.HYSTERIA2_SERVICE)
    else:
        raise ValueError(f"unknown service: {service}")

    return {"ok": rc == 0, "error": err.strip() if rc != 0 else None}

# ─── Logs ─────────────────────────────────────────────────────────────────────

async def get_service_logs(service: str, lines: int) -> str:
    if service == "awg":
        rc, out, err = await _exec("docker", "logs", "--tail", str(lines), config.AWG_CONTAINER)
    elif service == "xray":
        rc, out, err = await _exec("docker", "logs", "--tail", str(lines), config.XRAY_CONTAINER)
    elif service == "hysteria2":
        rc, out, err = await _exec(
            "journalctl", "-u", config.HYSTERIA2_SERVICE,
            "-n", str(lines), "--no-pager", "--output=short-iso",
        )
    else:
        raise ValueError(f"unknown service: {service}")
    return (out + err) if rc == 0 else f"[ошибка {rc}]: {err}"

# ─── AWG client management ────────────────────────────────────────────────────

async def awg_add_peer(allowed_ips: str) -> dict:
    iface = config.AWG_INTERFACE

    rc, privkey, err = await _docker_exec(config.AWG_CONTAINER, "wg", "genkey")
    if rc != 0:
        raise RuntimeError(f"genkey: {err}")
    privkey = privkey.strip()

    rc, pubkey, err = await _docker_exec_input(
        config.AWG_CONTAINER, privkey.encode(), "wg", "pubkey"
    )
    if rc != 0:
        raise RuntimeError(f"pubkey: {err}")
    pubkey = pubkey.strip()

    rc, _, err = await _docker_exec(
        config.AWG_CONTAINER, "wg", "set", iface, "peer", pubkey,
        "allowed-ips", allowed_ips,
    )
    if rc != 0:
        raise RuntimeError(f"wg set: {err}")

    # Persist: try awg-quick first, fall back to wg-quick
    rc2, _, _ = await _docker_exec(config.AWG_CONTAINER, "awg-quick", "save", iface)
    if rc2 != 0:
        await _docker_exec(config.AWG_CONTAINER, "wg-quick", "save", iface)

    return {"public_key": pubkey, "private_key": privkey, "allowed_ips": allowed_ips}


async def awg_remove_peer(public_key: str) -> None:
    iface = config.AWG_INTERFACE
    rc, _, err = await _docker_exec(
        config.AWG_CONTAINER, "wg", "set", iface, "peer", public_key, "remove"
    )
    if rc != 0:
        raise RuntimeError(f"wg set remove: {err}")
    rc2, _, _ = await _docker_exec(config.AWG_CONTAINER, "awg-quick", "save", iface)
    if rc2 != 0:
        await _docker_exec(config.AWG_CONTAINER, "wg-quick", "save", iface)

# ─── VLESS client management ──────────────────────────────────────────────────

async def vless_list_clients() -> list[dict]:
    try:
        cfg, _ = await _read_xray_config()
        clients = []
        for ib in cfg.get("inbounds", []):
            if ib.get("protocol") == "vless":
                for c in ib.get("settings", {}).get("clients", []):
                    clients.append({
                        "id": c.get("id"), "email": c.get("email", ""),
                        "flow": c.get("flow", ""),
                    })
        return clients
    except Exception:
        return []


async def vless_add_client(email: str) -> dict:
    cfg, path = await _read_xray_config()
    new_id = str(uuid.uuid4())
    added = False
    for ib in cfg.get("inbounds", []):
        if ib.get("protocol") == "vless":
            ib.setdefault("settings", {}).setdefault("clients", []).append(
                {"id": new_id, "email": email, "flow": ""}
            )
            added = True
            break
    if not added:
        raise RuntimeError("No VLESS inbound found in xray config")
    await _write_xray_config(cfg, path)
    await _exec("docker", "restart", config.XRAY_CONTAINER)
    return {"id": new_id, "email": email}


async def vless_remove_client(client_id: str) -> None:
    cfg, path = await _read_xray_config()
    for ib in cfg.get("inbounds", []):
        if ib.get("protocol") == "vless":
            clients = ib.get("settings", {}).get("clients", [])
            ib["settings"]["clients"] = [c for c in clients if c.get("id") != client_id]
    await _write_xray_config(cfg, path)
    await _exec("docker", "restart", config.XRAY_CONTAINER)

# ─── FastAPI routes ───────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))


@app.get("/api/system")
async def api_system():
    return get_system_stats()


@app.get("/api/status")
async def api_status():
    awg, xray, h2 = await asyncio.gather(
        get_awg_status(), get_xray_status(), get_hysteria2_status()
    )
    return {"awg": awg, "xray": xray, "hysteria2": h2}


@app.post("/api/services/{svc}/{action}")
async def api_service_action(svc: str, action: str):
    if svc not in ("awg", "xray", "hysteria2"):
        raise HTTPException(400, "Unknown service")
    if action not in ("start", "stop", "restart"):
        raise HTTPException(400, "Unknown action")
    res = await service_action(svc, action)
    if not res["ok"]:
        raise HTTPException(500, res["error"] or "command failed")
    return {"ok": True}


@app.get("/api/logs/{svc}")
async def api_logs(svc: str, lines: int = 150):
    if svc not in ("awg", "xray", "hysteria2"):
        raise HTTPException(400, "Unknown service")
    text = await get_service_logs(svc, min(lines, 500))
    return {"logs": text}


# AWG clients
@app.get("/api/clients/awg")
async def api_awg_clients():
    st = await get_awg_status()
    return {"peers": st.get("peers", [])}


class AddAWGPeer(BaseModel):
    allowed_ips: str   # e.g. "10.8.0.5/32"


@app.post("/api/clients/awg")
async def api_awg_add(data: AddAWGPeer):
    try:
        return await awg_add_peer(data.allowed_ips)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.delete("/api/clients/awg/{public_key:path}")
async def api_awg_remove(public_key: str):
    try:
        await awg_remove_peer(public_key)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))


# VLESS clients
@app.get("/api/clients/vless")
async def api_vless_clients():
    return {"clients": await vless_list_clients()}


class AddVLESSClient(BaseModel):
    email: str


@app.post("/api/clients/vless")
async def api_vless_add(data: AddVLESSClient):
    try:
        return await vless_add_client(data.email)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.delete("/api/clients/vless/{client_id}")
async def api_vless_remove(client_id: str):
    try:
        await vless_remove_client(client_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.APP_HOST, port=config.APP_PORT, log_level="info")
