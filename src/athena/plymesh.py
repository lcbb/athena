from pathlib import Path
import struct
import itertools

from PySide2.QtGui import QColor, QVector3D as vec3d
from PySide2.QtCore import QByteArray, Qt
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DExtras import Qt3DExtras

from plyfile import PlyData, PlyElement
import numpy as np
from numpy.lib.recfunctions import repack_fields

from athena import geom
from earcut import earcut

def tri_norm(a,b,c):
    tri_normal = np.cross( a-b, a-c)
    tri_normal /= np.linalg.norm(tri_normal)
    return tri_normal

def edge( a, b ):
    return (min(a,b), max(a,b))

def edgeIter(poly):
    it = iter(poly)
    i0 = next(it)
    i_last = i0
    for i in it:
        yield edge( i_last, i )
        i_last = i
    yield edge( i_last, i0 )

def sharedEdges(poly, vtx):
    for a, b in edgeIter(poly):
        if vtx == a:
            yield b
        elif vtx == b:
            yield a

class PlyMesh(Qt3DCore.QEntity):
    '''
    QEntity for the 2D or 3D, wireframe-girt polygonal meshes
    that are the main display object of Athena.
    '''
    def __init__(self, parent, plydata):
        super().__init__(parent)

        ply_vertices = plydata['vertex'].data
        ply_faces = plydata['face'].data['vertex_indices']

        # The ply reader library returns the vertex data in numpy structured arrays,
        # which wind up being annoying to access manually, so define a convenience
        # lookup function here.
        # FIXME A lot of probably-unnecessary copying of numpy data takes place here,
        # causing loader slowness on very large ply models.
        def vertex(indices):
            vertices = np.take(ply_vertices, indices, axis=0)
            fields = ['x', 'y', 'z'] # Ignore any othe per-vertex values
            return np.r_[ [v[fields].item() for v in vertices] ]

        flat_xy = np.all( 0 == ply_vertices['z'] )
        self.dimensions = 2 if flat_xy else 3

        vertices = list()
        triangles = list()

        def add_vtx(v, a, b):
            vertices.append( np.hstack( [v , a , b] ) )
            return len(vertices) - 1

        # Each vertex in the mesh has nine coordinates:
        # The xyz coordinates of the vertex itself, and
        # the xyz coordinates of the two points adjacent to that
        # vertex in the wireframe mesh.  (The vertex shader refers to these
        # as wing1Vtx and wing2Vtx).  For a triangular face, a vertex's
        # two wing vertices are simply the other two vertices of the triangle.
        # add_simple_tri covers this case

        def add_simple_tri( *args ):
            A, B, C = vertex( args )
            i = add_vtx(A, B, C)
            j = add_vtx(B, A, C)
            k = add_vtx(C, A, B)
            triangles.append( (i, j, k) )

        # For non-triangular faces, we generate triangles (in the loop below),
        # and store each vertex with its adjacent edge vertices as its wing value.
        # This assumes that all triangle vertices fall on the boundary of a polygon
        # face, which seems to be a valid assumption for triangulations produced
        # by the earcut library.

        def add_complex_tri( a, b, c, poly ):
            def add_vertex_with_edges( x ):
                e1, e2 = tuple( x for x in sharedEdges(poly, x) )
                return add_vtx( *vertex( (x, e1, e2) ) )
            i = add_vertex_with_edges( a )
            j = add_vertex_with_edges( b )
            k = add_vertex_with_edges( c )
            triangles.append( (i, j, k) )

        for poly in ply_faces:
            if len(poly) == 3:
                add_simple_tri( *poly )
            else:
                external_edges = set( edgeIter( poly ) )
                assert( len(external_edges) == len(poly) )
                poly_geom = vertex(poly)
                # Compute the normal of this polygon from the first three verts;
                # we'll need this later to determine winding direction for the
                # triangulated faces
                poly_normal = tri_norm( *(poly_geom[x,:] for x in range(3)) )
                # Geometric centroid of the polygon
                G = np.average( poly_geom, axis=0 )
                offset_geom = poly_geom - G
                # Singular value decomposition: we want to map the 3D coordinates
                # to a 2D subspace that can be fed into a 2D triangulation algorithm.
                # For this we only need the last return value.
                _, _, vh = np.linalg.svd(offset_geom)
                vt = vh[:2,:].T
                xy_coords = np.dot(offset_geom, vt)
                flattened = earcut.flatten([xy_coords,[]])
                new_tris = earcut.earcut(flattened['vertices'],None,flattened['dimensions'])

                # Now we have the new triangles from earcut.
                # Check the first one's normal; if it doesn't match the polygon normal,
                # then we'll assume the 2D projection reversed our triangle windings.
                geom_tri0 = poly_geom.take(new_tris[0:3], axis=0)
                tri0_norm = tri_norm(*(geom_tri0[x,:] for x in range(3)))
                normcheck = np.dot(tri0_norm, poly_normal)
                flip = False
                if( not np.isclose(normcheck, 1.0, rtol=1e-1) ):
                    flip = True

                # Now add new triangles to the buffers
                for a,b,c in geom.grouper(new_tris,3):
                    idx_a = poly[a]
                    idx_b = poly[b]
                    idx_c = poly[c]
                    if( flip ): 
                        idx_b, idx_c = idx_c, idx_b
                    add_complex_tri( idx_a, idx_b, idx_c, poly )

        vertex_basetype = geom.basetypes.Float
        if( len(triangles) < 30000 ):
            index_basetype = geom.basetypes.UnsignedShort
        else:
            index_basetype = geom.basetypes.UnsignedInt

        vertex_nparr = np.array(vertices, dtype = geom.basetype_numpy_codes[vertex_basetype])

        index_nparr = np.array( triangles, dtype=geom.basetype_numpy_codes[index_basetype])

        self.geometry = Qt3DRender.QGeometry(self)

        # Setup vertex attributes for position and interior flags
        position_attrname = Qt3DRender.QAttribute.defaultPositionAttributeName()
        wing1_attrname = 'wing1Vtx'
        wing2_attrname = 'wing2Vtx'

        attrspecs = [ geom.AttrSpec(position_attrname, column=0, numcols=3 ),
                      geom.AttrSpec(wing1_attrname, column=3, numcols=3),
                      geom.AttrSpec(wing2_attrname, column=6, numcols=3) ]
        self.posAttr, self.wing1Attr, self.wing2Attr = geom.buildVertexAttrs( parent, vertex_nparr, attrspecs )
        self.geometry.addAttribute(self.posAttr)
        self.geometry.addAttribute(self.wing1Attr)
        self.geometry.addAttribute(self.wing2Attr)

        self.indexAttr = geom.buildIndexAttr( parent, index_nparr )
        self.geometry.addAttribute(self.indexAttr)

        self.lineMesh = Qt3DRender.QGeometryRenderer(parent)
        self.lineMesh.setGeometry(self.geometry)
        self.lineMesh.setPrimitiveType( Qt3DRender.QGeometryRenderer.Triangles )

        self.addComponent(self.lineMesh)

