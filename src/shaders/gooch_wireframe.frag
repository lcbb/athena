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

uniform vec3 ka;            // Ambient reflectivity
uniform vec3 kd;            // Diffuse reflectivity
uniform vec3 ks;            // Specular reflectivity
uniform float shininess;    // Specular shininess factor
uniform vec3 cool_color;
uniform vec3 warm_color;
uniform float alpha; 
uniform float face_enable;
uniform float wire_enable;

//const vec3 kblue = vec3 ( 0, .1, .8 );
//const vec3 kyellow = vec3( .7, .7, 0 );
const float gooch_beta = .35;
const float gooch_alpha = .2;
uniform mat4 viewportMatrix;

in WireframeVertex {
    vec3 position;
    flat vec3 normal;
    flat vec2 segments[9];
} fs_in;

out vec4 fragColor;

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

vec3 goochModel( const in vec3 pos, const in vec3 n )
{
    // Based upon the original Gooch lighting model paper at:
    // http://www.cs.northwestern.edu/~ago820/SIG98/abstract.html

    // Calculate the vector from the fragment to the eye position
    // (origin since this is in "eye" or "camera" space)
    vec3 v = normalize( -pos );
    // Calculate the vector from the light to the fragment
    vec3 s = normalize( vec3( light.position ) - pos );

    // Calculate kcool and kwarm from equation (3)
    vec3 kcool = clamp(cool_color + gooch_alpha * kd, 0.0, 1.0);
    vec3 kwarm = clamp(warm_color + gooch_beta * kd, 0.0, 1.0);

    // Calculate the cos theta factor mapped onto the range [0,1]
    float sDotNFactor = ( 1.0 + dot( s, n ) ) / 2.0;

    // Calculate the tone by blending the kcool and kwarm contributions
    // as per equation (2)
    vec3 intensity = mix( kcool, kwarm, sDotNFactor );
    return intensity;


    // Reflect the light beam using the normal at this fragment
    vec3 r = reflect( -s, n );

    // Calculate the specular component
    float specular = 0.0;
    if ( dot( s, n ) > 0.0 )
        specular = pow( max( dot( r, v ), 0.0 ), shininess );

    // Sum the blended tone and specular highlight
    return intensity + ks * specular;
}


vec4 shadeLine( const in vec4 color )
{
    // Find the smallest distance between the fragment and a triangle edge
    float d = 10000;

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
    // Calculate the color from the phong model

    vec4 color = vec4( line.color.xyz, 0.0 );
    if( face_enable > 0.0 ){
        float effective_alpha = min( alpha, face_enable );
        color = vec4( goochModel( fs_in.position, normalize( fs_in.normal ) ), effective_alpha );
    }
    if( wire_enable > 0.0 ){
        fragColor = shadeLine( color );
    }
    else{
        fragColor = color;
    }
}
