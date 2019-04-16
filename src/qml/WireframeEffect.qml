/****************************************************************************
**
** Copyright (C) 2014 Klaralvdalens Datakonsult AB (KDAB).
** Contact: https://www.qt.io/licensing/
**
** This file is part of the Qt3D module of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:BSD$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** BSD License Usage
** Alternatively, you may use this file under the terms of the BSD license
** as follows:
**
** "Redistribution and use in source and binary forms, with or without
** modification, are permitted provided that the following conditions are
** met:
**   * Redistributions of source code must retain the above copyright
**     notice, this list of conditions and the following disclaimer.
**   * Redistributions in binary form must reproduce the above copyright
**     notice, this list of conditions and the following disclaimer in
**     the documentation and/or other materials provided with the
**     distribution.
**   * Neither the name of The Qt Company Ltd nor the names of its
**     contributors may be used to endorse or promote products derived
**     from this software without specific prior written permission.
**
**
** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
** "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
** LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
** A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
** OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
** SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
** LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
** DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
** THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
** (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
** OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
**
** $QT_END_LICENSE$
**
****************************************************************************/

import Qt3D.Core 2.0
import Qt3D.Render 2.0

Effect {
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

            filterKeys: [ FilterKey { name: "renderingStyle"; value: "forward" } ]

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
