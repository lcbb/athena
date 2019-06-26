#version 330 core


in CylinderPoint {
    vec3 surface_point;
    vec3 axis;
    vec3 base;
    vec3 end_cyl;
    vec3 U;
    vec3 V;
    float H;
    float radius;
    float cap;
    float inv_sqr_height;
    vec4 color;
} fs_in;


out vec4 fragColor;

uniform mat4 projectionMatrix;

    //fragColor = fs_in.color;
/*
 * Get the lowest bit from 'bits' and shift 'bits' to the right.
 * Equivalent to (if 'bits' would be int):
 * bit = bits & 0x1; bits >>= 1; return bit;
 */
bool get_bit_and_shift(inout float bits) {
  float bit = mod(bits, 2.0);
  bits = (bits - bit) / 2.0;
  return bit > 0.5;
}

void main(void)
{
    vec3 ray_target = fs_in.surface_point;

    vec3 ray_origin = vec3(0, 0, 0);
    vec3 ray_direction = normalize(-ray_target);

    // basis is local system of coordinates for the cylinder
    mat3 basis = mat3(fs_in.U, fs_in.V, fs_in.axis);

    // vectors in cylinder xy-plane
    vec2 P = ((ray_target - fs_in.base) * basis).xy;
    vec2 D = (ray_direction * basis).xy;

    float radius = fs_in.radius * fs_in.H;
    float radius2 = radius * radius;

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
    vec3 new_point = ray_target + dist * ray_direction;

    vec3 tmp_point = new_point - fs_in.base;
    vec3 normal = normalize(tmp_point - fs_in.axis * dot(tmp_point, fs_in.axis));

    /* cap :  4 bits : 1st - frontcap
                       2nd - endcap
                       3rd - frontcapround
                       4th - endcapround
                       5th - interp
     */
    float fcap = fs_in.cap + .001;  // to account for odd rounding issues when setting
                              // varying cap from attribute a_cap, which is a non-normalized
                              // GL_UNSIGNED_BYTE
    bool frontcap      = get_bit_and_shift(fcap);
    bool endcap        = get_bit_and_shift(fcap);
    bool frontcapround = get_bit_and_shift(fcap); // && no_flat_caps;
    bool endcapround   = get_bit_and_shift(fcap); //  && no_flat_caps;
    bool nocolorinterp = !get_bit_and_shift(fcap);

    
    vec4 color = fs_in.color;
    /*float ratio = dot(new_point-fs_in.base, vec3(fs_in.end_cyl-fs_in.base)) * inv_sqr_height;

    if (isPicking || !lighting_enabled){ // for picking
       ratio = step(.5, ratio);
    } else if (nocolorinterp){
       // determine color of half-bond, possible antialiasing 
       // based on half_bond, depth, and height
       float dp = clamp(-half_bond*new_point.z*inv_height, 0., .5);
       ratio = smoothstep(.5 - dp, .5 + dp, ratio);
    } else {
       ratio = clamp(ratio, 0., 1.);
    }
    color = mix(color1, color2, ratio);*/

    bool cap_test_base = 0.0 > dot((new_point - fs_in.base), fs_in.axis);
    bool cap_test_end  = 0.0 < dot((new_point - fs_in.end_cyl), fs_in.axis);

    if (cap_test_base || cap_test_end) {
      vec3 thisaxis = -fs_in.axis;
      vec3 thisbase = fs_in.base;

      if (cap_test_end) {
        thisaxis = fs_in.axis;
        thisbase = fs_in.end_cyl;
        frontcap = endcap;
        frontcapround = endcapround;
      }

      if (!frontcap)
        discard;

      if (frontcapround) {
        vec3 sphere_direction = thisbase - ray_origin;
        float b = dot(sphere_direction, ray_direction);
        float pos = b*b + radius2 -dot(sphere_direction, sphere_direction);
        if (pos < 0.0)
          discard;

        float near = sqrt(pos) + b;
        new_point = near * ray_direction + ray_origin;
        normal = normalize(new_point - thisbase);
      } else {
        // ray-plane intersection
        float dNV = dot(thisaxis, ray_direction);
        if (dNV < 0.0)
          discard;

        float near = dot(thisaxis, thisbase - ray_origin) / dNV;
        new_point = ray_direction * near + ray_origin;
        // within the cap radius?
        if (dot(new_point - thisbase, new_point - thisbase) > radius2)
          discard;

        normal = thisaxis;
      }
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