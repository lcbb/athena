#version 330 core

// Adapted from PyMOL

in SphereVertex {
    vec3 sphere_center;
    vec3 point;
    float radius2;
    vec4 color;
} fs_in;

out vec4 fragColor;

uniform mat4 projectionMatrix;
uniform float proj_orthographic;

void main()
{
    vec3 ray_origin = vec3(0, 0, 0);
    vec3 ray_direction = normalize( fs_in.point );
    vec3 sphere_direction = fs_in.sphere_center;

    if( proj_orthographic > 0.5 ){
        ray_origin = fs_in.point;
        ray_direction = vec3(0., 0., -1.);
        sphere_direction = ray_origin - fs_in.sphere_center;
    }

    // Calculate sphere-ray intersection
    float b = dot(sphere_direction, ray_direction);

    float position = b * b + fs_in.radius2 - dot(sphere_direction, sphere_direction);

    // Check if the ray missed the sphere
    if (position < 0.0)
       discard;

    // Calculate nearest point of intersection
    float nearest = b - sqrt(position);

    // Calculate intersection point on the sphere surface.  The ray
    // origin is at the quad (center point), so we need to project
    // back towards the user to get the front face.
    vec3 ipoint = nearest * ray_direction + ray_origin;

    // Calculate normal at the intersection point
    vec3 normal = normalize(ipoint - fs_in.sphere_center);

    // Calculate depth in clipping space 
    vec2 clipZW = ipoint.z * projectionMatrix[2].zw +
        projectionMatrix[3].zw;

    float depth = 0.5 + 0.5 * clipZW.x / clipZW.y;

    // this is a workaround necessary for Mac
    // otherwise the modified fragment won't clip properly

/*
    float isDiscarded = step(.5, step(depth, 0.) + step(1.-depth, 0.));
    if (isDiscarded > 0.0)
      discard;
*/
    if (depth <= 0.0 || depth >= 1.0)
      discard;

    gl_FragDepth = depth;

    fragColor = fs_in.color * min( 1, dot( -ray_direction, normal ) );

}
