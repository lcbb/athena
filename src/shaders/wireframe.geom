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
    noperspective vec4 edgeA;
    flat vec3 interior;
    flat vec2 p[3];
    noperspective vec4 edgeB;
    flat int configuration;
    flat vec2 segments[9];
} gs_out;

uniform mat4 viewportMatrix;
uniform mat3 modelViewNormal;

const int infoA[]  = int[]( 0, 0, 0, 0, 1, 1, 2 );
const int infoB[]  = int[]( 1, 1, 2, 0, 2, 1, 2 );
const int infoAd[] = int[]( 2, 2, 1, 1, 0, 0, 0 );
const int infoBd[] = int[]( 2, 2, 1, 2, 0, 2, 1 );

vec2 transformToViewport( const in vec4 p )
{
    return vec2( viewportMatrix * ( p / p.w ) );
}

float cross2( const in vec2 a, const in vec2 b )
{
    return a.x * b.y - b.x * a.y;
}

void main()
{
    gs_out.normal = normalize( modelViewNormal * normalize( cross( gs_in[1].origPosition - gs_in[0].origPosition,
                                                        gs_in[2].origPosition - gs_in[0].origPosition ) ));
    //gs_out.configuration = int(gl_in[0].gl_Position.z < 0) * int(4)
           //+ int(gl_in[1].gl_Position.z < 0) * int(2)
           //+ int(gl_in[2].gl_Position.z < 0);

    gs_out.configuration = 0;

    // If all vertices are behind us, cull the primitive
    //if (gs_out.configuration == 7)
     //   return;

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

    if (gs_out.configuration == 0)
    {
        // Common configuration where all vertices are within the viewport
        gs_out.edgeA = vec4(0.0);
        gs_out.edgeB = vec4(0.0);
        
        float area2 = abs( cross2( p[2]-p[0] , p[2]-p[1] ) );

        // Calculate lengths of 3 edges of triangle
        float a = distance( p[1], p[2] );
        float b = distance( p[2], p[0] );
        float c = distance( p[1], p[0] );

        // Calculate the perpendicular distance of each vertex from the opposing edge
        float ha = area2 / a;
        float hb = area2 / b;
        float hc = area2 / c;

        // Now add this perpendicular distance as a per-vertex property in addition to
        // the position and normal calculated in the vertex shader.

        gs_out.p = p;

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
    else
    {
        // Viewport projection breaks down for one or two vertices.
        // Caclulate what we can here and defer rest to fragment shader.
        // Since this is coherent for the entire primitive the conditional
        // in the fragment shader is still cheap as all concurrent
        // fragment shader invocations will take the same code path.

        // Copy across the viewport-space points for the (up to) two vertices
        // in the viewport
        gs_out.edgeA.xy = p[infoA[gs_out.configuration]];
        gs_out.edgeB.xy = p[infoB[gs_out.configuration]];

        // Copy across the viewport-space edge vectors for the (up to) two vertices
        // in the viewport
        gs_out.edgeA.zw = normalize( gs_out.edgeA.xy - p[ infoAd[gs_out.configuration] ] );
        gs_out.edgeB.zw = normalize( gs_out.edgeB.xy - p[ infoBd[gs_out.configuration] ] );

        // Pass through the other vertex attributes
        //gs_out.normal = gs_in[0].normal;
        gs_out.position = gs_in[0].position;
        gl_Position = gl_in[0].gl_Position;
        EmitVertex();

        //gs_out.normal = gs_in[1].normal;
        gs_out.position = gs_in[1].position;
        gl_Position = gl_in[1].gl_Position;
        EmitVertex();

        //gs_out.normal = gs_in[2].normal;
        gs_out.position = gs_in[2].position;
        gl_Position = gl_in[2].gl_Position;
        EmitVertex();

        // Finish the primitive off
        EndPrimitive();
    }
}
