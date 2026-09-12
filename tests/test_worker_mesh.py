"""Suite mesh Live Nodes + QNM-BUILD-1.0 + QNS-CD-1.0 contract.

Default OFF. live|locked|isolated. QNS-CD-1.0 photon QNS1 cross-map only.
No public qnsd proxy. No Node Gate. No auto-heal. Not anonymity.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MESH = (ROOT / "workers/download-tracker/src/mesh.js").read_text(encoding="utf-8")
RUNTIME = (ROOT / "workers/download-tracker/src/runtime.js").read_text(encoding="utf-8")
INDEX = (ROOT / "workers/download-tracker/src/index.js").read_text(encoding="utf-8")
WRANGLER = (ROOT / "workers/download-tracker/wrangler.toml").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
WORKER_README = (ROOT / "workers/download-tracker/README.md").read_text(encoding="utf-8")


def test_mesh_contract_default_off_qnm_law() -> None:
    assert 'QNM_SPEC = "QNM-BUILD-1.0"' in MESH
    assert 'QNS_CD_SPEC = "QNS-CD-1.0"' in MESH
    assert "export const QNS_CD" in MESH
    assert "photon QNS1 packet transfer" in MESH
    assert "https://github.com/AzielEliab/qnm-node" in MESH
    assert "https://github.com/AzielEliab/aziel-runtime" in MESH
    assert "https://github.com/AzielEliab/azinterface" in MESH
    assert "QNS-CD-1.0" in MESH
    assert "softwares_tab: false" in MESH
    assert "qnsd_public: false" in MESH
    assert "public_proxy: false" in MESH
    assert "No public qnsd proxy" in MESH
    assert "attachQnsCd" in MESH
    assert "MESH_DEFAULT_OFF = true" in MESH
    assert "MESH_ANONYMITY_NETWORK = false" in MESH
    assert "MESH_NODE_GATE = false" in MESH
    assert "MESH_AUTO_HEAL = false" in MESH
    assert "MESH_IDENTITY = IDENTITY" in MESH or '"Aziel Eliab"' in MESH
    assert 'MESH_PRODUCT = "mialock"' in MESH
    assert 'MESH_PATH = "/v1/mesh"' in MESH
    assert "live|locked|isolated" in MESH
    assert "enabled_default: false" in MESH
    assert "anon_broadcast_publish_path: false" in MESH
    assert "Aziel Eliab" in MESH
    assert "code: extra.code || \"MESH-OK\"" in MESH or '"MESH-OK"' in MESH
    assert '"/v1/qnsd"' not in MESH
    assert '"/v1/qns"' not in MESH


def test_mesh_pointer_and_openapi_helpers() -> None:
    assert "export function meshPointer" in MESH
    assert "export function meshOpenApiPaths" in MESH
    assert "export function parseMeshDoc" in MESH
    assert "export function emptyMesh" in MESH
    assert "export function alignLiveNodes" in MESH
    assert "export function attachQnsCd" in MESH
    assert "fraggate_slug: MESH_SLUG" in MESH
    assert "mialock_mesh_" in MESH


def test_mesh_proxies_via_aziel_runtime() -> None:
    assert "MESH_ROUTE_METHODS" in MESH
    assert "isMeshPath" in MESH
    assert "runMeshProxy" in MESH
    assert "handleMeshApi" in MESH
    assert "originFetch" in MESH
    assert '"/v1/mesh"' in MESH
    assert 'startsWith("/v1/mesh/")' in MESH
    assert "AZIEL_RUNTIME" in MESH
    assert "https://aziel-runtime.vibelock.workers.dev" in MESH
    assert "AZIEL_RUNTIME" in WRANGLER
    assert "aziel-runtime" in WRANGLER
    assert "/v1/mesh" in WRANGLER
    assert 'id = "e397d1a7e84049ce94dadb6189b94fdc"' in WRANGLER


def test_index_routes_mesh_before_runtime_catchall() -> None:
    assert 'from "./mesh.js"' in INDEX
    assert "handleMeshApi" in INDEX
    mesh_idx = INDEX.index("handleMeshApi(request, url, env)")
    runtime_idx = INDEX.index("handleRuntimeApi(request, url)")
    assert mesh_idx < runtime_idx
    not_found = INDEX.rindex('return json({ error: "not found" }, 404)')
    assert mesh_idx < not_found


def test_runtime_advertises_mesh_proxy_and_pointer() -> None:
    assert 'from "./mesh.js"' in RUNTIME
    assert "meshPointer" in RUNTIME
    assert "meshOpenApiPaths" in RUNTIME
    assert "...meshOpenApiPaths()" in RUNTIME
    assert "mesh: meshPointer()" in RUNTIME
    assert "/v1/mesh" in RUNTIME
    assert "QNM-BUILD-1.0" in RUNTIME
    assert "QNS-CD-1.0" in RUNTIME
    assert "No Node Gate" in RUNTIME
    assert 'path === "/v1/mesh"' in RUNTIME or 'path.startsWith("/v1/mesh/")' in RUNTIME


ROSE_STAR_SHA256 = "af095e8b0916a7262860a53619c7110f25539988806775b1c7bff8df7b0ee848"
BRAND_MARK = (
    '<div class="brandrow"><img class="brandmark" src="/sigil.png" '
    'width="40" height="40" alt="" decoding="async"></div>'
)


def test_home_rose_star_brandmark() -> None:
    assert BRAND_MARK in INDEX
    assert ".brandrow{" in INDEX
    assert ".brandmark{" in INDEX
    assert 'alt=""' in INDEX
    assert "everblooming" not in INDEX.lower()
    assert "Everblooming" not in INDEX
    assert "Aziel Eliab" in INDEX
    assert "everblooming" not in README.lower()
    sigil = ROOT / "workers/download-tracker/public/sigil.png"
    assert sigil.is_file()
    data = sigil.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    # Official rose-star (196×139), not the 2MB oversized mark.
    assert len(data) == 75035
    assert hashlib.sha256(data).hexdigest() == ROSE_STAR_SHA256


def test_home_live_nodes_strip_no_node_gate() -> None:
    assert 'id="meshStrip"' in INDEX
    assert 'id="meshLiveCount"' in INDEX
    assert 'id="meshLine"' in INDEX
    assert "Live Nodes" in INDEX
    assert "QNM-BUILD-1.0" in INDEX
    assert "QNS-CD-1.0" in INDEX
    assert "No Node Gate" in INDEX
    assert "No auto-heal" in INDEX
    assert "Not an anonymity network" in INDEX
    assert "/v1/mesh" in INDEX
    assert 'product: "mialock"' in INDEX
    assert 'id="node-gate"' not in INDEX
    assert 'href="/node-gate"' not in INDEX
    assert "auto-heal this node" not in INDEX


def test_docs_advertise_mesh_proxy() -> None:
    assert "/v1/mesh" in README
    assert "/v1/mesh" in SKILL
    assert "QNM-BUILD-1.0" in WORKER_README
    assert "QNS-CD-1.0" in WORKER_README
    assert "QNS-CD-1.0" in README
    assert "QNS-CD-1.0" in SKILL
    assert "qnm-node" in README
    assert "aziel-runtime" in SKILL
    assert "AZIEL_RUNTIME" in WORKER_README
    assert "Live Nodes" in WORKER_README
    assert "MESH-OK" in WORKER_README
    assert "enabled: false" in WORKER_README
    assert "Aziel Eliab" in MESH
