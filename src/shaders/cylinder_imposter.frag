#version 330 core

// Adapted from PyMOL

uniform mat4 projectionMatrix;
uniform float proj_orthographic;

in CylinderPoint {
    vec3 surface_point;
    vec3 axis;
    vec3 base;
    vec3 end_cyl;
    vec3 U;
    vec3 V;
    float radius;
    vec4 color;
} fs_in;


out vec4 fragColor;

void main(void)
{
    vec3 ray_target = fs_in.surface_point;

    vec3 ray_origin;
    vec3 ray_direction;
    if( proj_orthographic >= 0.5f ){
        // orthographic projection
        ray_origin = fs_in.surface_point;
        ray_direction = vec3(0., 0., 1.);
    }
    else{
        // perspective projection
        ray_origin = vec3(0, 0, 0);
        ray_direction = normalize(-ray_target);
    }

    // basis is local system of coordinates for the cylinder
    mat3 basis = mat3(fs_in.U, fs_in.V, fs_in.axis);

    // vectors in cylinder xy-plane
    vec2 P = ((ray_target - fs_in.base) * basis).xy;
    vec2 D = (ray_direction * basis).xy;

    float radius2 = fs_in.radius*fs_in.radius;
    vec4 color = fs_in.color;

    // test if the ray is exactly tangent to the whole of the cylinder surface.
    // If this happens, everything we compute below will be garbage (because a2 will be 0),
    // and we need to jump straight into the cap test.
    // This was not in the original PyMol code, did they never have axis-aligned
    // cylinders in orthographic camera mode?
    bool bogus_tangent_ray = all( equal( D, vec2(0, 0) ) );
    vec3 new_point;
    vec3 normal;

    if( !bogus_tangent_ray ){
        // calculate distance to the cylinder from ray origin
        float a0 = P.x*P.x + P.y*P.y - radius2;
        float a1 = P.x*D.x + P.y*D.y;
        float a2 = D.x*D.x + D.y*D.y;
        // calculate a dicriminant of the above quadratic equation
        float d = a1*a1 - a0*a2;
        if (d < 0.0){
            // outside of the cylinder
            discard;
        }

        float dist = (-a1 + sqrt(d))/a2;

        // point of intersection on cylinder surface
        new_point = ray_target + dist * ray_direction;

        vec3 tmp_point = new_point - fs_in.base;
        normal = normalize(tmp_point - fs_in.axis * dot(tmp_point, fs_in.axis));
    }
    else{
        new_point = ray_origin;
    }

    bool cap_test_base = 0.0 > dot((new_point - fs_in.base), fs_in.axis);
    bool cap_test_end  = 0.0 < dot((new_point - fs_in.end_cyl), fs_in.axis);

    if (cap_test_base || cap_test_end || bogus_tangent_ray ){
      vec3 thisaxis = -fs_in.axis;
      vec3 thisbase = fs_in.base;

      if (cap_test_end) {
        thisaxis = fs_in.axis;
        thisbase = fs_in.end_cyl;
      }

      // ray-plane intersection
      float dNV = dot(thisaxis, ray_direction);
      if (dNV <= 0.0)
        discard;

      float near = dot(thisaxis, thisbase - ray_origin) / dNV;
      new_point = ray_direction * near + ray_origin;
      // within the cap radius?
      if (dot(new_point - thisbase, new_point - thisbase) > radius2)
        discard;

      normal = thisaxis;
    }

    vec2 clipZW = new_point.z * projectionMatrix[2].zw +
        projectionMatrix[3].zw;

    float depth = 0.5 + 0.5 * clipZW.x / clipZW.y;

    // front clipping
    if (depth <= 0.0)
      discard;

    gl_FragDepth = depth;
    fragColor = fs_in.color * min( 1, dot( ray_direction, normal ) );

}
