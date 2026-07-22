#!/usr/bin/env bash
set -euo pipefail

BREV_BIN="${BREV_BIN:-/opt/homebrew/bin/brev}"
INSTANCE_NAME="${BREV_INSTANCE_NAME:-harness-1-demo}"
INSTANCE_TYPE="${BREV_INSTANCE_TYPE:-hyperstack_H100}"
EXPECTED_HOURLY_USD="${BREV_HOURLY_USD:-3.00}"

if ! "$BREV_BIN" ls --json >/tmp/harness-brev-instances.json 2>/tmp/harness-brev-error.log; then
  echo "Brev is not authenticated. Run: $BREV_BIN login" >&2
  exit 1
fi

if ! grep -q "\"$INSTANCE_NAME\"" /tmp/harness-brev-instances.json; then
  cat <<EOF
No existing instance named $INSTANCE_NAME was found.
Requested type: $INSTANCE_TYPE
Expected price: \$$EXPECTED_HOURLY_USD/hour

Provisioning is intentionally not automatic. After confirming current pricing, run:
  $BREV_BIN create $INSTANCE_NAME --type $INSTANCE_TYPE
EOF
  exit 2
fi

"$BREV_BIN" exec "$INSTANCE_NAME" @scripts/brev/remote_setup.sh
echo "Deployment submitted. Start the local tunnel with scripts/brev/tunnel.sh."
