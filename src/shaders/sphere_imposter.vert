#version 330 core

in vec3 vertexPosition;
in float sphereRadius;
in vec4 vertexColor;

out EyeSpaceVertex {
    vec4 position;
    flat float radius;
    flat float radius2;
} vs_out;

uniform mat4 modelView;
uniform mat3 modelViewNormal;
uniform mat4 mvp;

void main()
{
    //vs_out.normal = normalize( modelViewNormal * vertexNormal );
    vs_out.position = modelView * vec4( vertexPosition, 1.0 );
    vs_out.radius =  sphereRadius;
    vs_out.radius2 = sphereRadius * sphereRadius;

    gl_Position = mvp * vec4( vertexPosition, 1.0 );
}
