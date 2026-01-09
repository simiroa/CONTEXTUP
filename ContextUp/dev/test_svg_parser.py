"""Verification of sub-path and relative coordinate parsing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.image.vectorizer.svg_builder import parse_d_to_ae_path

# Test 1: Multiple sub-paths (M commands)
d_multi = "M 0 0 L 10 0 L 10 10 Z M 20 20 L 30 20 L 30 30 Z"
print("Testing sub-paths...")
subs = parse_d_to_ae_path(d_multi)
print(f"  Got {len(subs)} sub-paths (Expected: 2)")
for i, s in enumerate(subs):
    print(f"  Sub {i}: {len(s['vertices'])} vertices, closed={s['closed']}")

# Test 2: Relative coordinates (m, l, c)
d_rel = "M 100 100 l 50 0 c 10 0 20 10 20 20 l 0 50 z"
print("\nTesting relative coordinates...")
subs_rel = parse_d_to_ae_path(d_rel)
vertices = subs_rel[0]['vertices']
print(f"  Start: {vertices[0]}")
print(f"  After l 50 0: {vertices[1]} (Expected: [150.0, 100.0])")
print(f"  After Bezier (abs pos): {vertices[2]} (Expected: [170.0, 120.0])")

# Test 3: Multiple coordinate pairs after M
d_m_multi = "M 0 0 10 10 20 20"
print("\nTesting multiple coordinates after M...")
subs_m = parse_d_to_ae_path(d_m_multi)
print(f"  Vertices: {subs_m[0]['vertices']} (Expected: [[0.0, 0.0], [10.0, 10.0], [20.0, 20.0]])")

if len(subs) == 2 and vertices[1] == [150.0, 100.0] and vertices[2] == [170.0, 120.0]:
    print("\n✅ SVG parser verification PASSED!")
else:
    print("\n❌ SVG parser verification FAILED!")
