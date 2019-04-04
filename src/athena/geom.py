import struct
import itertools

from plyfile import PlyData, PlyElement
import numpy as np

from PySide2.QtGui import QColor, QQuaternion, QVector3D as vec3d
from PySide2.QtCore import QUrl, QByteArray, Qt
from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DCore import Qt3DCore
from PySide2.QtQml import QQmlEngine, QQmlComponent

from athena import plymesh

ATHENA_GEOM_UP = vec3d(0, 0, 1)

def rotateAround( v1, v2, angle ):
    q = QQuaternion.fromAxisAndAngle( v2, angle )
    return q.rotatedVector( v1 )

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

def iterAttr( att ):
    '''Iterator over a Qt3DRender.QAttribute'''
    basetype = att.vertexBaseType()
    width = _basetype_widths[ basetype ]
    struct_code = _basetype_struct_codes[ basetype ]
    att_data = att.buffer().data().data()
    byteOffset = att.byteOffset()
    byteStride = att.byteStride()
    count = att.count()
    vertex_size = att.vertexSize()
    #print( width, struct_code, byteOffset, byteStride, vertex_size, count )
    if byteStride == 0:
        byteStride = width
    if vertex_size == 0:
        vertex_size = width
    for i in range (byteOffset, byteOffset + byteStride * count, byteStride ):
        datum = [ struct.unpack( struct_code, bytes(att_data[ i + (j*width) : i+(j*width)+width ]) )[0] for j in range(vertex_size) ]
        yield datum

def grouper(i, n):
    '''from the itertools recipe list: yield n-sized lists of items from iterator i'''
    return iter( lambda: list(itertools.islice(iter(i), n)), [])

def getVertexAttr( geom ):
    atts = geom.attributes()
    for att in atts:
        if att.name() == "vertexPosition" and att.attributeType() == Qt3DRender.QAttribute.AttributeType.VertexAttribute:
            return att
    return None


def dumpGeometry( geom, dumpf=print ):
    if geom is None:
        dumpf( "No geometry" )
        return
    atts = geom.attributes()
    for att in atts:
        att_type = att.attributeType()
        basetype = att.vertexBaseType()
        dumpf('{type} "{name}" '.format( type=str(att_type).split('AttributeType.')[-1], name=att.name()), end='' )
        dumpf( 'with base type {basetype}'.format(basetype = str(basetype).split('BaseType.')[-1]) )
        width = _basetype_widths[ basetype ]
        code = _basetype_struct_codes[ basetype ]

        if( att_type == Qt3DRender.QAttribute.AttributeType.VertexAttribute ):
            for vtx in iterAttr( att ):
                dumpf(vtx)
        elif att_type == Qt3DRender.QAttribute.AttributeType.IndexAttribute :
            count = att.count()
            num_tris = int(count / 3)
            dumpf( num_tris, "triangles" )
            for tri in grouper(iterAttr(att), 3):
                dumpf(tri)


def compute_AABB( geom ):
    vertices = getVertexAttr(geom)
    minimums = vec3d()
    maximums = vec3d()
    for vtx in iterAttr(vertices):
        minimums.setX( min( minimums.x(), vtx[0] ) )
        minimums.setY( min( minimums.y(), vtx[1] ) )
        minimums.setZ( min( minimums.z(), vtx[2] ) )
        maximums.setX( max( maximums.x(), vtx[0] ) )
        maximums.setY( max( maximums.y(), vtx[1] ) )
        maximums.setZ( max( maximums.z(), vtx[2] ) )
    return (minimums, maximums)




