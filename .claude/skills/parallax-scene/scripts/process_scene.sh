#!/usr/bin/env bash
# End-to-end parallax for ONE scene: classify plates -> key FG -> render clip.
#
#   process_scene.sh "SCENE_DIR" ID [SECONDS] [extra render_parallax args...]
#
# Expects SCENE_DIR to already contain the two freshly-pasted plates (raw
# Gemini drops). Produces <ID>_fg.png (transparent), <ID>_bg.png, <ID>_parallax.mp4.
#
#   process_scene.sh "3. THE FUNCTION → THE FLUID" 3b
#   process_scene.sh "7. CLOSER (don't cry me a stream)" 7b 30 --loop
set -euo pipefail

DIR="${1:?scene dir}"; ID="${2:?scene id}"; SECS="${3:-30}"; shift $(( $# >= 3 ? 3 : 2 ))
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. classify + rename the two pasted plates
python3 "$HERE/detect_plates.py" --dir "$DIR" --id "$ID"

# 2. chroma-key the FG plate to transparency (keep the raw magenta plate as
#    <id>_fgsrc.png so the key can be re-tuned later without regenerating)
[ -f "$DIR/${ID}_fgsrc.png" ] || cp "$DIR/${ID}_fg.png" "$DIR/${ID}_fgsrc.png"
python3 "$HERE/keychroma.py" "$DIR/${ID}_fgsrc.png" "$DIR/${ID}_fg.png" \
    --preview "$DIR/${ID}_bg.png" "$DIR/${ID}_keypreview.png"

# 3. render the parallax clip
python3 "$HERE/render_parallax.py" "$DIR/${ID}_bg.png" "$DIR/${ID}_fg.png" \
    "$DIR/${ID}_parallax.mp4" --seconds "$SECS" "$@"

echo "✅ $DIR/${ID}_parallax.mp4  (QA: ${ID}_keypreview.png)"
