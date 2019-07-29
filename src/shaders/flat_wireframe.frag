#version 330 core

// Adapted from Qt outline shader example

uniform struct LightInfo {
    vec4 position;
    vec3 intensity;
} light;

uniform struct LineInfo {
    float width;
    vec4 color;
} line;

uniform vec3 flat_color; 
uniform float face_enable;

in WireframeVertex {
    vec3 position;
    flat vec3 normal;
    noperspective vec4 edgeA;
    flat vec3 interior;
    flat vec2 p[3];
    noperspective vec4 edgeB;
    flat int configuration;
    flat vec2 segments[9];
} fs_in;

out vec4 fragColor;

uniform mat4 viewportMatrix;

vec2 transformToViewport( const in vec4 p )
{
    return vec2( viewportMatrix * ( p / p.w ) );
}

float cross2( const in vec2 a, const in vec2 b )
{
    return a.x * b.y - b.x * a.y;
}

float distance_to_line_segment( const in vec2 P, const in vec2 A, const in vec2 B, float d ){
    vec2 AP = P - A;
    vec2 AB = B - A;
    vec2 dist = AP - AB * clamp (dot(AP,AB)/dot(AB,AB), 0.0, 1.0);
    return min( d, length(dist) );
}

vec4 shadeLine( const in vec4 color )
{
    // Find the smallest distance between the fragment and a triangle edge
    float d = 100;

    vec2 point = gl_FragCoord.xy; //  transformToViewport( gl_FragCoord );

    d = distance_to_line_segment( point, fs_in.segments[0], fs_in.segments[1], d);
    d = distance_to_line_segment( point, fs_in.segments[1], fs_in.segments[2], d);

    d = distance_to_line_segment( point, fs_in.segments[3], fs_in.segments[4], d);
    d = distance_to_line_segment( point, fs_in.segments[4], fs_in.segments[5], d);

    d = distance_to_line_segment( point, fs_in.segments[6], fs_in.segments[7], d);
    d = distance_to_line_segment( point, fs_in.segments[7], fs_in.segments[8], d);

    // Blend between line color and phong color
    float mixVal;
    if ( d < line.width - 1.0 )
    {
        mixVal = 1.0;
    }
    else if ( d > line.width + 1.0 )
    {
        mixVal = 0.0;
    }
    else
    {
        float x = d - ( line.width - 1.0 );
        mixVal = exp2( -2.0 * ( x * x ) );
    }

    return mix( color, line.color, mixVal );
}

void main()
{
    //vec4 color = vec4( goochModel( fs_in.position, normalize( fs_in.normal ) ), alpha );
    //vec4 color = vec4( flat_color.x, flat_color.y, flat_color.z, alpha );
    
    vec4 color = vec4( flat_color, face_enable );
    fragColor = shadeLine( color );
}
