#version 330 core

in vec3 vertexPosition;
in float radius;
in vec4 vertexColor;

out EyeSpaceVertex {
    float radius;
    vec4 color;
} vs_out;

uniform mat4 modelView;
uniform mat3 modelViewNormal;
uniform mat4 mvp;

void main()
{

    vs_out.radius = radius;
    vs_out.color = vertexColor;
    gl_Position = modelView * vec4( vertexPosition, 1.0 );
}
