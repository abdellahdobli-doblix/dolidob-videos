#!/bin/sh
# The generator must reproduce the first episode's official figures (Texas vs California on $75,000).
set -e
cp podcast/script.json /tmp/script.backup.json
python3 scripts/make_episode.py California Texas 75000 > /dev/null
for v in '"Texas vs California on $75,000 (2026)"' '"-$7,670"' '"-$5,738"' '"-$4,027"' '"$61,593 vs $57,565"' '"California tax + SDI"'; do
  grep -qF "$v" podcast/script.json || { echo "missing $v"; cp /tmp/script.backup.json podcast/script.json; exit 1; }
done
cp /tmp/script.backup.json podcast/script.json
echo "make_episode reproduces the official Texas vs California figures"
