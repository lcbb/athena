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


    def _athenaMaterial( self, flavor ):
        engine = QQmlEngine()
        main_qml = Path(ATHENA_SRC_DIR) / 'qml' / 'main.qml'
        component = QQmlComponent(engine, main_qml.as_uri() )
        if ( component.status() != QQmlComponent.Ready ):
            print ("Error loading QML:")
            print(component.errorString())
        material = component.create()

        # Need to hold a reference in python to the QQmlComponent, or else
        # PySide2 will helpfully delete the material object along with it
        # after this function ends.
        self._qtrefs.append(component)

        shader_path = Path(ATHENA_SRC_DIR) / 'shaders'
        vert_shader = shader_path / 'wireframe.vert'
        geom_shader = shader_path / 'wireframe.geom'
        frag_shader = shader_path / (flavor+'_wireframe.frag')
        def loadShader( s ):
            return Qt3DRender.QShaderProgram.loadSource( s.as_uri() )
        shader = Qt3DRender.QShaderProgram(material)
        shader.setVertexShaderCode( loadShader( vert_shader ) )
        shader.setGeometryShaderCode( loadShader( geom_shader ) )
        shader.setFragmentShaderCode( loadShader( frag_shader ) )
        for rpass in material.effect().techniques()[0].renderPasses():
            rpass.setShaderProgram( shader )

        return material



    def __init__(self):
        super(AthenaViewer, self).__init__()
        self._qtrefs = []

        self.defaultFrameGraph().setClearColor( QColor(63, 63, 63) )
        self.renderSettings().setRenderPolicy(self.renderSettings().OnDemand)

        self.rootEntity = Qt3DCore.QEntity()
        self.camControl = CameraController(None, None, None)

        self.alpha_param = Qt3DRender.QParameter( self.rootEntity )
        self.alpha_param.setName('alpha')
        self.alpha_param.setValue(1.0)

        self.color_param = Qt3DRender.QParameter( self.rootEntity )
        self.color_param.setName('flat_color')
        self.color_param.setValue( QColor( 97, 188, 188 ) )

        self.flat_material = self._athenaMaterial( 'flat' )
        self.flat_material.addParameter( self.alpha_param )
        self.flat_material.addParameter( self.color_param )

        self.gooch_material = self._athenaMaterial( 'gooch' )
        self.gooch_material.addParameter( self.alpha_param )

        self.setRootEntity(self.rootEntity)

        # Each time a mesh is loaded, we create a new Plymesh and add a material as a component.
        # Old meshes are deleteLater()-ed.  A problem with this approach is that the deleted QEntities
        # also delete their components (and this seems true even if we try to remove the component first).
        # The workaround we use here is to also add the materials as components of the root entity,
        # which keeps Qt3D from deleting it.  I don't know if this is the best approach, but it works.
        self.rootEntity.addComponent(self.flat_material)
        self.rootEntity.addComponent(self.gooch_material)
        self.meshEntity = None
        self.lastpos = None

    def setAlpha(self, value):
        self.alpha_param.setValue( float(value) / 255.0 )

    def reloadGeom(self, filepath, mesh_3d):
        self.meshFilepath = filepath
        self.plydata = PlyData.read(filepath)
        if( self.meshEntity ):
            self.meshEntity.deleteLater()
        self.meshEntity = plymesh.PlyMesh(self.rootEntity, self.plydata)
        if( mesh_3d ):
            self.meshEntity.addComponent(self.gooch_material)
            self.camControl = CameraController3D(self, self.camera(), self.meshEntity.geometry)
        else:
            self.meshEntity.addComponent(self.flat_material)
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
