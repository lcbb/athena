from PySide2.QtGui import QColor, QVector3D as vec3d
from PySide2.QtCore import QUrl, Qt
from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DCore import Qt3DCore

class AthenaGeomView(Qt3DExtras.Qt3DWindow):
    def __init__(self):
        super(AthenaGeomView, self).__init__()

        self.defaultFrameGraph().setClearColor( QColor(63, 63, 63) )
        self.renderSettings().setRenderPolicy(self.renderSettings().OnDemand)

        self.camera().lens().setPerspectiveProjection(45, 16/9, .01, 1000)
        self.camera().setPosition( vec3d( 5, 5, 5 ) )
        self.camera().setUpVector( vec3d( 0, 1, 0 ) )
        self.camera().setViewCenter( vec3d( 0, 0, 0) )

        self.rootEntity = Qt3DCore.QEntity()

        self.material = Qt3DExtras.QGoochMaterial(self.rootEntity)

        self.meshEntity = Qt3DCore.QEntity(self.rootEntity)
        self.displayMesh = Qt3DRender.QMesh(self.rootEntity)
        self.meshEntity.addComponent( self.displayMesh )
        self.meshEntity.addComponent( self.material )
        self.setRootEntity(self.rootEntity)

        self.lastpos = None

    def reloadGeom(self, filepath):
        self.displayMesh.setSource( QUrl.fromLocalFile(str(filepath)) )
        print(self.displayMesh.meshName(), self.displayMesh.status() )
        self.camera().viewAll()

    def mouseMoveEvent(self, event):
        if( self.lastpos ):
            delta = event.pos()-self.lastpos
            if( event.buttons() == Qt.LeftButton ):
                self.camera().panAboutViewCenter( -delta.x() )
                self.camera().tiltAboutViewCenter( delta.y() )
                self.camera().setUpVector( vec3d(0,1,0) )
        self.lastpos = event.pos()

    def wheelEvent( self, event ):
        delta = event.angleDelta() / 25
        fov = self.camera().fieldOfView()
        self.camera().setFieldOfView( fov - delta.y() )
