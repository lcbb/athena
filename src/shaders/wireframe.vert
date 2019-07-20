#version 330 core

// Adapted from Qt outline shader example

in vec3 vertexPosition;
in vec3 vertexNormal;
in float vertexInterior;

out EyeSpaceVertex {
    vec3 position;
    vec3 normal;
    flat float interior;
} vs_out;

uniform mat4 modelView;
uniform mat3 modelViewNormal;
uniform mat4 mvp;

void main()
{
    //vs_out.normal = normalize( modelViewNormal * vertexNormal );
    vs_out.normal = vertexPosition;
    vs_out.position = vec3( modelView * vec4( vertexPosition, 1.0 ) );
    vs_out.interior =  vertexInterior;

    gl_Position = mvp * vec4( vertexPosition, 1.0 );
}
