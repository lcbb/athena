#version 330 core

// Adapted from Qt outline shader example

in vec3 vertexPosition;
in vec3 wing1Vtx;
in vec3 wing2Vtx;

out EyeSpaceVertex {
    vec3 origPosition;
    vec3 position;
    vec4 wing1;
    vec4 wing2;
} vs_out;

uniform mat4 modelView;
uniform mat3 modelViewNormal;
uniform mat4 mvp;

void main()
{
    vs_out.origPosition = vertexPosition;
    vs_out.position = vec3( modelView * vec4( vertexPosition, 1.0 ) );
    vs_out.wing1 = mvp * vec4( wing1Vtx, 1.0 );
    vs_out.wing2 = mvp * vec4( wing2Vtx, 1.0 );

    gl_Position = mvp * vec4( vertexPosition, 1.0 );
}
