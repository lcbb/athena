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

class AABBOutline(Qt3DCore.QEntity):
    def __init__(self, parent, geom, plydata):
        super(AABBOutline, self).__init__(parent)

        print(plydata['vertex'].name, plydata['vertex'].properties)
        print(plydata['face'].name, plydata['face'].properties)

        vertices = plydata['vertex'].data
        faces = plydata['face'].data
        print(type(vertices[0][0]), vertices)
        print(vertices.ravel())
        print(type(faces[0][0][0]), faces[0][0])

        self.geometry = Qt3DRender.QGeometry(self)
        codechar = _basetype_struct_codes[_basetypes.Float]
        (min_vtx, max_vtx) = compute_AABB(geom)

        #self.qbytes = QByteArray()
        #self.qbytes.resize(3*2*_basetype_widths[_basetypes.Float])
        #struct.pack_into( codechar*6, self.qbytes, 0, min_vtx.x(), min_vtx.y(), min_vtx.z(), 
        #                                                     max_vtx.x(), max_vtx.y(), max_vtx.z() )
        #rawstring= struct.pack( codechar*6, min_vtx.x(), min_vtx.y(), min_vtx.z(), 
                                 #max_vtx.x(), max_vtx.y(), max_vtx.z() )
        rawstring = vertices.tobytes()
        print(struct.unpack('ffffff', rawstring[:24]))
        self.qvbytes = QByteArray(rawstring)

        self.qvbuf = Qt3DRender.QBuffer(self.geometry)
        self.qvbuf.setData(self.qvbytes)

        self.positionAttr = Qt3DRender.QAttribute(self.geometry)
        self.positionAttr.setName( Qt3DRender.QAttribute.defaultPositionAttributeName() )
        self.positionAttr.setVertexBaseType(_basetypes.Float)
        self.positionAttr.setVertexSize(3)
        self.positionAttr.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        self.positionAttr.setBuffer(self.qvbuf)
        self.positionAttr.setByteStride(3*_basetype_widths[_basetypes.Float])
        self.positionAttr.setCount(len(vertices))
        self.geometry.addAttribute(self.positionAttr)

        index_type = _basetypes.UnsignedShort
        total_segments = 0
        for poly in faces:
            total_segments += len(poly[0])
        index_buffer_np = np.zeros(2*total_segments, np.int16)
        idx = 0
        def poly_line_iter(poly):
            a,b = itertools.tee(poly)
            next(b, None)
            return zip(a,b)
        for poly in faces:
            indices = poly[0]
            for a, b in poly_line_iter(indices):
                index_buffer_np[idx] = a
                idx += 1
                index_buffer_np[idx] = b
                idx += 1

        #rawstring = struct.pack( _basetype_struct_codes[index_type]*4, faces[0][0][0], faces[0][0][1], faces[0][0][2], faces[0][0][0] )
        rawstring = index_buffer_np.tobytes()
        
        print(struct.unpack('HHHH',rawstring[:8]))
        #rawstring = faces.tobytes()
        self.qibytes = QByteArray(rawstring)
        self.qibuf = Qt3DRender.QBuffer(self.geometry)
        self.qibuf.setData(self.qibytes)

        self.indexAttr = Qt3DRender.QAttribute(self.geometry)
        self.indexAttr.setVertexBaseType(index_type)
        self.indexAttr.setAttributeType(Qt3DRender.QAttribute.IndexAttribute)
        self.indexAttr.setBuffer(self.qibuf)
        self.indexAttr.setCount(total_segments*2)
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

        self.renderStates = Qt3DRender.QRenderStateSet(self.rootEntity)
        self.renderStateLines = Qt3DRender.QLineWidth(self.rootEntity)
        self.renderStateLines.setSmooth(False)
        self.renderStateLines.setValue(10000)
        self.renderStates.addRenderState(self.renderStateLines)
        self.activeFrameGraph().setParent(self.renderStates)
        self.setActiveFrameGraph(self.renderStates)
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
            dumpGeometry(geom)
            print( compute_AABB( geom ) )
            if( self.aabb ):
                self.aabb.deleteLater()
            self.aabb = AABBOutline( self.rootEntity, geom, self.plydata )

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
