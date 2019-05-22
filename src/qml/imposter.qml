import Qt3D.Core 2.0
import Qt3D.Render 2.0
import Qt3D.Input 2.0
import Qt3D.Extras 2.0

Material {
    id: impostermaterial
    effect: Effect { 
        id: root

        parameters: [
        ]

        techniques: [
            Technique {
                graphicsApiFilter {
                    api: GraphicsApiFilter.OpenGL
                    profile: GraphicsApiFilter.CoreProfile
                    majorVersion: 3
                    minorVersion: 1
                }

                filterKeys: [ FilterKey { name: "renderingStyle"; value: "forward" } ]

                parameters: []

                renderPasses: [
                    RenderPass {
                        // populated with a shader within geomview.py, since qml cannot usefully work with
                        // relative file paths for shader loading
                    } ]
        }
    ]
    }
}
