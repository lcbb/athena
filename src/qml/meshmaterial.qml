
import Qt3D.Core 2.0
import Qt3D.Render 2.0

Material {
    id: wireframeMaterial
    effect: Effect {
      id: root

      parameters: [
          Parameter { name: "ka";   value: Qt.vector3d( 0.1, 0.1, 0.1 ) },
          Parameter { name: "kd";   value: Qt.vector3d( 0.7, 0.7, 0.7 ) },
          Parameter { name: "ks";  value: Qt.vector3d( 0.05, 0.05, 0.05 ) },
          Parameter { name: "shininess"; value: 150.0 }
      ]

      techniques: [
          Technique {
              graphicsApiFilter {
                  api: GraphicsApiFilter.OpenGL
                  profile: GraphicsApiFilter.CoreProfile
                  majorVersion: 3
                  minorVersion: 1
              }

              filterKeys: [ //FilterKey { name: "renderingStyle"; value: "forward" },
                            FilterKey { name: "pass"; value: "transp" } ]

              parameters: []

              // As ever, it's tricky to display the inside of a complex transparent mesh.  We don't
              // have any way to depth-sort our triangles, so true back-to-front rendering is not easy
              // to implement here.  Here's a decent potemkin version of that: render all the back faces
              // first, when the depth test disabled, then render the front faces in the usual way.
              // It's goofy-looking for certain models but looks good for most.
              renderPasses: [
                  RenderPass {
                      renderStates:[ 
                          CullFace{ mode : CullFace.Front },
                          //DepthTest{ depthFunction: DepthTest.Always },
                          NoDepthMask {},
                          BlendEquationArguments{ 
                              sourceRgb: BlendEquationArguments.SourceAlpha
                              destinationRgb: BlendEquationArguments.OneMinusSourceAlpha
                          },
                          BlendEquation{ blendFunction: BlendEquation.Add}
                      ]
                      // populated with a shader within geomview.py, since qml cannot usefully work with
                      // relative file paths for shader loading
                  },
                  RenderPass {
                      renderStates:[ 
                          CullFace{ mode : CullFace.Back },
                          DepthTest{ depthFunction: DepthTest.Less },
                          //NoDepthMask {},
                          BlendEquationArguments{ 
                              sourceRgb: BlendEquationArguments.SourceAlpha
                              destinationRgb: BlendEquationArguments.OneMinusSourceAlpha
                          },
                          BlendEquation{ blendFunction: BlendEquation.Add}
                      ]
                      // populated with a shader within geomview.py, since qml cannot usefully work with
                      // relative file paths for shader loading
                  }
              ]
          }
      ]
  }
}
