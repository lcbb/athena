#version 330 core

in SphereVertex {
    vec3 sphere_center;
    vec3 point;
    float radius2;
} fs_in;

out vec4 fragColor;

void main()
{
    fragColor = vec4(0, 1, 0, 1);
}
