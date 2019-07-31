#version 330 core

// Adapted from Qt outline shader example

layout( triangles ) in;
layout( triangle_strip, max_vertices = 3 ) out;

uniform struct LineInfo {
    float width;
    vec4 color;
} line;

in EyeSpaceVertex {
    vec3 origPosition;
    vec3 position;
    vec4 wing1;
    vec4 wing2;
} gs_in[];

out WireframeVertex {
    vec3 position;
    flat vec3 normal;
    flat vec2 segments[9];
} gs_out;

uniform mat4 viewportMatrix;
uniform mat4 athena_viewport;
uniform mat3 modelViewNormal;

vec2 transformToViewport( const in vec4 p )
{
    return vec2( athena_viewport * ( p / p.w ) );
}

float cross2( const in vec2 a, const in vec2 b )
{
    return a.x * b.y - b.x * a.y;
}

void main()
{
    gs_out.normal = normalize( modelViewNormal * normalize( cross( gs_in[1].origPosition - gs_in[0].origPosition,
                                                        gs_in[2].origPosition - gs_in[0].origPosition ) ));


    // Transform each vertex into viewport space
    vec2 p[3];
    p[0] = transformToViewport( gl_in[0].gl_Position );
    p[1] = transformToViewport( gl_in[1].gl_Position );
    p[2] = transformToViewport( gl_in[2].gl_Position );

    gs_out.segments[0] = transformToViewport( gs_in[0].wing1 );
    gs_out.segments[1] = transformToViewport( gl_in[0].gl_Position );
    gs_out.segments[2] = transformToViewport( gs_in[0].wing2 );

    gs_out.segments[3] = transformToViewport( gs_in[1].wing1 );
    gs_out.segments[4] = transformToViewport( gl_in[1].gl_Position );
    gs_out.segments[5] = transformToViewport( gs_in[1].wing2 );

    gs_out.segments[6] = transformToViewport( gs_in[2].wing1 );
    gs_out.segments[7] = transformToViewport( gl_in[2].gl_Position );
    gs_out.segments[8] = transformToViewport( gs_in[2].wing2 );


    // Vertex 0 (a)
    gs_out.position = gs_in[0].position;
    gl_Position = gl_in[0].gl_Position;
    EmitVertex();

    // Vertex 1 (b)
    gs_out.position = gs_in[1].position;
    gl_Position = gl_in[1].gl_Position;
    EmitVertex();

    // Vertex 2 (c)
    gs_out.position = gs_in[2].position;
    gl_Position = gl_in[2].gl_Position;
    EmitVertex();

    // Finish the primitive off
    EndPrimitive();
}
