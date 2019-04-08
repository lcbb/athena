from pathlib import Path
import struct
import itertools

from PySide2.QtCore import QByteArray, Qt
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender

from plyfile import PlyData, PlyElement
import numpy as np

from athena import geom
from earcut import earcut

# The base types enumeration
_basetypes = Qt3DRender.QAttribute.VertexBaseType

# Map from the enumeration to (byte_width, struct_code) pairs
# This dict is unzipped into two convenience dicts below.
_basetype_data = { _basetypes.Byte : (1,'b'), _basetypes.UnsignedByte : (1,'B'),
                     _basetypes.Short: (2, 'h'), _basetypes.UnsignedShort : (2,'H'),
                     _basetypes.Int  : (4, 'i'), _basetypes.UnsignedInt : (4,'I'),
                     _basetypes.HalfFloat : (2, 'e'),
                     _basetypes.Float : (4, 'f'),
                     _basetypes.Double : (8, 'd') }

# Map of Qt3D base types to byte widths
_basetype_widths = { k: v[0] for k,v in _basetype_data.items()}

# Map of Qt3D base types to codes for struct.unpack
_basetype_struct_codes = { k: v[1] for k,v in _basetype_data.items()}

# Map of Qt3D base types to numpy types
_basetype_numpy_codes = { k: np.sctypeDict[v] for k,v in _basetype_struct_codes.items()}

def tri_norm(a,b,c):
    tri_normal = np.cross( a-b, a-c)
    tri_normal /= np.linalg.norm(tri_normal)
    return tri_normal

class PlyMesh(Qt3DCore.QEntity):
    def __init__(self, parent, plydata):
        super(PlyMesh, self).__init__(parent)

        vertices = plydata['vertex'].data
        faces = plydata['face'].data['vertex_indices']

        # Count the faces in the model that have more than 3 vertices: we will need to
        # synthesize central vertices for these.
        large_faces = [x for x in faces if len(x) > 3]
        num_large_faces = len(large_faces)
        num_tris = len(faces) - num_large_faces
        num_interior_tris = sum(len(x) for x in large_faces)

        total_vertices = len(vertices) + num_large_faces
        total_tris = num_tris + num_interior_tris

        vertex_basetype = _basetypes.Float
        if( total_tris < 30000 ):
            index_basetype = _basetypes.UnsignedShort
        else:
            index_basetype = _basetypes.UnsignedInt

        vertex_nparr = np.zeros([total_vertices,7],dtype=_basetype_numpy_codes[vertex_basetype])
        # Fill with the input vertices
        vertex_nparr[:len(vertices),0] = vertices['x']
        vertex_nparr[:len(vertices),1] = vertices['y']
        vertex_nparr[:len(vertices),2] = vertices['z']
        vtx_idx = len(vertices)

        tri_nparr = np.zeros([total_tris,3],dtype=_basetype_numpy_codes[index_basetype])
        tri_idx = 0

        def add_vtx(v,interior=1):
            nonlocal vtx_idx
            vertex_nparr[vtx_idx,:]=v
            vertex_nparr[vtx_idx,6] = interior
            #print("New vtx:", vertex_nparr[vtx_idx])
            vtx_idx += 1
            return vtx_idx - 1

        def add_tri(t):
            nonlocal tri_idx
            tri_nparr[tri_idx,:]=t
            tri_idx += 1
            return tri_idx - 1

        # create the index buffer and any needed internal vertices
        for poly in faces:
            if( len(poly) == 3 ):
                add_tri(poly)
            else:
                poly_verts = np.take(vertex_nparr, poly, axis=0)
                poly_geom = np.c_[ poly_verts[:,0:3] ]#, np.ones(poly_verts.shape[0]) ]
                poly_normal = tri_norm( *(poly_geom[x,:] for x in range(3)) )
                G = poly_geom.sum(axis=0) / poly_geom.shape[0]
                u, s, vh = np.linalg.svd(poly_geom - G, full_matrices=True ) #- G)
                xvec = vh[0,:]
                yvec = vh[1,:]
                norm = vh[2,:]
                #flip = False
                #if( not np.allclose(norm[:3],poly_normal) ):
                    #print('flip', norm, poly_normal, "dot", np.dot(norm, poly_normal) )
                    #print(poly_geom)
                    #print(u)
                    #print(s)
                    #print(vh)
                    ##flip = True
                    #import code
                    #code.InteractiveConsole(locals=locals()).interact()
                    #xvec *= -1
                    #yvec *= -1
                #print( 's vh', s, vh )
                #print( 'components', xvec, yvec, norm, poly_normal)
                #xy_coords = np.dot(poly_geom-G, np.c_[xvec,yvec])
                vt = vh[:2,:].T
                xy_coords = np.dot(poly_geom-G, vt)
                print(xy_coords)
                flattened = earcut.flatten([xy_coords,[]])
                #print(flattened)
                new_tris = earcut.earcut(flattened['vertices'],None,flattened['dimensions'])

                tri0 = new_tris[0:3]
                geom_tri0 = poly_geom.take(tri0, axis=0)
                tri0_norm = tri_norm(*(geom_tri0[x,:] for x in range(3)))
                print('tri0', geom_tri0,'norm=',tri0_norm)
                normcheck = np.dot(tri0_norm, poly_normal)
                flip = False
                if( not np.isclose(normcheck, 1.0) ):
                    flip = True
                print('normcheck', normcheck)
                
                #print(list(iter(geom.grouper(new_tris,3))))
                for a,b,c in geom.grouper(new_tris,3):
                    idx_a = poly[a]
                    idx_b = poly[b]
                    idx_c = poly[c]
                    if( flip ): 
                        idx_b = poly[c]
                        idx_c = poly[b]

                    print(a,b,c,idx_a,idx_b,idx_c)
                    add_tri(np.array([idx_a,idx_b,idx_c]))
                #centroid = np.mean(poly_verts, axis=0)
                #c = add_vtx(centroid) # c is the index into vertex_nparr of new centroid vertex
                #for i in range(len(poly)):
                    #a = poly[i-1]
                    #b = poly[i]
                    #add_tri( np.array([a, b, c]) )


        # Sanity checks
        #assert( vtx_idx == total_vertices )
        #assert( tri_idx == total_tris )

        self.geometry = Qt3DRender.QGeometry(self)

        # Create qt3d vertex buffers
        rawstring = vertex_nparr.tobytes()
        self.qvbytes = QByteArray(rawstring)
        self.qvbuf = Qt3DRender.QBuffer(parent)
        self.qvbuf.setData(self.qvbytes)

        # Position attribute
        self.positionAttr = Qt3DRender.QAttribute(parent)
        self.positionAttr.setName( Qt3DRender.QAttribute.defaultPositionAttributeName() )
        self.positionAttr.setVertexBaseType(vertex_basetype)
        self.positionAttr.setVertexSize(3)
        self.positionAttr.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        self.positionAttr.setBuffer(self.qvbuf)
        self.positionAttr.setByteStride(7*_basetype_widths[vertex_basetype])
        self.positionAttr.setCount(len(vertex_nparr))
        self.geometry.addAttribute(self.positionAttr)

        # Interior attribute
        self.interiorAttr = Qt3DRender.QAttribute(parent)
        self.interiorAttr.setName( 'vertexInterior' )
        self.interiorAttr.setVertexBaseType(vertex_basetype)
        self.interiorAttr.setVertexSize(1)
        self.interiorAttr.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        self.interiorAttr.setBuffer(self.qvbuf)
        self.interiorAttr.setByteStride(7*_basetype_widths[vertex_basetype])
        self.interiorAttr.setByteOffset(6*_basetype_widths[vertex_basetype])
        self.interiorAttr.setCount(len(vertex_nparr))
        self.geometry.addAttribute(self.interiorAttr)

        rawstring = tri_nparr.tobytes()
        
        self.qibytes = QByteArray(rawstring)
        self.qibuf = Qt3DRender.QBuffer(parent)
        self.qibuf.setData(self.qibytes)

        self.indexAttr = Qt3DRender.QAttribute(self.geometry)
        self.indexAttr.setVertexBaseType(index_basetype)
        self.indexAttr.setAttributeType(Qt3DRender.QAttribute.IndexAttribute)
        self.indexAttr.setBuffer(self.qibuf)
        self.indexAttr.setCount(3*total_tris)
        self.geometry.addAttribute(self.indexAttr)

        self.lineMesh = Qt3DRender.QGeometryRenderer(parent)
        self.lineMesh.setGeometry(self.geometry)
        self.lineMesh.setPrimitiveType( Qt3DRender.QGeometryRenderer.Triangles )

        self.addComponent(self.lineMesh)




class WireOutline(Qt3DCore.QEntity):
    # This is a lines-based outline renderer, not currently used
    def __init__(self, parent, geom, plydata):
        super(WireOutline, self).__init__(parent)

        vertices = plydata['vertex'].data
        faces = plydata['face'].data

        self.geometry = Qt3DRender.QGeometry(self)

        # borrow the position attribute buffer from geom
        vatt = getQAttribute( geom, att_name = Qt3DRender.QAttribute.defaultPositionAttributeName() )
        self.geometry.addAttribute(vatt)

        # Now create the index attribute.  This is different from the Qt3D mesh, which has been triangulated,
        # so we'll need to iterate over the .ply faces and build up our own buffer.

        def edge_index_iter():
            '''Iterate all pairs of connected vertices (i.e. all edges) in the faces structure

            May repeat edges.  Returns (x,y) pairs with x always less than y.
            '''
            for poly in faces:
                indices = poly[0]
                it = iter(indices)
                i0 = next(it)
                i_last = i0
                for i in it:
                    pair = (min(i_last, i), max(i_last, i))
                    i_last = i
                    yield pair
                yield (min(i_last,i0), max(i_last,i0))

        unique_edges = set(pair for pair in edge_index_iter())

        #  use the same basetype as the Qt3D mesh, since presumably that file loader chose a suitable type
        iatt = getQAttribute(geom, att_type=Qt3DRender.QAttribute.IndexAttribute)
        index_type = iatt.vertexBaseType()
        index_buffer_np = np.array(list(unique_edges), dtype=_basetype_numpy_codes[index_type])
        rawstring = index_buffer_np.tobytes()
        
        self.qibytes = QByteArray(rawstring)
        self.qibuf = Qt3DRender.QBuffer(self.geometry)
        self.qibuf.setData(self.qibytes)

        self.indexAttr = Qt3DRender.QAttribute(self.geometry)
        self.indexAttr.setVertexBaseType(index_type)
        self.indexAttr.setAttributeType(Qt3DRender.QAttribute.IndexAttribute)
        self.indexAttr.setBuffer(self.qibuf)
        self.indexAttr.setCount(index_buffer_np.size)
        self.geometry.addAttribute(self.indexAttr)

        self.lineMesh = Qt3DRender.QGeometryRenderer(parent)
        self.lineMesh.setGeometry(self.geometry)
        self.lineMesh.setPrimitiveType( Qt3DRender.QGeometryRenderer.Lines )

        #self.lineMaterial = Qt3DExtras.QPhongMaterial(parent)
        #self.lineMaterial.setAmbient(QColor(255,255,0))

        #self.lineEntity = Qt3DCore.QEntity(parent)
        self.addComponent(self.lineMesh)
        #self.lineEntity.addComponent(self.lineMaterial)
