#version 330 core

layout( points ) in;
//layout( points, max_vertices = 3 ) out;
layout( triangle_strip, max_vertices = 4 ) out;


in EyeSpaceVertex {
    vec4 position;
    flat float radius;
    flat float radius2;
    vec4 color;
} gs_in[];

out SphereVertex {
    vec3 sphere_center;
    vec3 point;
    float radius2;
    vec4 color;
} gs_out;

uniform mat4 viewportMatrix;
uniform mat3 modelViewNormal;

void main()
{

    gs_out.sphere_center = gs_in[0].position.xyz;
    gs_out.point = gs_out.sphere_center;
    gs_out.radius2 = gs_in[0].radius2;
    gs_out.color = gs_in[0].color;
    float radius = .05;

    gl_Position = gl_in[0].gl_Position + vec4( -radius,-radius, 0, 0 );
    EmitVertex();
    gl_Position = gl_in[0].gl_Position + vec4( radius,-radius, 0, 0 );
    EmitVertex();
    gl_Position = gl_in[0].gl_Position + vec4( -radius, radius, 0, 0 );
    EmitVertex();
    gl_Position = gl_in[0].gl_Position + vec4( radius, radius, 0, 0 );
    EmitVertex();
    //EndPrimitive();

}
