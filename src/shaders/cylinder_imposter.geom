#version 330 core

layout( lines ) in;
layout( triangle_strip, max_vertices = 14 ) out;
//layout( points, max_vertices = 16 ) out;

in EyeSpaceVertex {
    vec3 vertex;
    float radius;
    vec4 color;
} gs_in[];

out CylinderPoint {
    vec3 surface_point;
    vec3 axis;
    vec3 base;
    vec3 end_cyl;
    vec3 U;
    vec3 V;
    float radius;
    float inv_sqr_height;
    vec4 color;
} gs_out;

uniform mat4 projectionMatrix;
uniform mat4 modelView;
uniform mat4 viewportMatrix;
uniform mat3 modelViewNormal;
uniform mat4 mvp;

    // compute bounding box vertex position
    // static unsigned char cyl_flags[] = { 0, 4, 6, 2, 1, 5, 7, 3 }; // right(4)/up(2)/out(1) 
    // == (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
    //    (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)

    // strip order
    // { 3, 2, 6, 7, 4, 2, 0, 3, 1, 6, 5, 4, 1, 0 }
    // (0, 0, 0),

    /*
    int box_indices[36] = { // box indices 
    0, 2, 1, | 2, 0, 3, || 1, 6, 5, | 6, 1, 2, ||  0, 1, 5, | 5, 4, 0,  ||
    0, 7, 3, | 7, 0, 4, || 3, 6, 2, | 6, 3, 7, ||  4, 5, 6, | 6, 7, 4 };

    -- ( 0, 0, 0 ), (0, 1, 0), (0, 0, 1), | (0, 1, 0), (0, 0, 0), (0, 1, 1) // face 1: 0, 1, 2, 3
    -- ( 0, 0, 1 ), (1, 1, 0), (1, 0, 1), | (1, 1, 0), (0, 0, 1), (0, 1, 0) // face 2: 1, 2, 6, 5
    -- ( 0, 0, 0 ), (0, 0, 1), (1, 0, 1), | (1, 0, 1), (1, 0, 0), (0, 0, 0) // face 3: 0, 1, 4, 5
    -- ( 0, 0, 0 ), (1, 1, 1), (0, 1, 1), | (1, 1, 1), (0, 0, 0), (1, 0, 0) // face 4: 0, 3, 4, 7
    -- ( 0, 1, 1 ), (1, 1, 0), (0, 1, 0), | (1, 1, 0), (0, 1, 1), (1, 1, 1) // face 5: 2, 3, 6, 7
    -- ( 1, 0, 0 ), (1, 0, 1), (1, 1, 0), | (1, 1, 0), (1, 1, 1), (1, 0, 0) // face 6: 4, 5, 6, 7
    */

// static unsigned char cyl_flags[] = { 0, 4, 6, 2, 1, 5, 7, 3 }; // right(4)/up(2)/out(1) 
const int box_vertices[]  = int[]( 0, 4, 6, 2, 1, 5, 7, 3 );
const float box_tristrip_indices[] = float[]( 3, 7, 1, 5, 4, 7, 6, 3, 2, 1, 0, 6, 3, 5 );
//const float box_tristrip_indices[] =   float[]( );
const float idx_right[] = float[]( 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1 );
const float idx_up[] =    float[]( 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1 );
const float idx_out[] =   float[]( 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0 );

// get_bit_and_shift: returns 0 or 1
float get_bit_and_shift(inout float bits) {
  float bit = mod(bits, 2.0);
  bits = (bits - bit) / 2.0;
  return step(.5, bit);
}

void main(){
    
    vec3 attr_vertex1 = gs_in[0].vertex;
    vec3 attr_vertex2 = gs_in[1].vertex;

    vec3 attr_axis = attr_vertex2 - attr_vertex1;

    float radius = gs_in[0].radius;
    //float radius = 1;
    gs_out.radius = radius;
    gs_out.color = gs_in[0].color;

    float uniformglscale = 1;

    // calculate reciprocal of squared height
    gs_out.inv_sqr_height = length(attr_axis) / uniformglscale;
    gs_out.inv_sqr_height *= gs_out.inv_sqr_height;
    gs_out.inv_sqr_height = 1.0 / gs_out.inv_sqr_height;

    gl_Position = mvp * vec4( attr_vertex1, 1.);
    //EmitVertex();
    gl_Position = mvp * vec4( attr_vertex2, 1.);
    //EmitVertex();
    //EndPrimitive();
    //return;

    // h is a normalized cylinder axis
    vec3 h = normalize(attr_axis);
    // axis is the cylinder axis in modelview coordinates
    gs_out.axis = normalize(modelViewNormal * h);
    // u, v, h is local system of coordinates
    vec3 u = cross(h, vec3(1.0, 0.0, 0.0));
    if (dot(u,u) < 0.001) 
      u = cross(h, vec3(0.0, 1.0, 0.0));
    u = normalize(u);
    vec3 v = normalize(cross(u, h));

    // transform to modelview coordinates
    gs_out.U = normalize(modelViewNormal * u);
    gs_out.V = normalize(modelViewNormal * v);

    vec4 base4 = modelView * vec4(attr_vertex1, 1.0);
    gs_out.base = base4.xyz;
    vec4 end4 = modelView * vec4(attr_vertex2, 1.0);
    gs_out.end_cyl = end4.xyz;

    // compute properties of each of the 12 vertices of imposter box as tristrip
    //for( int i = 11; i >= 0; --i ){
    for( int i = 0; i < 14; ++i ){

        vec4 vertex = vec4(attr_vertex1, 1.0); 
        float packed_flags = box_tristrip_indices[i];
        //float out_v = get_bit_and_shift(packed_flags);
        //float up_v = get_bit_and_shift(packed_flags);
        //float right_v = get_bit_and_shift(packed_flags);
        float out_v = idx_out[i];
        float up_v = idx_up[i];
        float right_v = idx_right[i];
        vertex.xyz += up_v * attr_axis;
        vertex.xyz += (2.0 * right_v - 1.0) * radius * u;
        vertex.xyz += (2.0 * out_v - 1.0) * radius * v;
        vertex.xyz += (2.0 * up_v - 1.0) * radius * h;

        vec4 tvertex = modelView * vertex;
        gs_out.surface_point = tvertex.xyz;

        gl_Position = projectionMatrix * modelView * vertex;

        // support uniform scaling
        //gs_out.radius /= uniformglscale;

        // clamp z on front clipping plane if impostor box would be clipped.
        // (we ultimatly want to clip on the calculated depth in the fragment
        // shader, not the depth of the box face)
        if (gl_Position.z / gl_Position.w < -1.0) {
            // upper bound of possible cylinder z extend
            float diff = abs(base4.z - end4.z) + radius * 3.5;

            // z-`diff`-offsetted vertex
            vec4 inset = modelView * vertex;
            inset.z -= diff;
            inset = projectionMatrix * inset;

            // if offsetted vertex is within front clipping plane, then clamp
            if (inset.z / inset.w > -1.0) {
                gl_Position.z = -gl_Position.w;
            }
        }
        EmitVertex();
    }

    EndPrimitive();

}
