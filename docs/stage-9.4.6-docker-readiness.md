# Stage 9.4.6 — WS-δ Docker-on-Windows Readiness (Scout Cycle, Executor 2)

**Status:** SCOUT FINDINGS — pending advisor disposition at H#5 hand-back
**Predecessor SHA:** `5b7019f` (Stage 9.4.5 RATIFIED close-handoff, 2026-05-12)
**Probe wall-clock:** ~2 min
**Halt class:** READ-ONLY environmental probes; ZERO commits this cycle; ZERO container starts; ZERO image pulls

---

## §1 Scope

Per Stage 9.4.6 Executor 2 scout handover §3 Task 2 + advisor amendment A-E2-H2-2 (composite step 4: skip manifest inspect + lite-(ii) registry search + lite-(iii) installer reachability), verifying Docker-on-Windows readiness against ADR-9.2-V6 G-1 PASS-path assumption ("Docker sidecar adapter" — see [stage-9.4.6-g1-license-audit.md](./stage-9.4.6-g1-license-audit.md) §7 candidate F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE for substrate-fit cross-axis).

## §2 Probe 1 — `docker version` (client + server)

```
Client:
 Version:           29.0.1
 API version:       1.52
 Go version:        go1.25.4
 Git commit:        eedd969
 Built:             Fri Nov 14 16:19:55 2025
 OS/Arch:           windows/amd64
 Context:           desktop-linux

Server: Docker Desktop 4.53.0 (211793)
 Engine:
  Version:          29.0.1
  API version:      1.52 (minimum version 1.44)
  Git commit:       198b5e3
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd: v2.1.5
 runc: 1.3.3
```

**Disposition:** ✅ Docker installed (29.0.1) + Docker Desktop 4.53.0; client `windows/amd64`; server `linux/amd64`; context `desktop-linux`. Client/server major+minor versions match.

## §3 Probe 2 — `docker info` (daemon + Linux containers mode)

Key fields:
- **Server Version:** 29.0.1
- **OS/Arch (server):** linux/amd64 (resolved from probe 1)
- **Storage Driver:** overlayfs (`io.containerd.snapshotter.v1`)
- **Logging Driver:** json-file
- **Cgroup Driver:** cgroupfs
- **Cgroup Version:** 2
- **Plugins available:** ai, buildx, compose, debug, desktop, extension, init, mcp, model, offload, pass, sandbox, sbom, scout
- **Containers:** 4 (Running 3, Stopped 1); Images: 17

**Disposition:** ✅ Linux containers mode confirmed (server OS = linux). F-9.4.6-DOCKER-WINDOWSCONTAINERS candidate FALSIFIED (not in Windows-containers mode). Daemon healthy; cgroup v2 + overlayfs + json-file all standard production-compatible.

## §4 Probe 3 — WSL2 backend status

```
=== wsl --status ===
Default Distribution: Ubuntu
Default Version: 2

=== wsl --list --verbose ===
  NAME                STATE        VERSION
* Ubuntu              Running      2
  docker-desktop      Running      2
```

(Output formatting note: wsl.exe emits UTF-16LE on Windows, transcript shows interleaved nulls; substance interpreted above.)

**Disposition:** ✅ WSL2 backend operational. Default WSL version is 2. User Ubuntu distro Running at WSL2; Docker Desktop's `docker-desktop` distro Running at WSL2. No `docker-desktop-data` distro listed by name (likely Docker Desktop 4.53 consolidated storage architecture — non-blocking; storage works via overlayfs per Probe 2). All Docker-on-Windows backend prereqs satisfied.

## §5 Probe 4 (composite per A-E2-H2-2) — Forge distribution surface

### §5.1 Lite-(ii) Registry search

**Docker Hub** (via `docker search`):

| Query | Match | Stars | Affiliation | Disposition |
|---|---|---|---|---|
| `forgecode` | `cromulentscientist/forgecode` | 0 | unofficial / community | NOT canonical |
| `forgecode` | `jadshe/forgecode-extension` | 0 | unofficial / community | NOT canonical |
| `forge` | `jboss/forge` | 3 | JBoss Forge (unrelated product) | NOT canonical |
| `forge` | `diem/forge`, `runpod/forge`, `pangeo/forge`, `aiforgestudio/forge`, `prosysopc/forge`, `aptoslabs/forge`, etc. | 0–1 | unrelated namespaces | NOT canonical |

→ No `antinomyhq/forge`, no `tailcallhq/forge`, no `tailcallhq/forgecode` namespace images on Docker Hub. Two unofficial low-signal community images for `forgecode` exist but neither is upstream-published.

**GHCR** (via `gh api -X GET "/orgs/{org}/packages?package_type=container"`):

```
=== GHCR packages on tailcallhq ===
{"message":"You need at least read:packages scope to list packages.", "status":"403"}

=== GHCR packages on antinomyhq ===
{"message":"You need at least read:packages scope to list packages.", "status":"403"}
```

→ Local `gh` token lacks `read:packages` OAuth scope; **GHCR result INCONCLUSIVE for scout cycle**. Advisor may want to re-run with elevated token (`gh auth refresh --scopes read:packages`) post-cycle; OR Phase A.1 can verify directly via container registry web UI (`https://github.com/orgs/tailcallhq/packages` browser path) to disambiguate "no upstream Docker image" vs "upstream Docker image exists but unlisted in Docker Hub".

### §5.2 Lite-(iii) Installer reachability

```
$ curl -sI https://forgecode.dev/cli
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 25528
Server: GitHub.com
Content-Type: application/octet-stream
Last-Modified: Sun, 19 Apr 2026 11:31:57 GMT
ETag: "69e4bd2d-63b8"
Cache-Control: max-age=600
```

**Disposition:** ✅ Installer reachable HTTP 200, 25,528-byte shell script. `Server: GitHub.com` header reveals `forgecode.dev/cli` proxies/serves from GitHub-hosted content — the canonical distribution surface is a GitHub-served shell script, NOT a Docker image. Install vector: `curl -fsSL https://forgecode.dev/cli | sh`.

### §5.3 Composite step 4 disposition

- **No canonical upstream Docker image** confirmed via Docker Hub search + upstream README + GHCR (inconclusive due to token-scope, but Docker Hub absence + README install-vector silence suffices for "no canonical Docker image" finding).
- Distribution surface = shell-installer + Nix flake + ZSH plugin (per upstream README; see audit-report §7 F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE).
- Surface reframes ADR-9.2-V6 PASS-path "Docker sidecar adapter" assumption — see audit-report §7 carry-forward for Phase A.1 sub-charter.

## §6 WS-δ DISPOSITION + F-class candidates

### WS-δ disposition (primary readiness outcome)

**Docker-on-Windows readiness → CLEAR / GREEN** on environment axis:
- Probe 1: Docker 29.0.1 + Docker Desktop 4.53.0 installed ✅
- Probe 2: Linux containers mode confirmed (server OS = linux/amd64) ✅
- Probe 3: WSL2 backend operational (default version 2; Ubuntu + docker-desktop distros Running) ✅
- Probe 4 composite (per A-E2-H2-2): registry-search + installer-reachability confirm the substrate-distribution-surface is curl-installer, NOT Docker image

**B.1 environmental blocker:** NONE on Docker/WSL axis. Phase B.1 substrate-fit blocker is upstream-distribution-shape (F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE), NOT local Docker readiness.

### F-class candidates (advisor disposition pending at H#5)

Per refined 5b7019f AM-C-1: F-tokens in report-body prose are ACCEPTABLE. All tokens below are CANDIDATE class.

1. Surfaced as F-class candidate (cross-referenced — primary surface in license-audit §7): **F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE** — pending advisor disposition.
   - **Evidence summary** (full evidence in license-audit §7): no canonical Forge Docker image on Docker Hub; GHCR inconclusive (token-scope); upstream README install vectors are shell-installer + Nix + ZSH; `forgecode.dev/cli` HTTP 200 confirms shell-installer is the canonical distribution surface.
   - **Surface:** see license-audit §7.

### F-class candidates that were FALSIFIED during H#3

- ~~F-9.4.6-DOCKER-NOTINSTALLED~~ (seeded by handover §3 Task 2 disposition logic) — **FALSIFIED:** Probe 1 returned `Docker version 29.0.1` + Docker Desktop 4.53.0 server.
- ~~F-9.4.6-DOCKER-WINDOWSCONTAINERS~~ (seeded by handover §3 Task 2 disposition logic) — **FALSIFIED:** Probe 2 server OS/Arch = `linux/amd64` (Linux containers mode); client Context = `desktop-linux`.

### Phase A.1 / B.1 carry-forward

- **(Optional advisor scope, post-cycle):** elevate local `gh` token with `read:packages` scope to disambiguate GHCR inconclusive result OR verify via `https://github.com/orgs/tailcallhq/packages` browser path — confirms or refutes "no upstream Docker image" with certainty
- **(Phase A.1 sub-charter scope):** if proceeding with Forge substrate via shell-installer route, validate installer idempotency, version-pin mechanism (does `forgecode.dev/cli` honor a version flag, or only "latest"?), uninstall path, and offline-install possibility (relevant for air-gapped POV environments)

### §6 footer retro-note — F-class disposition status update

Per **[E2-H4 → E2-H5] advisor disposition** (post-H#4 surface relay), F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE (cross-referenced throughout this report; primary surface in [license-audit §7](./stage-9.4.6-g1-license-audit.md)) is lifted CANDIDATE → **DECLARED**. Substrate-fit assumption falsification at ADR-9.2-V6 PASS-path level — BLOCKS Phase A.1 sub-charter authoring until re-anchor disposition lands. GHCR community-image disambiguation deferred to Phase A.1 sub-charter authoring (advisor scope, post-cycle).

## §7 Provenance

**Probe wall-clock:** ~2 min
**Tool surface:** `docker version`, `docker info`, `wsl --status`, `wsl --list --verbose`, `docker search`, `gh api` (GHCR packages), `curl -sI` (installer reachability)
**Probe artifact retention:** raw outputs captured in conversation transcript at H#3
**ZERO container starts, ZERO image pulls, ZERO Forge clones, ZERO source edits**
**24-SHA chain unchanged through hand-back**
**Output file disposition:** UTF-8 explicit encoding; created as `??` (untracked); preserved for advisor read
