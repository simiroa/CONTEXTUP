// RigReady Vectorizer - After Effects Native Shape Import Script
// Auto-generated - creates native Shape Layers with proper position and anchor points

(function() {
    app.beginUndoGroup("RigReady Native Import");

    try {
        var compWidth = 100;
        var compHeight = 100;
        var fps = 24;
        var duration = 10;

        var layers = [
  {
    "name": "TestLayer",
    "x": 0,
    "y": 0,
    "w": 100,
    "h": 100,
    "anchor_x": 50,
    "anchor_y": 50,
    "local_ax": 50,
    "local_ay": 50,
    "shapes": [
      {
        "type": "group",
        "fill": "#FF0000",
        "opacity": 0.5,
        "paths": [
          {
            "vertices": [
              [
                0.0,
                0.0
              ],
              [
                100.0,
                0.0
              ],
              [
                100.0,
                100.0
              ],
              [
                0.0,
                100.0
              ]
            ],
            "inTangents": [
              [
                0,
                0
              ],
              [
                0,
                0
              ],
              [
                0,
                0
              ],
              [
                0,
                0
              ]
            ],
            "outTangents": [
              [
                0,
                0
              ],
              [
                0,
                0
              ],
              [
                0,
                0
              ],
              [
                0,
                0
              ]
            ],
            "closed": true
          },
          {
            "vertices": [
              [
                20.0,
                20.0
              ],
              [
                80.0,
                20.0
              ],
              [
                80.0,
                80.0
              ],
              [
                20.0,
                80.0
              ]
            ],
            "inTangents": [
              [
                0,
                0
              ],
              [
                0,
                0
              ],
              [
                0,
                0
              ],
              [
                0,
                0
              ]
            ],
            "outTangents": [
              [
                0,
                0
              ],
              [
                0,
                0
              ],
              [
                0,
                0
              ],
              [
                0,
                0
              ]
            ],
            "closed": true
          }
        ]
      }
    ]
  }
];

        var comp = app.project.items.addComp(
            "RigReady_Native_Vectors",
            compWidth,
            compHeight,
            1,
            duration,
            fps
        );

        function hexToAeColor(hex) {
            hex = hex.replace('#', '');
            if (hex.length === 3) {
                hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
            }
            var r = parseInt(hex.substring(0, 2), 16) / 255;
            var g = parseInt(hex.substring(2, 4), 16) / 255;
            var b = parseInt(hex.substring(4, 6), 16) / 255;
            return [r, g, b];
        }

        // Create each layer (index 0 = bottom, last = top)
        for (var i = 0; i < layers.length; i++) {
            var lData = layers[i];

            var shapeLayer = comp.layers.addShape();
            shapeLayer.name = lData.name;

            // Set anchor/position in comp space
            shapeLayer.property("ADBE Transform Group")
                .property("ADBE Anchor Point")
                .setValue([lData.local_ax, lData.local_ay]);
            shapeLayer.property("ADBE Transform Group")
                .property("ADBE Position")
                .setValue([lData.anchor_x, lData.anchor_y]);

            var contents = shapeLayer.property("ADBE Root Vectors Group");

            for (var j = lData.shapes.length - 1; j >= 0; j--) {
                var sGroup = lData.shapes[j];

                // Create a container group for the compound path
                var group = contents.addProperty("ADBE Vector Group");
                group.name = "Path Group " + (j + 1);
                var groupContents = group.property("ADBE Vectors Group");

                // Add all sub-paths first
                for (var k = 0; k < sGroup.paths.length; k++) {
                    var sData = sGroup.paths[k];
                    var pathProp = groupContents.addProperty("ADBE Vector Shape - Group");
                    var myShape = new Shape();
                    myShape.vertices = sData.vertices;
                    myShape.inTangents = sData.inTangents;
                    myShape.outTangents = sData.outTangents;
                    myShape.closed = sData.closed;
                    pathProp.property("ADBE Vector Shape").setValue(myShape);
                }

                // Add single fill for the entire group (handles holes)
                var fillProp = groupContents.addProperty("ADBE Vector Graphic - Fill");
                fillProp.property("ADBE Vector Fill Color").setValue(hexToAeColor(sGroup.fill));
                if (sGroup.opacity !== undefined) {
                    fillProp.property("ADBE Vector Fill Opacity").setValue(sGroup.opacity * 100);
                }
            }
        }

        comp.openInViewer();

        alert("Native Import Complete!\n\n" +
              "Layers created: " + layers.length + "\n" +
              "Each layer is a native After Effects Shape Layer.");

    } catch (e) {
        alert("Error during native import:\n" + e.toString() + "\nLine: " + e.line);
    }

    app.endUndoGroup();
})();
