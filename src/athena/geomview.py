from pathlib import Path
import struct

from PySide2.QtGui import QColor, QQuaternion, QVector3D as vec3d
from PySide2.QtCore import QUrl, Qt
from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DCore import Qt3DCore
from PySide2.QtQml import QQmlEngine, QQmlComponent

from athena import ATHENA_SRC_DIR

ATHENA_GEOM_UP = vec3d(0, 0, 1)

def rotateAround( v1, v2, angle ):
    q = QQuaternion.fromAxisAndAngle( v2, angle )
    return q.rotatedVector( v1 )

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
        if( basetype == Qt3DRender.QAttribute.VertexBaseType.Float ):
            width = 4
            code = 'f'
        elif( basetype == Qt3DRender.QAttribute.VertexBaseType.UnsignedShort ):
            width = 2 
            code = 'H'
        else:
            # ... others to come
            raise TypeError("I don't know base type "+str(basetype))

        att_data = att.buffer().data().data()
        if( att_type == Qt3DRender.QAttribute.AttributeType.VertexAttribute ):
            for i in range(att.byteOffset(), att.byteOffset() + (max(width,att.byteStride()))*att.count(), max(att.byteStride(),width)):
                vertex = [struct.unpack(code, bytes(att_data[i+(j*width):i+(j*width)+width])) for j in range(att.vertexSize())]
                dumpf(vertex)
        elif att_type == Qt3DRender.QAttribute.AttributeType.IndexAttribute :
            count = att.count()
            num_tris = int(count / 3)
            dumpf( num_tris, "triangles" )
            for i in range( 0, num_tris*3*width, 3*width ):
                tri = [struct.unpack(code, bytes(att_data[i+(j*width):i+(j*width)+width])) for j in range(3)]
                dumpf(tri)



class AthenaGeomView(Qt3DExtras.Qt3DWindow):
    def __init__(self):
        super(AthenaGeomView, self).__init__()

        self.defaultFrameGraph().setClearColor( QColor(63, 63, 63) )
        self.renderSettings().setRenderPolicy(self.renderSettings().OnDemand)

        self.reset2DCamera()

        self.rootEntity = Qt3DCore.QEntity()

        #self.material = Qt3DExtras.QGoochMaterial(self.rootEntity)
        #self.material.setDiffuse( QColor(200, 200, 200) )

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

        self.meshEntity = Qt3DCore.QEntity(self.rootEntity)
        self.displayMesh = Qt3DRender.QMesh(self.rootEntity)
        self.meshEntity.addComponent( self.displayMesh )
        self.meshEntity.addComponent( self.material )
        self.setRootEntity(self.rootEntity)

        self.lastpos = None

        self.displayMesh.statusChanged.connect(self.meshChange)
        self.displayMesh.geometryChanged.connect(self.meshChange)

    def reloadGeom(self, filepath, mesh_3d, cam_distance = None):
        self.displayMesh.setSource( QUrl.fromLocalFile(str(filepath)) )
        if (mesh_3d):
            self.reset3DCamera(cam_distance)
        else:
            self.reset2DCamera()
        geom = self.displayMesh.geometry()

    def meshChange( self ):
        print(self.displayMesh.source(), self.displayMesh.status())
        if self.displayMesh.status() == Qt3DRender.QMesh.Ready:
            geom = self.displayMesh.geometry()
            dumpGeometry(geom)

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
