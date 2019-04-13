#version 330 core

layout( triangles ) in;
layout( triangle_strip, max_vertices = 3 ) out;

uniform struct LineInfo {
    float width;
    vec4 color;
} line;

in EyeSpaceVertex {
    vec3 position;
    vec3 normal;
    flat float interior;
} gs_in[];

out WireframeVertex {
    vec3 position;
    flat vec3 normal;
    noperspective vec4 edgeA;
    noperspective vec4 edgeB;
    flat int configuration;
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
    gs_out.normal = normalize( modelViewNormal * normalize( cross( gs_in[1].normal - gs_in[0].normal,
                                                        gs_in[2].normal - gs_in[0].normal ) ));
    gs_out.configuration = int(gl_in[0].gl_Position.z < 0) * int(4)
           + int(gl_in[1].gl_Position.z < 0) * int(2)
           + int(gl_in[2].gl_Position.z < 0);

    // If all vertices are behind us, cull the primitive
    //if (gs_out.configuration == 7)
     //   return;

    // Transform each vertex into viewport space
    vec2 p[3];
    p[0] = transformToViewport( gl_in[0].gl_Position );
    p[1] = transformToViewport( gl_in[1].gl_Position );
    p[2] = transformToViewport( gl_in[2].gl_Position );

    if (gs_out.configuration == 0)
    {
        // Common configuration where all vertices are within the viewport
        gs_out.edgeA = vec4(0.0);
        gs_out.edgeB = vec4(0.0);
        
        float area2 = cross2( p[2]-p[0] , p[2]-p[1] );

        // Calculate lengths of 3 edges of triangle
        float a = distance( p[1], p[2] ); //length( p[1] - p[2] );
        float b = distance( p[2], p[0] );
        float c = distance( p[1], p[0] );

        // Calculate internal angles using the cosine rule
        float alpha_args = ( b * b + c * c - a * a ) / ( 2.0 * b * c );
        float alpha;
        if( alpha_args > 1-1e3 ){
            alpha = sqrt( (a*a-(b-c)*(b-c)) / (b*c) );
        }
        else{
            alpha = acos( alpha_args );
        }

        float beta;
        float beta_args = ( a * a +  c * c - b * b ) / ( 2.0 * a * c );
        if( beta_args > 1-1e3 ){
            beta = sqrt( (b*b-(a-c)*(a-c)) / (a*c) );
        }
        else{
            beta = acos( beta_args );
        }
        //float alpha = acos( ( b * b + c * c - a * a ) / ( 2.0 * b * c ) );
        //float beta = acos( ( a * a + c * c - b * b ) / ( 2.0 * a * c ) );

        float degen_offset = line.width+1.1;

        // Calculate the perpendicular distance of each vertex from the opposing edge
        //float ha = abs( c * sin(beta)  );
        //float hb = abs( c * sin(alpha) );
        //float hc = abs( b * sin(alpha) );
        float ha = max( abs( area2 / a ), degen_offset );
        float hb = max( abs( area2 / b ), degen_offset );
        float hc = max( abs( area2 / c ), degen_offset );
        //float ha = max( degen_offset*gs_in[1].interior, abs( c * sin( beta ) ) );
        //float hb = max( degen_offset*gs_in[2].interior, abs( c * sin( alpha ) ) );
        //float hc = max( degen_offset*gs_in[0].interior, abs( b * sin( alpha ) ) );


        // Now add this perpendicular distance as a per-vertex property in addition to
        // the position and normal calculated in the vertex shader.

        // Vertex 0 (a)
        gs_out.edgeA = vec4( ha, (b+degen_offset)*gs_in[2].interior, (c+degen_offset)*gs_in[0].interior, 0.0 );
        gs_out.position = gs_in[0].position;
        gl_Position = gl_in[0].gl_Position;
        EmitVertex();

        // Vertex 1 (b)
        gs_out.edgeA = vec4( (a+degen_offset)*gs_in[1].interior, hb, (c+degen_offset)*gs_in[0].interior, 0.0 );
        gs_out.position = gs_in[1].position;
        gl_Position = gl_in[1].gl_Position;
        EmitVertex();

        // Vertex 2 (c)
        gs_out.edgeA = vec4( (a+degen_offset)*gs_in[1].interior, (b+degen_offset)*gs_in[2].interior, hc, 0.0 );
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
