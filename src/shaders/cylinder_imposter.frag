#version 330 core

in CylinderPoint {
    vec3 point;
    vec4 color;
} fs_in;

out vec4 fragColor;

void main()
{
    fragColor = vec4(0, 1, 0, 1);
}
