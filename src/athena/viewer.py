from pathlib import Path

from PySide2.QtGui import QColor, QVector3D as vec3d
from PySide2.QtCore import QUrl, QByteArray, Qt

from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DCore import Qt3DCore
from PySide2.QtQml import QQmlEngine, QQmlComponent

from plyfile import PlyData, PlyElement

from athena import ATHENA_SRC_DIR, plymesh, geom

ATHENA_GEOM_UP = vec3d(0, 0, 1)

class CameraController:
    def __init__(self, window, camera, geometry):
        self.window = window
        self.camera = camera
        self.geometry = geometry

    def _windowAspectRatio(self):
        return self.window.width() / self.window.height()

    def reset(self):
        pass

    def zoom(self, delta):
        pass

    def drag(self, dx, dy):
        pass

    def resize(self, newsize_x, newsize_y):
        pass

class CameraController2D(CameraController):
    def __init__(self, window, camera, geometry):
        super(CameraController2D,self).__init__(window, camera, geometry)
        self.margin = 1.4
        self.aabb = geom.AABB(self.geometry)
        self.zpos = self.aabb.max.z() + 10
        self.reset()

    def reset(self):
        self.camera.setViewCenter( self.aabb.center )
        self.camera.setPosition( vec3d( self.aabb.center.x(), self.aabb.center.y(), self.zpos ) )
        self.camera.setUpVector( ATHENA_GEOM_UP )
        self._orient()

    def _extents(self, ratio=None):
        # Return the visible x,y dimensions
        ratio = ratio if ratio else self._windowAspectRatio()
        mesh_extents = self.aabb.max - self.aabb.min
        view_extents = mesh_extents * self.margin
        view_extents.setX( view_extents.y() * ratio )
        return view_extents.x(), view_extents.y()

    def _orient(self, ratio=None):
        x_view, y_view = self._extents(ratio)

        xmin = self.aabb.center.x() - x_view / 2
        xmax = self.aabb.center.x() + x_view / 2
        ymin = self.aabb.center.y() - y_view / 2
        ymax = self.aabb.center.y() + y_view / 2
        zmin = self.aabb.min.z() - 20
        zmax = self.aabb.max.z() + 20

        self.camera.lens().setOrthographicProjection( xmin, xmax, ymin, ymax, zmin, zmax )

    def drag( self, delta_x, delta_y ):
        xview, yview = self._extents()
        xchange = delta_x / self.window.width()
        ychange = delta_y / self.window.height()
        self.camera.translateWorld( vec3d( -xchange * xview, ychange * yview, 0 ), self.camera.TranslateViewCenter )
        self._orient()

    def zoom( self, delta ):
        delta = pow ( 1.1, -delta/100 )
        self.margin *= delta
        self._orient()

    def resize(self, new_width, new_height):
        new_ratio = new_width / new_height
        self._orient(new_ratio)

class CameraController3D(CameraController):
    def __init__(self, window, camera, geometry):
        super(CameraController3D,self).__init__(window, camera, geometry)
        self.aabb = geom.AABB(self.geometry)
        self.reset()

    def reset(self):
        ratio = self._windowAspectRatio()
        self.camera.lens().setPerspectiveProjection(45, ratio, .01, 1000)

        aabb_size = self.aabb.max - self.aabb.min
        cam_distance = 2 * max(aabb_size.x(), aabb_size.y(), aabb_size.z())
        cam_loc = self.aabb.center + vec3d( cam_distance, 0, 0 )
        self.camera.setPosition( cam_loc )
        self.camera.setViewCenter( self.aabb.center )
        self.rightVector = vec3d( 0, 1, 0 )
        self._orientCamera()

    def _orientCamera( self ):
        # Set the camera up vector based on our tracking of the right vector
        view_vec = self.camera.viewCenter() - self.camera.position()
        up = vec3d.crossProduct( self.rightVector, view_vec )
        self.camera.setUpVector( up.normalized() )

    def drag( self, delta_x, delta_y ):
        # Rotate camera based on mouse-drag inputs
        ctr = self.camera.viewCenter()
        up = ATHENA_GEOM_UP
        v = self.camera.position() - ctr
        right = self.rightVector
        v = geom.rotateAround( v, right, -delta_y )
        v = geom.rotateAround( v, up, -delta_x )
        self.camera.setPosition ( (ctr + v) )
        self.rightVector = geom.rotateAround( right, up, -delta_x )
        self._orientCamera()

    def zoom( self, delta ):
        delta = delta / 25
        fov = self.camera.fieldOfView()
        def clamp(min_, max_, value):
            return min( max( value, min_ ), max_ )
        new_fov = clamp (5, 150, fov - delta)
        self.camera.setFieldOfView( new_fov )

    def resize(self, new_width, new_height):
        new_ratio = new_width / new_height
        self.camera.setAspectRatio(new_ratio)


class AthenaViewer(Qt3DExtras.Qt3DWindow):
    def __init__(self):
        super(AthenaViewer, self).__init__()

        self.defaultFrameGraph().setClearColor( QColor(63, 63, 63) )
        self.renderSettings().setRenderPolicy(self.renderSettings().OnDemand)

        self.rootEntity = Qt3DCore.QEntity()
        self.camControl = CameraController(None, None, None)


        # Create the mesh shading material, stored as self.material
        self.eee = QQmlEngine()
        main_qml = Path(ATHENA_SRC_DIR) / 'qml' / 'main.qml'
        self.ccc = QQmlComponent(self.eee, main_qml.as_uri() )
        if( self.ccc.status() != QQmlComponent.Ready ):
            print("Error loading QML:")
            print(self.ccc.errorString())
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
        pass1 = self.material.effect().techniques()[0].renderPasses()[1]
        pass1.setShaderProgram(self.shader)

        self.alpha_param = Qt3DRender.QParameter( self.material )
        self.alpha_param.setName('alpha')
        self.alpha_param.setValue(1.0)
        self.material.addParameter( self.alpha_param )

        self.setRootEntity(self.rootEntity)

        # Each time a mesh is loaded, we create a new Plymesh and add self.material as a component.
        # Old meshes are deleteLater()-ed.  A problem with this approach is that the deleted QEntities
        # also delete their components (and this seems true even if we try to remove the component first).
        # The workaround we use here is to also add self.material as a component of the root entity,
        # which keeps Qt3D from deleting it.  I don't know if this is the best approach, but it works.
        self.rootEntity.addComponent(self.material)
        self.meshEntity = None
        self.lastpos = None

    def getMaterialParam(self, name):
        for param in self.material.parameters():
            if param.name() == name:
                return param
        return None

    def setAlpha(self, value):
        self.alpha_param.setValue( float(value) / 255.0 )

    def reloadGeom(self, filepath, mesh_3d):
        self.meshFilepath = filepath
        self.plydata = PlyData.read(filepath)
        if( self.meshEntity ):
            self.meshEntity.deleteLater()
        self.meshEntity = plymesh.PlyMesh(self.rootEntity, self.plydata)
        self.meshEntity.addComponent(self.material)
    
        if (mesh_3d):
            self.camControl = CameraController3D(self, self.camera(), self.meshEntity.geometry)
        else:
            self.camControl = CameraController2D(self, self.camera(), self.meshEntity.geometry)
        self.camControl.reset()

    def mouseMoveEvent(self, event):
        if( self.lastpos ):
            delta = event.pos()-self.lastpos
            if( event.buttons() == Qt.LeftButton ):
                self.camControl.drag( delta.x(), delta.y() )
        self.lastpos = event.pos()

    def wheelEvent( self, event ):
        self.camControl.zoom( event.angleDelta().y() )

    def resizeEvent( self, event ):
        newsize = event.size()
        self.camControl.resize(newsize.width(), newsize.height())
