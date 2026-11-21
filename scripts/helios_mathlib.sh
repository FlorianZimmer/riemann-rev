#!/usr/bin/env bash
# Build lean-mathlib/ (the skeleton's destination layer instantiated with Mathlib's ζ) on a SLURM
# cluster, at the archive's pins (Lean 4.33.1, Mathlib 0df444a3), in a temporary directory there.
# Mathlib needs about 11 GB; that is why this is not built on a laptop.
#
#   bash scripts/helios_mathlib.sh            # sync, set up (idempotent), build, fetch logs, record
#   bash scripts/helios_mathlib.sh --record   # only fetch the logs of the last build and rewrite the record
#   bash scripts/helios_mathlib.sh --cleanup  # remove the remote temporary directory
#
# The record (verification/logs/mathlib-zeta-axioms.json) carries the SHA-256 of the three files that
# were compiled, read back from the cluster; `make check` compares them with the files in this
# repository, so a record cannot silently outlive an edit.
#
# Settings, from the environment or from private/cluster.env (not part of the public tree):
#   HELIOS_HOST       SSH name of the cluster
#   HELIOS_TMP        a temporary directory on the cluster whose name contains "riemann-rev-tmp-"
#   HELIOS_ACCOUNT    SLURM account
#   HELIOS_PARTITION  SLURM partition
# The job asks for 8 CPUs and 45 minutes; the build takes about 15 minutes.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
[[ -f "$ROOT/private/cluster.env" ]] && source "$ROOT/private/cluster.env"
HOST=${HELIOS_HOST:?set HELIOS_HOST (see the head of this script)}
T=${HELIOS_TMP:?set HELIOS_TMP (see the head of this script)}
ACCOUNT=${HELIOS_ACCOUNT:?set HELIOS_ACCOUNT (see the head of this script)}
PARTITION=${HELIOS_PARTITION:?set HELIOS_PARTITION (see the head of this script)}
LOGS=$ROOT/verification/logs

if [[ "${1:-}" == "--cleanup" ]]; then
  # Only ever remove a directory that carries this project's temporary name.
  [[ "$T" == */riemann-rev-tmp-* ]] || { echo "refusing to remove '$T': not a riemann-rev temporary directory"; exit 2; }
  ssh -o BatchMode=yes "$HOST" "rm -rf -- '$T'" && echo "removed $HOST:$T"
  exit 0
fi

mkdir -p "$ROOT/lean-mathlib/Atlas" "$LOGS"
if [[ "${1:-}" != "--record" ]]; then
cp "$ROOT/lean/Atlas/Architecture.lean" "$ROOT/lean-mathlib/Atlas/Architecture.lean"
ssh -o BatchMode=yes "$HOST" "mkdir -p '$T'/{elan,cache,tmp,proj,logs} && chmod 700 '$T'"
rsync -a --exclude .lake --exclude Probe.lean "$ROOT/lean-mathlib/" "$HOST:$T/proj/"

ssh -o BatchMode=yes "$HOST" bash -s -- "$T" "$ACCOUNT" "$PARTITION" <<'REMOTE'
set -euo pipefail
T=$1; ACCOUNT=$2; PARTITION=$3
export ELAN_HOME=$T/elan XDG_CACHE_HOME=$T/cache TMPDIR=$T/tmp MATHLIB_CACHE_DIR=$T/cache/mathlib
export PATH="$HOME/.elan/bin:$PATH" GIT_TERMINAL_PROMPT=0 MATHLIB_NO_CACHE_ON_UPDATE=1
[[ -r /etc/pki/tls/certs/ca-bundle.crt ]] && export CURL_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt
cd "$T/proj"
[[ -x "$ELAN_HOME/toolchains/leanprover--lean4---v4.33.1/bin/lean" ]] || elan toolchain install leanprover/lean4:v4.33.1
[[ -d .lake/packages/mathlib ]] || lake update
[[ -f "$T/cache.done" ]] || { lake exe cache get > "$T/logs/cache.log" 2>&1 && touch "$T/cache.done"; } || { tail -5 "$T/logs/cache.log"; exit 1; }
# Lean memory-maps Mathlib's .olean files; on Lustre the first page faults are very slow, so the job
# first reads them in parallel into the node's page cache (as the reading project did), then builds.
srun -A "$ACCOUNT" -p "$PARTITION" -N1 -n1 -c8 --mem=24G -t 00:45:00 -J rr-mathlib \
  bash -c 'export LEAN_NUM_THREADS=8; { lean --version;
    s=$(date +%s); find .lake/packages -name "*.olean" -print0 | xargs -0 -n 64 -P 16 cat > /dev/null;
    echo "prefetch: $(( $(date +%s) - s )) s";
    lake build 2>&1; echo "exit=$?"; }' > "$T/logs/build.log" 2>&1 || true
tail -3 "$T/logs/build.log"
REMOTE
fi

scp -q "$HOST:$T/logs/build.log" "$LOGS/mathlib-zeta-build.log"
scp -q "$HOST:$T/proj/lake-manifest.json" "$ROOT/lean-mathlib/lake-manifest.json"
# The files that were compiled, hashed where they were compiled.
REMOTE_SUMS=$(ssh -o BatchMode=yes "$HOST" "cd '$T/proj' && sha256sum AtlasZeta.lean Atlas/Architecture.lean lake-manifest.json")
REMOTE_SUMS="$REMOTE_SUMS" python3 - "$LOGS/mathlib-zeta-build.log" "$LOGS/mathlib-zeta-axioms.json" "$ROOT" <<'PY'
import hashlib, json, os, pathlib, re, sys
log = open(sys.argv[1], encoding="utf-8").read()
root = pathlib.Path(sys.argv[3])
here = {"AtlasZeta.lean": "lean-mathlib/AtlasZeta.lean", "Atlas/Architecture.lean": "lean/Atlas/Architecture.lean",
        "lake-manifest.json": "lean-mathlib/lake-manifest.json"}
sources, stale = {}, []
for line in os.environ["REMOTE_SUMS"].splitlines():
    digest, name = line.split()
    sources[here[name]] = digest
    if hashlib.sha256((root / here[name]).read_bytes()).hexdigest() != digest:
        stale.append(f"{here[name]} differs from the file that was compiled")
manifest = json.loads((root / "lean-mathlib/lake-manifest.json").read_text(encoding="utf-8"))
mathlib_rev = next(p["rev"] for p in manifest["packages"] if p["name"] == "mathlib")
decl = {}
for m in re.finditer(r"'([^']+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])", log):
    decl[m.group(1)] = [a.strip() for a in m.group(3).split(",")] if m.group(3) else []
bad = [l for l in log.splitlines() if re.search(r"\berror\b|\bwarning\b|sorry", l)] + stale
ok = "exit=0" in log and "Build completed successfully" in log and not bad
json.dump({"lean": next((l for l in log.splitlines() if l.startswith("Lean (version")), ""),
           "mathlib_rev": mathlib_rev, "build": "passed" if ok else "failed",
           "build_log_sha256": hashlib.sha256(log.encode("utf-8")).hexdigest(),
           "sources": sources, "declarations": decl, "problems": bad},
          open(sys.argv[2], "w"), indent=2)
print("mathlib build:", "passed" if ok else "FAILED", "|", mathlib_rev[:8], "|", decl)
sys.exit(0 if ok else 1)
PY
