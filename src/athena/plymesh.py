from pathlib import Path
import struct
import itertools

from PySide2.QtCore import QByteArray, Qt
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender

from plyfile import PlyData, PlyElement
import numpy as np

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

class PlyMesh(Qt3DCore.QEntity):
    def __init__(self, parent, plydata):
        super(PlyMesh, self).__init__(parent)

        vertices = plydata['vertex'].data
        faces = plydata['face'].data['vertex_indices']

        print(vertices)
        print (faces, list(map(len,faces)))

        # Count the faces in the model that have more than 3 vertices: we will need to
        # synthesize central vertices for these.
        large_faces = [x for x in faces if len(x) > 3]
        num_large_faces = len(large_faces)
        num_tris = len(faces) - num_large_faces
        num_interior_tris = sum(len(x) for x in large_faces)

        total_vertices = len(vertices) + num_large_faces
        total_tris = num_tris + num_interior_tris
        vertex_nparr = np.zeros([total_vertices,3],dtype=_basetype_numpy_codes[_basetypes.Float])
        # Fill with the input vertices
        vertex_nparr[:len(vertices),0] = vertices['x']
        vertex_nparr[:len(vertices),1] = vertices['y']
        vertex_nparr[:len(vertices),2] = vertices['z']
        vtx_idx = len(vertices)

        tri_nparr = np.zeros([total_tris,3],dtype=_basetype_numpy_codes[_basetypes.UnsignedShort])
        tri_idx = 0

        def add_vtx(v):
            nonlocal vtx_idx
            vertex_nparr[vtx_idx,:]=v
            vtx_idx += 1
            return vtx_idx - 1

        def add_tri(t):
            nonlocal tri_idx
            print(t, type(t))
            tri_nparr[tri_idx,:]=t
            tri_idx += 1
            return tri_idx - 1

        # synthesize central vertices for large polys
        for poly in large_faces:
            poly_verts = np.take(vertex_nparr, poly, axis=0)
            print(poly_verts, type(poly_verts))
            print(np.mean(poly_verts,axis=0))
            #centroid = np.mean

        # create the index buffer
        for poly in faces:
            if( len(poly) == 3 ):
                add_tri(poly)
            else:
                poly_verts = np.take(vertex_nparr, poly, axis=0)
                centroid = np.mean(poly_verts, axis=0)
                c = add_vtx(centroid) # c = index into vertex_nparr of centroid 
                for i in range(len(poly)):
                    a = poly[i-1]
                    b = poly[i]
                    add_tri( np.array([a, b, c]) )


        # Sanity checks
        assert( vtx_idx == total_vertices )
        assert( tri_idx == total_tris )

        self.geometry = Qt3DRender.QGeometry(self)

        # Create qt3d vertex buffer
        rawstring = vertex_nparr.tobytes()
        self.qvbytes = QByteArray(rawstring)
        self.qvbuf = Qt3DRender.QBuffer(parent)
        self.qvbuf.setData(self.qvbytes)
        self.positionAttr = Qt3DRender.QAttribute(parent)
        self.positionAttr.setName( Qt3DRender.QAttribute.defaultPositionAttributeName() )
        self.positionAttr.setVertexBaseType(_basetypes.Float)
        self.positionAttr.setVertexSize(3)
        self.positionAttr.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        self.positionAttr.setBuffer(self.qvbuf)
        #self.positionAttr.setByteStride(3*_basetype_widths[_basetypes.Float])
        self.positionAttr.setCount(len(vertex_nparr))
        self.geometry.addAttribute(self.positionAttr)

        # Now create the index attribute.
        #  use the same basetype as the Qt3D mesh, since presumably that file loader chose a suitable type
        #iatt = _basetypes.UnsignedShort # getQAttribute(geom, att_type=Qt3DRender.QAttribute.IndexAttribute)
        index_type = _basetypes.UnsignedShort # iatt.vertexBaseType()
        #index_buffer_np = np.array(tri_nparr, dtype=_basetype_numpy_codes[index_type])
        rawstring = tri_nparr.tobytes()
        
        self.qibytes = QByteArray(rawstring)
        self.qibuf = Qt3DRender.QBuffer(parent)
        self.qibuf.setData(self.qibytes)

        self.indexAttr = Qt3DRender.QAttribute(self.geometry)
        self.indexAttr.setVertexBaseType(index_type)
        self.indexAttr.setAttributeType(Qt3DRender.QAttribute.IndexAttribute)
        self.indexAttr.setBuffer(self.qibuf)
        self.indexAttr.setCount(3*total_tris)
        self.geometry.addAttribute(self.indexAttr)

        self.lineMesh = Qt3DRender.QGeometryRenderer(parent)
        self.lineMesh.setGeometry(self.geometry)
        self.lineMesh.setPrimitiveType( Qt3DRender.QGeometryRenderer.Triangles )

        #self.lineMaterial = Qt3DExtras.QPhongMaterial(parent)
        #self.lineMaterial.setAmbient(QColor(255,255,0))

        #self.lineEntity = Qt3DCore.QEntity(parent)
        self.addComponent(self.lineMesh)
        #self.lineEntity.addComponent(self.lineMaterial)

