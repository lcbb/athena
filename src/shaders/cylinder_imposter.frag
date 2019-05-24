#version 330 core


in CylinderPoint {
    vec3 surface_point;
    vec3 axis;
    vec3 base;
    vec3 end_cyl;
    vec3 U;
    vec3 V;
    float radius;
    float cap;
    float inv_sqr_height;
    vec4 color;
} fs_in;

out vec4 fragColor;

void main()
{
    fragColor = fs_in.color;
}
