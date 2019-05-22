#version 330 core

layout( lines ) in;
layout( triangle_strip, max_vertices = 8 ) out;

in EyeSpaceVertex {
    float radius;
    vec4 color;
} gs_in[];

out CylinderPoint {
    vec3 point;
    vec4 color;
} gs_out;

uniform mat4 projectionMatrix;
uniform mat4 viewportMatrix;
uniform mat3 modelViewNormal;

void main(){

    //EmitVertex();

    EndPrimitive();

}
