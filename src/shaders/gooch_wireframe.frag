#version 330 core

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

//const vec3 kblue = vec3 ( 0, .1, .8 );
//const vec3 kyellow = vec3( .7, .7, 0 );
const float gooch_beta = .35;
const float gooch_alpha = .2;

in WireframeVertex {
    vec3 position;
    flat vec3 normal;
    noperspective vec4 edgeA;
    noperspective vec4 edgeB;
    flat int configuration;
} fs_in;

out vec4 fragColor;

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
    float d;
    if ( fs_in.configuration == 0 )
    {
        // Common configuration
        d = min( fs_in.edgeA.x, fs_in.edgeA.y );
        d = min( d, fs_in.edgeA.z );
    }
    else
    {
        // Handle configuration where screen space projection breaks down
        // Compute and compare the squared distances
        vec2 AF = gl_FragCoord.xy - fs_in.edgeA.xy;
        float sqAF = dot( AF, AF );
        float AFcosA = dot( AF, fs_in.edgeA.zw );
        d = abs( sqAF - AFcosA * AFcosA );

        vec2 BF = gl_FragCoord.xy - fs_in.edgeB.xy;
        float sqBF = dot( BF, BF );
        float BFcosB = dot( BF, fs_in.edgeB.zw );
        d = min( d, abs( sqBF - BFcosB * BFcosB ) );

        // Only need to care about the 3rd edge for some configurations.
        if ( fs_in.configuration == 1 || fs_in.configuration == 2 || fs_in.configuration == 4 )
        {
            float AFcosA0 = dot( AF, normalize( fs_in.edgeB.xy - fs_in.edgeA.xy ) );
            d = min( d, abs( sqAF - AFcosA0 * AFcosA0 ) );
        }

        d = sqrt( d );
    }

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
    vec4 color = vec4( goochModel( fs_in.position, normalize( fs_in.normal ) ), alpha );
    fragColor = shadeLine( color );
}
