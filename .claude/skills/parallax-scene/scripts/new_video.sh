#!/usr/bin/env bash
# Scaffold a new video project folder in this repo, matching the channel's layout.
#
#   new_video.sh "Video Title" ["thumbnail text"] ["youtube title"]
#
# Creates:
#   <Video Title>/
#     planning.md                 (thumbnail text / title / intent / arc / brain-dump)
#     script.md                   (title header)
#     scenes/
#       STYLE_REFERENCE.md        (canonical art-direction template)
#       PARALLAX_PROMPTS.md       (empty split-prompt scaffold)
#
# Then: fill planning.md, break it into scenes/ folders + .md files, write the split
# prompts, generate art, and run process_scene.sh per scene. See SKILL.md.
set -euo pipefail

TITLE="${1:?usage: new_video.sh \"Video Title\" [\"thumbnail text\"] [\"youtube title\"]}"
THUMB="${2:-<thumbnail text>}"
YT="${3:-$TITLE}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS="$HERE/../assets"
ROOT="$(cd "$HERE/../../../.." && pwd)"          # repo root (…/.claude/skills/parallax-scene/scripts)
DIR="$ROOT/$TITLE"

[ -e "$DIR" ] && { echo "✗ already exists: $DIR"; exit 1; }
mkdir -p "$DIR/scenes"

# planning.md — expand the template placeholders
sed -e "s|{{THUMB}}|$THUMB|g" -e "s|{{YT}}|$YT|g" "$ASSETS/planning_template.md" > "$DIR/planning.md"

# script.md
printf '# %s — Script\n' "$TITLE" > "$DIR/script.md"

# scenes templates (copied verbatim; fill per-video blanks later)
cp "$ASSETS/style_reference_template.md"   "$DIR/scenes/STYLE_REFERENCE.md"
cp "$ASSETS/parallax_prompts_template.md"  "$DIR/scenes/PARALLAX_PROMPTS.md"

echo "✓ created \"$TITLE\""
echo "  $DIR/planning.md"
echo "  $DIR/script.md"
echo "  $DIR/scenes/{STYLE_REFERENCE,PARALLAX_PROMPTS}.md"
echo
echo "Next: fill planning.md, then break it into scenes/ (see SKILL.md phase 1)."
