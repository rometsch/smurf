#!/usr/bin/env bash
SCRIPT_DIR="$(dirname $(realpath $0))"
HOME_DIR="$HOME/.smurf"
mkdir -p "$HOME_DIR"
cp $SCRIPT_DIR/shell_plugin "$HOME_DIR"
cp $SCRIPT_DIR/shell_completion "$HOME_DIR"

echo "$SCRIPT_DIR" > "$HOME_DIR/script_dir.txt"

# check whether shell integration is already enabled
echo "To activate the shell plugin for this session, run:"
echo "source ~/.smurf/shell_plugin"
echo "Add the following lines to your rc file:"
echo "# smurf: enable shell plugin"
echo "[[ -f ~/.smurf/shell_plugin ]] && source ~/.smurf/shell_plugin"
