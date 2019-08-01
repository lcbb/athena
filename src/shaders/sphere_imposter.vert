#version 330 core

// Adapted from PyMOL

in vec3 vertexPosition;
in float sphereRadius;
in vec4 vertexColor;

out EyeSpaceVertex {
    //vec4 sphere_center;
    float radius;
    float radius2;
    vec4 color;
} vs_out;

uniform mat4 modelView;
uniform mat3 modelViewNormal;
uniform mat4 mvp;

void main()
{
    vs_out.radius =  sphereRadius;
    vs_out.radius2 = sphereRadius * sphereRadius;
    vs_out.color = vertexColor;
    gl_Position = modelView * vec4( vertexPosition, 1.0 );
}
