#version 330 core

layout( points ) in;
layout( triangle_strip, max_vertices = 4 ) out;


in EyeSpaceVertex {
    //vec4 sphere_center;
    float radius;
    float radius2;
    vec4 color;
} gs_in[];

out SphereVertex {
    vec3 sphere_center;
    vec3 point;
    float radius2;
    vec4 color;
} gs_out;

uniform mat4 projectionMatrix;
uniform mat4 viewportMatrix;
uniform mat3 modelViewNormal;

/*
 * horizontial and vertical adjustment of outer tangent hitting the
 * impostor quad, in model view space.
 */
vec2 outer_tangent_adjustment(vec3 center, float radius_sq) {
    vec2 xy_dist = vec2(length(center.xz), length(center.yz));

    // without clamping, this caused flickering (divide-by-zero)
    vec2 cos_a = clamp(center.z / xy_dist, -1., 1.);
    vec2 cos_b = xy_dist / sqrt(radius_sq + (xy_dist * xy_dist));

    // numerically more stable version of:
    // vec2 tan_ab_sq = pow(tan(acos(cos_b) + acos(cos_a)), 2);
    vec2 cos_ab = (cos_a * cos_b + sqrt(
                (1. - cos_a * cos_a) *
                (1. - cos_b * cos_b)));
    vec2 cos_ab_sq = cos_ab * cos_ab;
    vec2 tan_ab_sq = (1. - cos_ab_sq) / cos_ab_sq;

    vec2 adjustment = sqrt(tan_ab_sq + 1.);

    // max out (empirical) to avoid exploding (can happen for spheres outside of the viewport)
    return min(adjustment, 10.);
}

/*
vec4 imposter_corner( vec4 tmppos, float radius, float radius2, vec2 corner_offset ){
    corner_offset *= outer_tangent_adjustment(tmppos.xyz, radius2);
    vec4 eye_space_pos = tmppos;
    eye_space_pos.xy += radius * corner_offset;
    return eye_space_pos;
}*/

void main()
{

    vec4 tmppos = gl_in[0].gl_Position;
    gs_out.sphere_center = tmppos.xyz / tmppos.w;
    gs_out.radius2 = gs_in[0].radius2;
    gs_out.color = gs_in[0].color;
    float radius = gs_in[0].radius;

    vec2 ot_adjust = outer_tangent_adjustment( tmppos.xyz, gs_in[0].radius2 );

    // corner -1, -1
    vec2 corner_offset = ot_adjust * vec2(-radius, -radius);
    vec4 eye_space_pos = tmppos;
    eye_space_pos.xy += corner_offset;
    gs_out.point = eye_space_pos.xyz / eye_space_pos.w;
    gl_Position = projectionMatrix * eye_space_pos;
    EmitVertex();

    // corner 1, -1
    corner_offset = ot_adjust * vec2(radius, -radius);
    eye_space_pos = tmppos;
    eye_space_pos.xy += corner_offset;
    gs_out.point = eye_space_pos.xyz / eye_space_pos.w;
    gl_Position = projectionMatrix * eye_space_pos;
    EmitVertex();

    // corner -1, 1
    corner_offset = ot_adjust * vec2(-radius, radius);
    eye_space_pos = tmppos;
    eye_space_pos.xy += corner_offset;
    gs_out.point = eye_space_pos.xyz / eye_space_pos.w;
    gl_Position = projectionMatrix * eye_space_pos;
    EmitVertex();

    // corner 1, 1
    corner_offset = ot_adjust * vec2(radius, radius);
    eye_space_pos = tmppos;
    eye_space_pos.xy += corner_offset;
    gs_out.point = eye_space_pos.xyz / eye_space_pos.w;
    gl_Position = projectionMatrix * eye_space_pos;
    EmitVertex();

    EndPrimitive();

}
