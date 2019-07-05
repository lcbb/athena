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
uniform float proj_orthographic;

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

    if( proj_orthographic > 0.5 ){
        ray_direction = vec3(0., 0, 1);
        ray_origin = fs_in.surface_point;
    }

    // refer to the helpful derivation at 
    // http://www.illusioncatalyst.com/notes_files/mathematics/line_cone_intersection.php

    float len = length(fs_in.end_cyl - fs_in.base);
    float radius2 = fs_in.radius * fs_in.radius;
    float m = (radius2) / ( len * len );

    vec3 v = ray_direction;
    vec3 w = ray_origin - fs_in.end_cyl;
    vec3 h = fs_in.axis;
    vec3 H = fs_in.end_cyl - fs_in.base;

    float vdoth = dot( v, h );
    float vdoth2 = vdoth * vdoth;
    float wdoth = dot( w, h );
    float wdoth2 = wdoth * wdoth;

    float a = dot( v, v ) - m * vdoth2 - vdoth2;
    float b = 2 * ( dot( v, w ) - m * vdoth * wdoth - vdoth*wdoth );
    float c = dot( w, w ) - m * (wdoth2) - wdoth2;
    float d = b*b - 4 * a *c;

    vec4 color = fs_in.color;

    if (d < 0.0){
        // outside of the cone
        discard;
    }

    float dist = (-b + sqrt(d)) / (2 * a);

    // point of intersection on cone surface
    vec3 new_point = ray_origin + dist * ray_direction;
    vec3 tmp_point = fs_in.end_cyl - new_point;
    vec3 tangent = -cross( tmp_point, fs_in.axis ); // tangent to cone
    vec3 normal = normalize( cross( tmp_point, tangent ) ); 

    bool in_cone = true;
    float HH = dot( (new_point - fs_in.base) , h );
    if( HH < 0 || HH > length(H) ) { in_cone = false; }

    // now test for intersection with the base cap
    bool in_base = false;
    vec3 thisaxis = -fs_in.axis;
    vec3 thisbase = fs_in.base;

    // ray-plane intersection
    float dNV = dot(thisaxis, ray_direction);
    if (dNV >= 0.0 ){
        float cap_dist = dot( thisaxis, thisbase - ray_origin) / dNV;
        vec3 cap_point = ray_direction * cap_dist + ray_origin;
        if( dot(cap_point - thisbase, cap_point - thisbase) <= radius2 ){
            if( cap_dist < dist || in_cone == false ){
                new_point = cap_point;
                normal = thisaxis;
                in_base = true;
            }
        }
    }
    if( in_base == false && in_cone == false ){
        discard;
    }

    vec2 clipZW = new_point.z * projectionMatrix[2].zw +
        projectionMatrix[3].zw;

    float depth = 0.5 + 0.5 * clipZW.x / clipZW.y;

    // front clipping
    if (depth <= 0.0)
      discard;

    gl_FragDepth = depth;
    fragColor = color * min(1, dot(ray_direction, normal));

}
