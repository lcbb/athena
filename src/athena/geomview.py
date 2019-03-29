from pathlib import Path
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

from athena import ATHENA_SRC_DIR

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

def getQAttribute( geom, att_type=Qt3DRender.QAttribute.VertexAttribute, att_name=None ):
    for att in geom.attributes():
        if att.attributeType() == att_type and (att_name is None or att.name() == att_name):
            return att
    return None

class WireOutline(Qt3DCore.QEntity):
    def __init__(self, parent, geom, plydata):
        super(WireOutline, self).__init__(parent)

        vertices = plydata['vertex'].data
        faces = plydata['face'].data

        self.geometry = Qt3DRender.QGeometry(self)

        # The xyz position attribute: recorded here is the way to generate it from the plyfile data.
        # In practice, the resultng buffer has always been identical to the vertex buffer from
        # Qt3D's polygon mesh (which was, after all, created from the same file), so we are just
        # going to borrow that buffer below instead of creating a whole new QAttribute/QBuffer.
        # But I'm keeping this commented code here in case it proves needful in the future.
        #rawstring = vertices.tobytes()
        #self.qvbytes = QByteArray(rawstring)
        #self.qvbuf = Qt3DRender.QBuffer(self.geometry)
        #self.qvbuf.setData(self.qvbytes)
        #self.positionAttr = Qt3DRender.QAttribute(self.geometry)
        #self.positionAttr.setName( Qt3DRender.QAttribute.defaultPositionAttributeName() )
        #self.positionAttr.setVertexBaseType(_basetypes.Float)
        #self.positionAttr.setVertexSize(3)
        #self.positionAttr.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        #self.positionAttr.setBuffer(self.qvbuf)
        #self.positionAttr.setByteStride(3*_basetype_widths[_basetypes.Float])
        #self.positionAttr.setCount(len(vertices))
        #self.geometry.addAttribute(self.positionAttr)

        # Instead of the above, borrow the position attribute buffer from geom
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

        self.lineMaterial = Qt3DExtras.QPhongMaterial(parent)
        self.lineMaterial.setAmbient(QColor(255,255,0))

        self.lineEntity = Qt3DCore.QEntity(parent)
        self.lineEntity.addComponent(self.lineMesh)
        self.lineEntity.addComponent(self.lineMaterial)




class AthenaGeomView(Qt3DExtras.Qt3DWindow):
    def __init__(self):
        super(AthenaGeomView, self).__init__()

        self.defaultFrameGraph().setClearColor( QColor(63, 63, 63) )
        self.renderSettings().setRenderPolicy(self.renderSettings().OnDemand)

        self.reset2DCamera()

        self.rootEntity = Qt3DCore.QEntity()


        # Load
        self.eee = QQmlEngine()
        main_qml = Path(ATHENA_SRC_DIR) / 'qml' / 'main.qml'
        self.ccc = QQmlComponent(self.eee, main_qml.as_uri() )
        #print(self.ccc.errorString())
        self.material = self.ccc.create()
        # We must set the shader program paths here, because qml doesn't know where ATHENA_DIR is

        self.shader = Qt3DRender.QShaderProgram()
        shader_path = Path(ATHENA_SRC_DIR) / 'shaders' / 'robustwireframe'
        def loadShader(suffix):
            return Qt3DRender.QShaderProgram.loadSource( shader_path.with_suffix( suffix ).as_uri() )
        self.shader.setVertexShaderCode( loadShader( '.vert' ) )
        self.shader.setGeometryShaderCode( loadShader( '.geom' ) )
        self.shader.setFragmentShaderCode( loadShader( '.frag' ) )
        pass0 = self.material.effect().techniques()[0].renderPasses()[0]
        pass0.setShaderProgram(self.shader)

        self.material = Qt3DExtras.QGoochMaterial(self.rootEntity)
        self.material.setDiffuse( QColor(200, 200, 200) )

        self.meshEntity = Qt3DCore.QEntity(self.rootEntity)
        self.displayMesh = Qt3DRender.QMesh(self.rootEntity)
        self.meshEntity.addComponent( self.displayMesh )
        self.meshEntity.addComponent( self.material )

        #self.activeFrameGraph().addRenderSettings(self.renderStates)
        #self.activeFrameGraph().add
        #self.renderSettings.setActiveFrameGraph(self.renderStates)
        #self.rootEntity.addComponent(self.)

        self.setRootEntity(self.rootEntity)

        self.lastpos = None
        self.aabb = None

        self.displayMesh.statusChanged.connect(self.meshChange)
        self.displayMesh.geometryChanged.connect(self.meshChange)

    def reloadGeom(self, filepath, mesh_3d, cam_distance = None):
        self.meshFilepath = filepath
        self.displayMesh.setSource( QUrl.fromLocalFile(str(filepath)) )
        self.plydata = PlyData.read(filepath)
        if (mesh_3d):
            self.reset3DCamera(cam_distance)
        else:
            self.reset2DCamera()

    def meshChange( self ):
        print(self.displayMesh.source(), self.displayMesh.status())
        if self.displayMesh.status() == Qt3DRender.QMesh.Ready:
            geom = self.displayMesh.geometry()
            #dumpGeometry(geom)
            if( self.aabb ):
                self.aabb.deleteLater()
            self.aabb = WireOutline( self.rootEntity, geom, self.plydata )

    def reset2DCamera( self ):
        self.camera_3d = False
        ratio = self.width() / self.height()
        x = 100 * ratio
        self.camera().lens().setOrthographicProjection( -x, x, -100, 100, -100, 100 )
        self.camera().setPosition( vec3d( 0, 0, 0 ) )
        self.camera().setViewCenter( vec3d( 0, 0, -100) )
        self.camera().rightVector = vec3d( 1, 0, 0 )
        self.orientCamera()

    def reset3DCamera( self, cam_distance ):
        if cam_distance == None: cam_distance = 5
        self.camera_3d = True
        ratio = self.width() / self.height()
        self.camera().lens().setPerspectiveProjection(45, ratio, .01, 1000)
        self.camera().setPosition( vec3d( cam_distance, 0, 0 ) )
        self.camera().setViewCenter( vec3d( 0, 0, 0) )
        self.camera().rightVector = vec3d( 0, 1, 0 )
        self.orientCamera()

    def orientCamera( self ):
        # Set the camera up vector based on our tracking of the right vector
        view_vec = self.camera().viewCenter() - self.camera().position()
        up = vec3d.crossProduct( self.camera().rightVector, view_vec )
        self.camera().setUpVector( up.normalized() )
        
    def rotateCamera( self, delta_x, delta_y ):
        # Rotate camera based on mouse-drag inputs
        ctr = self.camera().viewCenter()
        up = ATHENA_GEOM_UP
        v = self.camera().position() - ctr 
        right = self.camera().rightVector
        v = rotateAround( v, right, -delta_y )
        v = rotateAround( v, up, -delta_x )
        self.camera().setPosition ( (ctr + v) )
        self.camera().rightVector = rotateAround( right, up, -delta_x )
        self.orientCamera()

    def moveCamera( self, delta_x, delta_y ):
        self.camera().translateWorld( vec3d( -delta_x/3., delta_y/3., 0 ), self.camera().TranslateViewCenter )
        #ctr = self.camera().viewCenter()
        #self.camera().setViewCenter( ctr + vec3d( -delta_x, delta_y, 0 ) )
        #pos = self.camera().position()
        #self.camera().setPosition( pos + vec3d( -delta_x, delta_y, 0 ) )


    def mouseMoveEvent(self, event):
        if( self.lastpos ):
            delta = event.pos()-self.lastpos
            if( event.buttons() == Qt.LeftButton ):
                if self.camera_3d :
                    self.rotateCamera( delta.x(), delta.y() )
                else:
                    self.moveCamera( delta.x(), delta.y() )
        self.lastpos = event.pos()

    def wheelEvent( self, event ):
        delta = event.angleDelta() / 25
        fov = self.camera().fieldOfView()
        def clamp(min_, max_, value):
            return min( max( value, min_ ), max_ )
        new_fov = clamp (5, 150, fov - delta.y())
        self.camera().setFieldOfView( new_fov )

    def resizeEvent( self, event ):
        newsize = event.size()
        ratio = newsize.width() / newsize.height()
        if self.camera_3d:
            self.camera().setAspectRatio( ratio )
        else:
            self.reset2DCamera()
