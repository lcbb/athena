from pathlib import Path
import math
import numpy as np

from PySide2.QtGui import QColor, QVector3D as vec3d, QImageWriter, QOffscreenSurface, QSurfaceFormat, QImage
from PySide2.QtCore import QUrl, QByteArray, Qt, Signal, QRectF, QSize

from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DCore import Qt3DCore
from PySide2.QtQml import QQmlEngine, QQmlComponent

from plyfile import PlyData, PlyElement

from athena import ATHENA_SRC_DIR, plymesh, geom, decorations, screenshot

ATHENA_GEOM_UP = geom.ATHENA_GEOM_UP

class CameraController:
    def __init__(self, window, camera, geometry, split):
        self.window = window
        self.camera = camera
        self.geometry = geometry
        self.split = split
        if( geometry ) : 
            self.aabb = geom.AABB(self.geometry)
            self._setupCamera()

    def _windowAspectRatio(self):
        w = self.window.width()
        h = self.window.height()
        if self.split: h = 2 * h
        return w / h

    def _setupCamera(self):
        aabb_dims = self.aabb.dimensions()
        # Diameter of a bounding sphere over the input geometry
        bounding_sphere_diam = max( aabb_dims ) * math.sqrt(3)

        # Add a slight offset to ensure the boundary will cover
        # output decorations (cylinders etc) that are outside the original
        # geometry boundary.  This was determined experimentally
        # by running TALOS with mitered edges on the cube geometry.
        bounding_sphere_diam *= 1.4

        # Save the bounding sphere radius
        self.bounding_radius = bounding_sphere_diam / 2

    def reset(self):
        self.camLoc = vec3d( 0, 0, 2 * self.bounding_radius )
        self.rightVector = vec3d(1, 0, 0)
        self.upVector = vec3d(0, 1, 0)
        self._apply()
        self._setProjection()

    def _apply(self):
        self.camera.setViewCenter( self.aabb.center )
        self.camera.setPosition( self.camLoc )
        self.camera.setUpVector( self.upVector )

    def _setProjection(self):
        pass

    def zoom(self, delta):
        pass

    def pan(self, dx, dy):
        pass

    def rotate( self, dx, dy ):
        ctr = self.aabb.center
        up = self.upVector
        v = self.camLoc - ctr
        right = self.rightVector
        v = geom.rotateAround( v, right, -dy )
        v = geom.rotateAround( v, up, -dx )
        self.camLoc = ctr + v
        self.rightVector = geom.rotateAround( right, up, -dx )
        self._apply()

    def resize(self, ratio=None):
        self._setProjection()

class OrthoCamController(CameraController):
    def __init__(self, window, camera, geometry, split):
        super().__init__(window, camera, geometry, split)
        self.margin = 1.4
        self.reset()

    def _setProjection(self):
        r = self.bounding_radius
        x = self.aabb.dimensions()[0] / 2 * self.margin
        y = x / self._windowAspectRatio()
        self.camera.lens().setOrthographicProjection( -x, x, -y, y, r, 3*r )

    def zoom( self, delta ):
        delta = pow ( 1.1, -delta/100 )
        self.margin *= delta
        self._setProjection()

class PerspectiveCamController(CameraController):
    def __init__(self, window, camera, geometry, split):
        super().__init__(window, camera, geometry, split)
        self.reset()

    def _setProjection(self):
        frustum_min = self.bounding_radius
        frustum_max = 3 * frustum_min
        ratio = self._windowAspectRatio()
        self.camera.lens().setPerspectiveProjection(50, ratio, frustum_min, frustum_max)

    def zoom( self, delta ):
        delta = delta / 25
        fov = self.camera.fieldOfView()
        def clamp(min_, max_, value):
            return min( max( value, min_ ), max_ )
        new_fov = clamp (5, 150, fov - delta)
        self.camera.setFieldOfView( new_fov )


class OffscreenRenderTarget( Qt3DRender.QRenderTarget ):
    def __init__(self, parent, size = QSize(500,500) ):
        super().__init__(parent)
        self.size = size

        self.output = Qt3DRender.QRenderTargetOutput( self )
        self.output.setAttachmentPoint( Qt3DRender.QRenderTargetOutput.Color0 )

        self.texture = Qt3DRender.QTexture2D(self.output)
        self.texture.setSize(size.width(), size.height())
        self.texture.setFormat(Qt3DRender.QAbstractTexture.RGB8_UNorm)
        self.texture.setMinificationFilter(Qt3DRender.QAbstractTexture.Linear)
        self.texture.setMagnificationFilter(Qt3DRender.QAbstractTexture.Linear)

        self.output.setTexture(self.texture)
        self.addOutput(self.output)

        self.depthTexOutput = Qt3DRender.QRenderTargetOutput( self )
        self.depthTexOutput.setAttachmentPoint( Qt3DRender.QRenderTargetOutput.Depth )
        self.depthTex = Qt3DRender.QTexture2D(self.depthTexOutput )
        self.depthTex.setSize( size.width(), size.height() )
        self.depthTex.setFormat( Qt3DRender.QAbstractTexture.D32F )
        self.depthTex.setMinificationFilter(Qt3DRender.QAbstractTexture.Linear)
        self.depthTex.setMagnificationFilter(Qt3DRender.QAbstractTexture.Linear)
        self.depthTex.setComparisonFunction(Qt3DRender.QAbstractTexture.CompareLessEqual)
        self.depthTex.setComparisonMode(Qt3DRender.QAbstractTexture.CompareRefToTexture)

        self.depthTexOutput.setTexture( self.depthTex)
        self.addOutput( self.depthTexOutput )

    def setSize( self, size ):
        self.texture.setSize( size.width(), size.height() )
        self.depthTex.setSize( size.width(), size.height() )



class AthenaFrameGraph:
    '''
    Class to manage the Qt3D framegraph on behalf of the Athena viewer
    '''

    def __init__(self, window):

        self.window = window

        self.offscreenSurface = QOffscreenSurface()
        sformat = QSurfaceFormat.defaultFormat()
        sformat.setDepthBufferSize(32)
        self.offscreenSurface.setFormat( sformat )
        self.offscreenSurface.create()

        self.overlayCamera = Qt3DRender.QCamera()
        self.overlayCamera.setViewCenter( vec3d() )
        self.overlayCamera.setPosition( vec3d( 0, 0, -1 ) )
        self.overlayCamera.setUpVector( vec3d( 0, 1, 0 ) )
        self.overlayCamera.lens().setOrthographicProjection( -1, 1, -1, 1, -1, 1 )

        # Framegraph root
        self.surfaceSelector = Qt3DRender.QRenderSurfaceSelector()
        self.surfaceSelector.setSurface(window)
        self.root = self.surfaceSelector

        # Used for offscreen renders, not in the graph by default
        # During screenshots, this will become a child of surfaceSelector
        # and the branch roots will become a child of renderTargetSelector
        self.renderTargetSelector = Qt3DRender.QRenderTargetSelector()
        self.targetTexture = OffscreenRenderTarget(self.renderTargetSelector)
        self.renderTargetSelector.setTarget(self.targetTexture)
        self.noDraw2 = Qt3DRender.QNoDraw(self.renderTargetSelector)

        # Branch 1: clear buffers
        self.clearBuffers = Qt3DRender.QClearBuffers(self.surfaceSelector)
        self.clearBuffers.setBuffers(Qt3DRender.QClearBuffers.ColorDepthBuffer)
        self.clearBuffers.setClearColor(Qt.white)
        self.noDraw = Qt3DRender.QNoDraw(self.clearBuffers)

        # Branch 2: main drawing branches using the Athena camera
        self.cameraSelector = Qt3DRender.QCameraSelector(self.surfaceSelector)
        self.cameraSelector.setCamera(window.camera())

        # Branch 2A: solid objects
        self.viewport = Qt3DRender.QViewport(self.cameraSelector)
        self.viewport.setNormalizedRect(QRectF(0, 0, 1.0, 1.0))
        self.qfilt = Qt3DRender.QTechniqueFilter(self.viewport)
        self.solidPassFilter = Qt3DRender.QFilterKey(self.qfilt)
        self.solidPassFilter.setName('pass')
        self.solidPassFilter.setValue('solid')
        self.qfilt.addMatch(self.solidPassFilter)

        # Branch 2B: transparent objects
        self.viewport2 = Qt3DRender.QViewport(self.cameraSelector)
        self.viewport2.setNormalizedRect(QRectF(0, 0, 1.0, 1.0))
        self.qfilt2 = Qt3DRender.QTechniqueFilter(self.viewport2)
        self.transPassFilter = Qt3DRender.QFilterKey(self.qfilt2)
        self.transPassFilter.setName('pass')
        self.transPassFilter.setValue('transp')
        self.qfilt2.addMatch(self.transPassFilter)

        # Branch 3: 2D screen overlays
        self.cameraSelector2 = Qt3DRender.QCameraSelector(self.surfaceSelector)
        self.cameraSelector2.setCamera(self.overlayCamera)
        self.viewport3 = Qt3DRender.QViewport(self.cameraSelector2)
        self.viewport3.setNormalizedRect(QRectF(0, 0, 1.0, 1.0))
        self.qfilt3 = Qt3DRender.QTechniqueFilter(self.viewport3)
        self.overlayPassFilter = Qt3DRender.QFilterKey(self.viewport3)
        self.overlayPassFilter.setName('pass')
        self.overlayPassFilter.setValue('overlay')
        self.qfilt3.addMatch(self.overlayPassFilter)

        # Branch 4: render capture branch for taking screenshots
        self.renderCapture = Qt3DRender.QRenderCapture(self.surfaceSelector)
        self.noDraw3 = Qt3DRender.QNoDraw(self.renderCapture)

        # Branch roots are the bits that need reparenting when switching between
        # offscreen and onscreen rendering
        self.branchRoots = [ self.clearBuffers, self.cameraSelector, self.cameraSelector2, self.renderCapture ]

        #self.dump()

    def setOffscreenRendering ( self, size = QSize(1200,1200) ):
        self.targetTexture.setSize(size)
        self.surfaceSelector.setSurface(self.offscreenSurface)
        self.surfaceSelector.setExternalRenderTargetSize(size)
        self.renderTargetSelector.setParent(self.surfaceSelector)
        for node in self.branchRoots:
            node.setParent( self.renderTargetSelector )

    def setOnscreenRendering (self):
        self.surfaceSelector.setSurface(self.window)
        # Turns out you want to call this even for non-external rendering targets
        self.surfaceSelector.setExternalRenderTargetSize(self.window.size())
        for node in self.branchRoots:
            node.setParent( self.surfaceSelector )
        self.renderTargetSelector.setParent( None )


    def dump(self):
        # Framegraph display and testing code
        def frameGraphLeaf(node, prefix=' '):
            print(prefix, node, node.objectName())
            children = node.children()
            for c in children:
                frameGraphLeaf(c, prefix+'-')

        frameGraphLeaf(self.root)



class _metaParameters(type(Qt3DExtras.Qt3DWindow)):
    '''
    Metaclass magic to simplify attaching QParameters to a QObject

    This metaclass adds methods to a class that invokes it.  QParameter
    names and default values should be specified in the invoking class's
    _qparameters dict (which needs to be a class member, not an instance
    member). Then, for each parameter foo, this metaclass defines:

        * foo(), the getter method
        * setFoo(), the setter method
        * fooChanged(), a qt signal
        * initFoo(), an initializer for self._fooParam
        * resetFoo(), a method to reset the param to initial value

    It also defines initParameters(), which calls all the initFoos.  These
    initializer methods assume that the object will have already defined
    a self.rootEntity to parent the newly-created QParameters onto.

    It also defines resetParameters() which calls all the resetFoos.

    These automatic method definitions do not override custom definitions given
    in the class, so it's possible to customize any of these methods as necessary.
    '''

    @staticmethod
    def _mkGetter(attr_name):
        def getter(self):
            return getattr( self, attr_name ).value()
        return getter

    @staticmethod
    def _mkSetter(attr_name, getter_name, signal_name):
        def setter( self, param ):
            oldvalue = getattr( self, getter_name )()
            if( oldvalue != param ):
                getattr( self, attr_name ).setValue( param )
                getattr( self, signal_name ).emit(param)
        return setter

    @staticmethod
    def _mkInit(attr_name, key, value):
        def init( self ):
            param = Qt3DRender.QParameter( self.rootEntity )
            param.setName( key )
            param.setValue( value )
            setattr( self, attr_name, param )
        return init

    @staticmethod
    def _mkReset( setter_name, value ):
        def reset( self ):
            setter = getattr( self, setter_name )
            setter( value )
        return reset

    @staticmethod
    def _mkInitAll(initializers):
        def initAll(self):
            for x in initializers:
                getattr(self, x)()
        return initAll

    @staticmethod
    def _mkResetAll(resetters):
        def resetAll(self):
            for x in resetters:
                getattr(self,x)()
        return resetAll


    def __new__(cls, name, parents, dct):
        params =dct['_qparameters']
        api_translation = str.maketrans( {'.':None, '_':None} )

        def addMethod(name, value):
            if name in dct:
                return
            dct[name] = value

        initList = list()
        resetList = list()
        for key, value in params.items():
            # Create API names for each parameter:
            # with a running example for a key named flat_color
            camel_key = key[0] + key.title()[1:]
            api_name = camel_key.translate( api_translation )
            studly_name = api_name[0].upper() + api_name[1:]
            getter_name = api_name           # flatColor
            setter_name = 'set'+studly_name  # setFlatColor
            signal_name = api_name+'Changed' # flatColorChanged
            init_name = 'init'+studly_name   # initFlatColor
            reset_name = 'reset'+studly_name # resetFlatColor
            attr_name = '_'+api_name+'Param' # _flatColorParam 

            addMethod( getter_name, _metaParameters._mkGetter(attr_name) )
            addMethod( setter_name, _metaParameters._mkSetter(attr_name, getter_name, signal_name) )
            addMethod( signal_name, Signal( type ( value ) ) )
            addMethod( init_name, _metaParameters._mkInit( attr_name, key, value ) )
            addMethod( reset_name, _metaParameters._mkReset( setter_name, value ) )
            initList.append(init_name)
            resetList.append(reset_name)

        addMethod('initParameters', _metaParameters._mkInitAll( initList ) )
        addMethod('resetParameters', _metaParameters._mkResetAll( resetList ) )

        return super(_metaParameters,cls).__new__(cls,name,parents,dct)

class AthenaViewer(Qt3DExtras.Qt3DWindow, metaclass=_metaParameters):

    _qparameters = { 'alpha': 1.0,
                     'face_enable': 1.0,
                     'proj_orthographic': 1.0,
                     'flat_color': QColor( 97, 188, 188),
                     'cool_color': QColor( 0, 25, 170 ),
                     'warm_color': QColor( 210, 190, 0),
                     'line.width': 1.0,
                     'line.color': QColor( 200, 10, 10),
                     'light.position': vec3d( 0, 0, 100) }

    def _qmlLoad( self, qmlfile ):
        engine = QQmlEngine()
        main_qml = Path(ATHENA_SRC_DIR) / 'qml' / qmlfile
        component = QQmlComponent(engine, main_qml.as_uri() )
        if ( component.status() != QQmlComponent.Ready ):
            print ("Error loading QML:")
            print(component.errorString())
        result = component.create()
        # Need to hold a reference in python to the QQmlComponent, or else
        # PySide2 will helpfully delete the material object along with it
        # after this function ends.
        self._qtrefs.append(component)
        return result


    def _athenaMaterial( self, qmlfile, vert_shader, frag_shader, geom_shader=None ):
        material = self._qmlLoad( qmlfile )
        shader_path = Path(ATHENA_SRC_DIR) / 'shaders'
        vert_shader = shader_path / vert_shader
        frag_shader = shader_path / frag_shader
        if( geom_shader ): geom_shader = shader_path / geom_shader
        def loadShader( s ):
            return Qt3DRender.QShaderProgram.loadSource( s.as_uri() )
        shader = Qt3DRender.QShaderProgram(material)
        shader.setVertexShaderCode( loadShader( vert_shader ) )
        if( geom_shader): shader.setGeometryShaderCode( loadShader( geom_shader ) )
        shader.setFragmentShaderCode( loadShader( frag_shader ) )
        for rpass in material.effect().techniques()[0].renderPasses():
            rpass.setShaderProgram( shader )
        return material



    def _plyMeshMaterial( self, flavor ):
        material =  self._athenaMaterial( 'main.qml', 'wireframe.vert', 
                                                      flavor+'_wireframe.frag',
                                                      'wireframe.geom' )
        material.addParameter( self._alphaParam )
        material.addParameter( self._faceEnableParam )
        material.addParameter( self._lineWidthParam )
        material.addParameter( self._lineColorParam )
        return material

    def _imposterMaterial(self, flavor):
        flavor_str = flavor + '_imposter'
        material =  self._athenaMaterial( 'imposter.qml', flavor_str + '.vert', 
                                                          flavor_str + '.frag',
                                                          flavor_str + '.geom' )

        material.addParameter( self._projOrthographicParam )
        return material

    def _overlayMaterial( self ):
        material = self._athenaMaterial( 'overlay.qml', 'overlay.vert', 'overlay.frag' )
        return material


    def __init__(self):
        super(AthenaViewer, self).__init__()
        self._qtrefs = []

        self.framegraph = AthenaFrameGraph(self)
        self.setActiveFrameGraph(self.framegraph.root)

        self.setBackgroundColor( QColor(63,63,63) )
        self.lightOrientation = int(0) # Internal integer controlling light.position attribute
        self.renderSettings().setRenderPolicy(self.renderSettings().OnDemand)

        self.rootEntity = Qt3DCore.QEntity()
        self.camControl = CameraController(None, None, None, False)

        self.initParameters() # defined in metaclass
        self.faceEnableChanged.connect( self.handleFaceRenderChange )
        self.lightPositionChanged.connect( self.handleLightPositionChange )

        self.sphere_material = self._imposterMaterial('sphere')
        #self.cylinder_material = Qt3DExtras.QPerVertexColorMaterial(self.rootEntity)
        self.cylinder_material = self._imposterMaterial('cylinder')
        self.cone_material = self._imposterMaterial('cone')

        self.flat_material = self._plyMeshMaterial( 'flat' )
        self.flat_material.addParameter( self._flatColorParam )

        self.gooch_material = self._plyMeshMaterial( 'gooch' )
        self.gooch_material.addParameter( self._coolColorParam )
        self.gooch_material.addParameter( self._warmColorParam )
        self.gooch_material.addParameter( self._lightPositionParam )

        # The vertical split line enabled for split-screen view
        self.overlay_material = self._overlayMaterial()

        self.splitLineEntity = decorations.LineDecoration( self.rootEntity, [0,-1,0], [0,1,0], [1,1,1,1] )
        self.splitLineEntity.addComponent( self.overlay_material )
        self.splitLineEntity.setEnabled(False)


        # Each time a mesh is loaded, we create a new Plymesh and add a material as a component.
        # Old meshes are deleteLater()-ed.  A problem with this approach is that the deleted QEntities
        # also delete their components (and this seems true even if we try to remove the component first).
        # The workaround we use here is to also add the materials as components of the root entity,
        # which keeps Qt3D from deleting it.  I don't know if this is the best approach, but it works.
        self.rootEntity.addComponent(self.flat_material)
        self.rootEntity.addComponent(self.gooch_material)
        self.rootEntity.addComponent(self.sphere_material)
        self.rootEntity.addComponent(self.cylinder_material)
        self.rootEntity.addComponent(self.cone_material)

        self.setRootEntity(self.rootEntity)

        self.meshEntityParent = Qt3DCore.QEntity( self.rootEntity )

        self.meshEntity = None

        class DecorationEntity(Qt3DCore.QEntity):
            def __init__(self, parent):
                super().__init__(parent)
                self.spheres = None
                self.cylinders = None
                self.cones = None

        self.cylModelEntity = DecorationEntity( self.rootEntity )
        self.routModelEntity = DecorationEntity( self.rootEntity )
        self.atomModelEntity = DecorationEntity( self.rootEntity )

        self.lastpos = None

        #import IPython
        #IPython.embed()

    backgroundColorChanged = Signal( QColor )

    def backgroundColor( self ):
        return self.framegraph.clearBuffers.clearColor()

    def setBackgroundColor( self, color ):
        self.framegraph.clearBuffers.setClearColor( color )
        self.backgroundColorChanged.emit(color)

    faceRenderingEnabledChanged = Signal( bool )

    def faceRenderingEnabled( self ):
        return self._faceEnableParam.value() > 0.0

    def toggleFaceRendering( self, boolvalue ):
        self.setFaceEnable( 1.0 if boolvalue else 0.0 )

    def handleFaceRenderChange( self, floatvalue ):
        self.faceRenderingEnabledChanged.emit( True if floatvalue > 0.0 else False )

    lightOrientationChanged = Signal( int )

    def setLightOrientation( self, value ):
        if( value != self.lightOrientation ):
            scaled_value = float(value)
            new_value = geom.rotateAround( vec3d(0,0,100), vec3d(0,1,0), scaled_value )
            self.setLightPosition( new_value ) 

    def handleLightPositionChange( self, new_posn ):
        new_orientation = math.degrees( math.atan2( new_posn.x(), new_posn.z() ))
        self.lightOrientationChanged.emit( int(new_orientation) )

    def setSplitViewEnabled( self, enabled ):

        if( enabled ):
            self.framegraph.viewport.setNormalizedRect( QRectF( 0.5, 0, 0.5, 1.0) )
            self.framegraph.viewport2.setNormalizedRect( QRectF( 0, 0, 0.5, 1.0 ) )
            self.splitLineEntity.setEnabled( True )
        else:
            whole_screen = QRectF( 0, 0, 1, 1 )
            self.framegraph.viewport.setNormalizedRect( whole_screen )
            self.framegraph.viewport2.setNormalizedRect( whole_screen )
            self.splitLineEntity.setEnabled( False )
        self.camControl.split = enabled
        self.camControl.resize()

    def resetCamera(self):
        self.camControl.reset()

    def clearAllGeometry( self ):
        if( self.meshEntity ):
            self.meshEntity.deleteLater()
            self.meshEntity = None
        self.clearDecorations()

    def clearDecorations( self ):
        for ent in [self.cylModelEntity, self.routModelEntity, self.atomModelEntity]:
            if( ent.spheres ):
                ent.spheres.deleteLater()
                ent.spheres = None
            if (ent.cylinders ):
                ent.cylinders.deleteLater()
                ent.cylinders = None
            if (ent.cones ):
                ent.cones.deleteLater()
                ent.cones = None

    def reloadGeom(self, filepath):

        self.meshFilepath = filepath
        self.plydata = PlyData.read(filepath)
        self.clearAllGeometry()
        self.meshEntity = plymesh.PlyMesh(self.meshEntityParent, self.plydata)
        mesh_3d = self.meshEntity.dimensions == 3
        split = self.camControl.split
        if( mesh_3d ):
            self.meshEntity.addComponent(self.gooch_material)
            self.camControl = PerspectiveCamController(self, self.camera(), self.meshEntity.geometry, split)
            self.setProjOrthographic(0.0)
        else:
            self.meshEntity.addComponent(self.flat_material)
            self.camControl = PerspectiveCamController(self, self.camera(), self.meshEntity.geometry, split)
            self.setProjOrthographic(0.0)
        self.camControl.reset()
        return mesh_3d

    def requestScreenshot(self, size):
        ratio = size.width() / size.height()
        def cleanup():
            self.framegraph.setOnscreenRendering()
            self.camControl.resize()
        self.framegraph.setOffscreenRendering(size)
        self.camControl.resize(ratio)
        request = self.framegraph.renderCapture.requestCapture()
        request.completed.connect( cleanup )
        # Now ensure a frame redraw occurs so that the capture can go forward.
        # A nicer way would be to call renderSettings().sendCommand('InvalidateFrame'),
        # but PySide2 does not expose QNode.sendCommand().
        # c.f. the implementation of Qt3DWindow::event()
        self.requestUpdate()
        return request

    def mouseMoveEvent(self, event):
        if( self.lastpos ):
            delta = event.pos()-self.lastpos
            if( event.buttons() == Qt.LeftButton ):
                self.camControl.rotate( delta.x(), delta.y() )
        self.lastpos = event.pos()

    def wheelEvent( self, event ):
        self.camControl.zoom( event.angleDelta().y() )

    def resizeEvent( self, event ):
        self.camControl.resize()

    def newDecoration(self, parent, bild_results, decoration_aabb = None):

        if decoration_aabb is None:
            decoration_aabb = geom.AABB( bild_results )
        geom_aabb = self.camControl.aabb

        T = geom.transformBetween( decoration_aabb, geom_aabb )

        if( bild_results.spheres ):
            parent.spheres = decorations.SphereDecorations(parent, bild_results, T)
            parent.spheres.addComponent( self.sphere_material )

        if( bild_results.cylinders ):
            parent.cylinders = decorations.CylinderDecorations(parent, bild_results, T)
            parent.cylinders.addComponent( self.cylinder_material )
            
        if( bild_results.arrows ):
            parent.cones = decorations.ConeDecorations(parent, bild_results, T)
            parent.cones.addComponent( self.cone_material )

    def setCylDisplay(self, bild_results, map_aabb):
        self.newDecoration( self.cylModelEntity, bild_results, map_aabb )

    def setRoutDisplay(self, bild_results, map_aabb):
        self.newDecoration( self.routModelEntity, bild_results, map_aabb )

    def setAtomDisplay(self, bild_results, map_aabb):
        self.newDecoration( self.atomModelEntity, bild_results, map_aabb )

    def toggleCylDisplay(self, value):
        self.cylModelEntity.setEnabled( value )

    def toggleRoutDisplay(self, value):
        self.routModelEntity.setEnabled( value )

    def toggleAtomDisplay(self, value):
        self.atomModelEntity.setEnabled( value )
