#!/usr/bin/env bash
# 14-quest.sh
#
# Why: 1.3.2 adds QUEST ("Quest of the Undying Emerald Sovereign
# Throne"), a Legend-of-the-Red-Dragon homage door — the town hub +
# the daily-rationed forest grind + the twelve Great-Work level masters
# + the Emerald-fragment spine. The pure logic is unit-tested
# (t161-t166); this drives the screen flow over telnet in practice mode
# (no login): town -> forest -> a fight -> back to town -> the Bank.
#
# Success: the banner renders, the forest offers a hunt, a fight starts
# and an attack resolves, and the Bank screen shows. Exit 0.

set -euo pipefail
cd "$(dirname "$0")/../.."

HOST=127.0.0.1
PORT=${1:-2327}

[ -x ./build/agora ] || cyrius build src/main.cyr build/agora
./build/agora serve "$PORT" --store ./bbs >/tmp/agora-quest-smoke.log 2>&1 &
SERVER=$!
trap 'kill "$SERVER" 2>/dev/null || true' EXIT
sleep 0.5

exec 3<>/dev/tcp/"$HOST"/"$PORT"
drain() { while IFS= read -r -t "${1:-0.5}" -u 3 line; do printf '%s\n' "$(printf '%s' "$line" | tr -d '\r')"; done; }

while IFS= read -r -t 0.4 -u 3 _; do :; done        # banner + IAC

echo "=== play quest ==="
printf 'play quest\r\n' >&3; sleep 0.3
town=$(drain)
printf '%s\n' "$town"

echo "=== b (bank), then r (town) ==="
printf 'b\r\n' >&3; sleep 0.3
bank=$(drain)
printf '%s\n' "$bank"
printf 'r\r\n' >&3; sleep 0.2; drain >/dev/null

echo "=== f (forest) ==="
printf 'f\r\n' >&3; sleep 0.3
forest=$(drain)
printf '%s\n' "$forest"

echo "=== y (hunt) ==="
printf 'y\r\n' >&3; sleep 0.3
fight=$(drain)
printf '%s\n' "$fight"

echo "=== a (attack) ==="
printf 'a\r\n' >&3; sleep 0.3
hit=$(drain)
printf '%s\n' "$hit"

printf 'f\r\n' >&3 || true   # flee if still fighting
printf 'r\r\n' >&3 || true
printf 'q\r\n' >&3 || true
exec 3<&-

rc=0
case "$town"   in *"UNDYING EMERALD SOVEREIGN THRONE"*) echo "OK — quest banner rendered";; *) echo "FAIL — no banner" >&2; rc=1;; esac
case "$town"   in *"the Forest"*)        echo "OK — town hub menu";; *) echo "FAIL — no town menu" >&2; rc=1;; esac
case "$forest" in *"hunt a beast"*)      echo "OK — forest offers a hunt";; *) echo "FAIL — no forest hunt" >&2; rc=1;; esac
case "$fight"  in *"attack"*)            echo "OK — a fight began";; *) echo "FAIL — no fight" >&2; rc=1;; esac
case "$bank"   in *"10% a day"*)         echo "OK — the Bank screen";; *) echo "FAIL — no bank" >&2; rc=1;; esac

exit "$rc"
