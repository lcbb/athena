#version 330 core

in EyeSpaceVertex{
    vec3 position;
    vec4 color;
} fs_in;

out vec4 fragColor;


void main()
{
    fragColor = fs_in.color;
}
