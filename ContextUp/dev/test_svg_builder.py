"""Updated test script for native AE Shape Layer generation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.image.vectorizer.svg_builder import (
    parse_svg_to_ae_shapes, 
    build_ae_jsx_script, 
)

# Test SVG content with a cubic bezier and a line
test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <path d="M 10 10 L 90 10 C 95 10 100 15 100 20 L 100 90 Z" fill="#FF5733"/>
</svg>'''

print("Testing parse_svg_to_ae_shapes...")
shapes = parse_svg_to_ae_shapes(test_svg)

if not shapes:
    print("❌ Failed to parse shapes from SVG")
    sys.exit(1)

shape_data = shapes[0]
path = shape_data['path']

print(f"  Parsed {len(shapes)} paths")
print(f"  Path Fill: {shape_data['fill']}")
print(f"  Vertices: {len(path['vertices'])}")
print(f"  Closed: {path['closed']}")

# Verification of vertex/tangent structure
expected_vertices = 5 # M, L, C, L, Z(closed)
if len(path['vertices']) >= 4:
    print("✅ Vertex count looks reasonable")
else:
    print(f"❌ Unexpected vertex count: {len(path['vertices'])}")

# Test JSX generation
import tempfile
output_dir = Path(tempfile.mkdtemp()) / "native_vec_test"
jsx_path = output_dir / "native_import.jsx"

print("\nTesting build_ae_jsx_script (Native)...")
layer_data = [{
    "name": "NativeTestLayer",
    "offset_x": 10,
    "offset_y": 20,
    "width": 100,
    "height": 100,
    "anchor_x": 60,
    "anchor_y": 70,
    "shapes": shapes
}]

build_ae_jsx_script(layer_data, 1920, 1080, jsx_path)

jsx_content = jsx_path.read_text(encoding='utf-8')
print(f"  JSX created at: {jsx_path}")
print(f"  JSX contains vertices: {'vertices' in jsx_content}")
print(f"  JSX contains ADBE Root Vectors Group: {'ADBE Root Vectors Group' in jsx_content}")

if 'vertices' in jsx_content and 'ADBE Root Vectors Group' in jsx_content:
    print("\n✅ Native JSX generation verified!")
else:
    print("\n❌ JSX content is missing required AE properties")

print("\nTest completed.")
