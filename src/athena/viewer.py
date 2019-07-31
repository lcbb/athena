from pathlib import Path
import math
import numpy as np

from PySide2.QtGui import QColor, QVector3D as vec3d, QImageWriter, QOffscreenSurface, QSurfaceFormat, QImage, QMatrix4x4
from PySide2.QtCore import QUrl, QByteArray, Qt, Signal, QRectF, QSize

from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DCore import Qt3DCore
from PySide2.QtQml import QQmlEngine, QQmlComponent

from plyfile import PlyData, PlyElement

from athena import ATHENA_SRC_DIR, plymesh, geom, decorations, screenshot

ATHENA_GEOM_UP = geom.ATHENA_GEOM_UP

class CameraController:

    @classmethod
    def createFrom( cls, cc ):
        '''Copy constructor'''
        ret = cls( cc.window, cc.camera, cc.mesh, cc.split )
        if( cc.mesh ):
            ret.camCenter = cc.camCenter
            ret.camLoc = cc.camLoc
            ret.upVector = cc.upVector
            ret.rightVector = cc.rightVector
            ret._apply()
            ret._setProjection()
        return ret

    def __init__(self, window, camera, mesh, split):
        self.window = window
        self.camera = camera
        self.mesh = mesh
        self.split = split
        if( self.mesh ) : 
            self.aabb = geom.AABB(self.mesh.geometry)
            self._setupCamera()

    def newMesh( self, mesh ):
        self.mesh = mesh
        self.aabb = geom.AABB( self.mesh.geometry )
        self._setupCamera()
        self.reset()

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
        if( self.mesh is None ): return 
        self.camCenter = self.aabb.center
        camDistance = 2 * self.bounding_radius
        if( self.mesh.dimensions == 2 ):
            self.rightVector = vec3d(1, 0, 0)
            self.upVector = vec3d(0, 1, 0)
            self.camLoc = self.camCenter + vec3d( 0, 0, camDistance )
        else:
            self.rightVector = vec3d( 0, 1, 0 )
            self.upVector = vec3d( 0, 0, 1 )
            self.camLoc = self.camCenter + vec3d( camDistance, 0, 0 )
        self._apply()
        self._setProjection()

    # Cross of right and forward vector -- the "true up" of the camera.
    # self.upVector is immutable and used as the reference direction for rotations.
    def _currentUp(self):
        return vec3d.crossProduct( self.rightVector, self.camCenter - self.camLoc ).normalized()

    def _apply(self):
        self.camera.setUpVector( self._currentUp() )
        self.camera.setPosition( self.camLoc )
        self.camera.setViewCenter( self.camCenter )

    def _setProjection(self, ratio = None):
        # Defined in concrete subclasses
        pass

    def zoom(self, dx, dy):
        # Defined in concrete subclasses
        pass

    def pan(self, dx, dy):
        delta_x = -dx * self.rightVector
        delta_y = dy * self._currentUp()
        delta = delta_x + delta_y
        delta *= self._panfactor()
        self.camCenter += delta
        self.camLoc += delta
        self._setProjection()
        self._apply()

    def rotate( self, dx, dy ):
        up = self.upVector
        right = self.rightVector
        ctr = self.aabb.center

        v = self.camLoc - ctr
        v = geom.rotateAround( v, right, -dy )
        v = geom.rotateAround( v, up, -dx )
        self.camLoc = ctr + v

        d = self.camCenter - ctr
        d = geom.rotateAround( d, right, -dy )
        d = geom.rotateAround( d, up, -dx )
        self.camCenter = ctr + d

        self.rightVector = geom.rotateAround( right, up, -dx )
        self._apply()

    def resize(self, newsize = None):
        if( self.mesh ):
            if( newsize ):
                ratio = newsize.width() / newsize.height()
                if self.split: ratio /= 2
            else: ratio = None
            self._setProjection( ratio )
            self._apply()

class OrthoCamController(CameraController):

    def __init__(self, window, camera, geometry, split):
        super().__init__(window, camera, geometry, split)
        self.margin = 1.4
        self.reset()

    def _panfactor(self):
        f = self.bounding_radius * self.margin / self.window.width()
        return f

    def _setProjection(self, ratio = None):
        r = self.bounding_radius
        ratio = ratio if ratio else self._windowAspectRatio()
        x = self.aabb.dimensions()[0] / 2 * self.margin
        y = x / ratio
        self.camera.lens().setOrthographicProjection( -x, x, -y, y, r, 3*r )

    def reset ( self ):
        self.margin = 1.4
        super().reset()

    def zoom( self, dx, dy ):
        delta = pow ( 1.1, -dy/100 )
        self.margin *= delta
        self._setProjection()
        self._apply()

class PerspectiveCamController(CameraController):

    def __init__(self, window, camera, geometry, split):
        super().__init__(window, camera, geometry, split)
        self.fov = 50
        self.reset()

    def _panfactor(self):
        f = self.bounding_radius * ( self.fov / 15 ) / self.window.width() 
        return f

    def _setProjection(self, ratio=None):
        frustum_min = self.bounding_radius
        frustum_max = 3 * frustum_min
        ratio = ratio if ratio else self._windowAspectRatio()
        self.camera.lens().setPerspectiveProjection(self.fov, ratio, frustum_min, frustum_max)

    def reset ( self ):
        self.fov = 50
        super().reset()

    def zoom( self, dx, dy ):
        delta = dy / 25
        fov = self.fov
        def clamp(min_, max_, value):
            return min( max( value, min_ ), max_ )
        new_fov = clamp (5, 150, fov - delta)
        self.fov = new_fov
        self._setProjection()
        self._apply()


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

        # Framegraph root #1 -- onscreen rendering
        self.surfaceSelector = Qt3DRender.QRenderSurfaceSelector()
        self.surfaceSelector.setSurface(window)
        self.root = self.surfaceSelector


        # Framgraph root #2 -- Used for offscreen renders, not in the graph by default
        # During screenshots, offscreenSurfaceSelector becomes the root
        # and the branch roots will become a child of renderTargetSelector
        self.offscreenSurfaceSelector = Qt3DRender.QRenderSurfaceSelector()
        self.offscreenSurfaceSelector.setSurface(self.offscreenSurface)
        self.renderTargetSelector = Qt3DRender.QRenderTargetSelector(self.offscreenSurfaceSelector)
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
        for node in self.branchRoots:
            node.setParent( self.renderTargetSelector )
        self.root = self.offscreenSurfaceSelector
        self.offscreenSurfaceSelector.setExternalRenderTargetSize(size)

    def setOnscreenRendering (self):
        for node in self.branchRoots:
            node.setParent( self.surfaceSelector )
        self.root = self.surfaceSelector


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
                     'wire_enable': 1.0,
                     'proj_orthographic': 1.0,
                     'dpi' : 100.0,
                     'flat_color': QColor( 215, 72, 215),
                     'cool_color': QColor( 0, 0, 127 ),
                     'warm_color': QColor( 255, 0, 255),
                     'line.width': 1.0,
                     'line.color': QColor( 55, 110, 255),
                     'light.position': vec3d( 0, 0, 100),
                     'athena_viewport': QMatrix4x4() # see function resizeViewport() for explanation
                    }

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
        material =  self._athenaMaterial( 'meshmaterial.qml', 'wireframe.vert', 
                                                      flavor+'_wireframe.frag',
                                                      'wireframe.geom' )
        material.addParameter( self._alphaParam )
        material.addParameter( self._dpiParam )
        material.addParameter( self._faceEnableParam )
        material.addParameter( self._wireEnableParam )
        material.addParameter( self._lineWidthParam )
        material.addParameter( self._lineColorParam )
        material.addParameter( self._athenaViewportParam )
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

        self.resetBackgroundColor()
        self.lightOrientation = int(0) # Internal integer controlling light.position attribute
        self.renderSettings().setRenderPolicy(self.renderSettings().OnDemand)

        self.rootEntity = Qt3DCore.QEntity()

        self.initParameters() # defined in metaclass
        self.faceEnableChanged.connect( self.handleFaceRenderChange )
        self.lightPositionChanged.connect( self.handleLightPositionChange )
        self.wireEnableChanged.connect( self.handleWireframeRenderChange )

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
        # which keeps Qt3D from deleting them.  I don't know if this is the best approach, but it works.
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
        self.routModelEntities = [ DecorationEntity( self.rootEntity ) for x in range(2) ]
        self.atomModelEntities = [ DecorationEntity( self.rootEntity ) for x in range(2) ]

        self.lastpos = None
        self.mouseTool = 'rotate'

        self.setDpi( self.screen().physicalDotsPerInch() )
        self.camControl = OrthoCamController(self,self.camera(),None,False)

        #import IPython
        #IPython.embed()

    backgroundColorChanged = Signal( QColor )

    def resetBackgroundColor( self ):
        self.setBackgroundColor( QColor(0,0,0) )

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

    wireframeRenderingEnabledChanged = Signal( bool )

    def wireframeRenderingEnabled( self ):
        return self._wireEnableParam.value() > 0.0

    def toggleWireframeRendering( self, boolvalue ):
        self.setWireEnable( 1.0 if boolvalue else 0.0 )

    def handleWireframeRenderChange( self, floatvalue ):
        self.wireframeRenderingEnabledChanged.emit( True if floatvalue > 0.0 else False )

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
        self.resizeViewport()

    def resetCamera(self):
        # FIXME camControl.reset() *should* work here, but something is amiss
        # and this is the more reliable method right now.  Ugh.
        camclass = self.camControl.__class__
        self.camControl = camclass( self, self.camera(), self.meshEntity, self.camControl.split )

    def clearAllGeometry( self ):
        if( self.meshEntity ):
            self.meshEntity.deleteLater()
            self.meshEntity = None
        self.clearDecorations()

    def clearDecorations( self ):
        for ent in [self.cylModelEntity] + self.routModelEntities + self.atomModelEntities:
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
        self.meshEntity = plymesh.PlyMesh2(self.meshEntityParent, self.plydata)
        mesh_3d = self.meshEntity.dimensions == 3
        self.camControl.newMesh(self.meshEntity)
        if( mesh_3d ):
            self.meshEntity.addComponent(self.gooch_material)
        else:
            self.meshEntity.addComponent(self.flat_material)
        self.camControl.reset()
        return mesh_3d

    def setPerspectiveCam(self):
        self.setProjOrthographic(0.0)
        self.camControl = PerspectiveCamController.createFrom( self.camControl)

    def setOrthoCam(self):
        self.setProjOrthographic(1.0)
        self.camControl = OrthoCamController.createFrom( self.camControl)

    def setRotateTool(self):
        self.mouseTool = 'rotate'

    def setPanTool(self):
        self.mouseTool = 'pan'

    def setZoomTool(self):
        self.mouseTool = 'zoom'

    def requestScreenshot(self, size, dpi=None):
        ratio = size.width() / size.height()
        def cleanup():
            self.framegraph.setOnscreenRendering()
            self.setActiveFrameGraph(self.framegraph.root)
            self.setDpi( self.screen().physicalDotsPerInch() )
            self.camControl.resize()
            self.resizeViewport()
            self.requestUpdate()
        if dpi: self.setDpi(dpi)
        self.camControl.resize(size)
        self.resizeViewport( size )
        self.framegraph.setOffscreenRendering(size)
        self.setActiveFrameGraph(self.framegraph.root)
        request = self.framegraph.renderCapture.requestCapture()
        request.completed.connect( cleanup )
        # Now ensure a frame redraw occurs so that the capture can go forward.
        # A nicer way would be to call renderSettings().sendCommand('InvalidateFrame'),
        # but PySide2 does not expose QNode.sendCommand().
        # c.f. the implementation of Qt3DWindow::event()
        self.requestUpdate()
        return request

    def mouseMoveEvent(self, event):
        if( self.meshEntity and self.lastpos ):
            delta = event.pos()-self.lastpos
            if( event.buttons() == Qt.LeftButton ):
                tool = getattr(self.camControl, self.mouseTool)
                tool( delta.x(), delta.y() )
        self.lastpos = event.pos()

    def wheelEvent( self, event ):
        self.camControl.zoom( 0, event.angleDelta().y() )

    def _physicalPixelSize( self, size = None ):
        if size is None: size = self.size()
        factor = self.screen().devicePixelRatio()
        return QSize( size.width() * factor, size.height() * factor )

    def resizeViewport( self, size = None ):
        # the athena_viewport QParameter exists because the Qt3D ViewportMatrix shader
        # uniform is unreliable: it doesn't seem to be consistently updated before a draw
        # operation occurs under a new viewport matrix.  This messes up shader calculations,
        # especially in screenshots (where only a single frame is captured under new
        # rendering dimensions), which in turn wrecks the wireframe renderer.
        #
        # This function manually recreates the viewport matrix that Qt3D uses and keeps
        # it updated in the athena_viewport parameter.
        # Note that it's important to use physical pixel sizes in this calculation, so
        # always multiply on-screen sizes by self.screen().devicePixelRatio()
        viewport_matrix = QMatrix4x4()

        # The only renderer to use the athena_viewport parameter is the wireframe renderer,
        # which is always under framegraph.viewport2
        viewport = self.framegraph.viewport2.normalizedRect()
        if ( size == None ):
            size = self._physicalPixelSize()

        # c.f. Qt3DRender::SubmissionContext::setViewport()
        viewport_matrix.viewport( viewport.x() * size.width(),
                                  (1.0 - viewport.y() - viewport.height()) * size.height(),
                                  viewport.width() * size.width(),
                                  viewport.height() * size.height() );
        self.setAthenaViewport( viewport_matrix )

    def resizeEvent( self, event ):
        size = event.size()
        self.resizeViewport( self._physicalPixelSize(size) )
        self.camControl.resize( size )

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

    def setRoutDisplay(self, bild_results, map_aabb, variant):
        self.newDecoration( self.routModelEntities[variant], bild_results, map_aabb )

    def setAtomDisplay(self, bild_results, map_aabb, variant):
        self.newDecoration( self.atomModelEntities[variant], bild_results, map_aabb )

    def toggleCylDisplay(self, value):
        self.cylModelEntity.setEnabled( value )

    def toggleRoutDisplay(self, value, variant):
        self.routModelEntities[variant].setEnabled( value )

    def toggleAtomDisplay(self, value, variant):
        self.atomModelEntities[variant].setEnabled( value )
