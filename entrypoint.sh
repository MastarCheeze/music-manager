#!/usr/bin/env bash
set -euo pipefail

# Generate default config
rip config reset -y > /dev/null
CONFIG_PATH="/root/.config/streamrip/config.toml"

# Disable storing downloaded and failed tracks in database, we will do this manually
sed -i "s/^downloads_enabled = true$/downloads_enabled = false/" "$CONFIG_PATH"
sed -i "s/^failed_downloads_enabled = true$/failed_downloads_enabled = false/" "$CONFIG_PATH"
# Disable save artwork as separate image file
sed -i "s/^save_artwork = true$/save_artwork = false/" "$CONFIG_PATH"
# Disable progress bars
sed -i "s/^progress_bars = true$/progress_bars = false/" "$CONFIG_PATH"
# Disable check for updates banner
sed -i "s/^check_for_updates = true$/check_for_updates = false/" "$CONFIG_PATH"

# Set Deezer ARL
sed -i "s/^arl = \".*\"$/arl = \"${DEEZER_ARL:-}\"/" "$CONFIG_PATH"
# Set track format
if [ -n "${TRACK_FORMAT:-}" ]; then
  sed -i "s/^track_format = \".*\"$/track_format = \"$TRACK_FORMAT\"/" "$CONFIG_PATH"
fi

exec "$@"