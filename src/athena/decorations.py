import numpy as np

from PySide2.QtGui import QColor, QVector3D as vec3d
from PySide2.QtCore import QByteArray, Qt
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender

from athena.bildparser import Sphere, Cylinder, Arrow
from athena import geom


class SphereDecorations(Qt3DCore.QEntity):

    def __init__(self, parent, bildfile, transform=None):
        super().__init__(parent)
        spherelist = bildfile.spheres
        num_spheres = len(spherelist)

        if num_spheres == 0: return

        total_vertices = num_spheres
        vertex_basetype = geom.basetypes.Float
        if( total_vertices < 30000 ):
            index_basetype = geom.basetypes.UnsignedShort
        else:
            index_basetype = geom.basetypes.UnsignedInt

        vertex_nparr = np.zeros([total_vertices,7],dtype=geom.basetype_numpy_codes[vertex_basetype])

        for idx, (color, x, y, z, r) in enumerate(spherelist):
            if color is None: color = QColor('white')
            vertex_nparr[idx,:] = x, y, z, r, color.redF(), color.greenF(), color.blueF()

        if( transform ):
            vertex_nparr[:,0:3] = transform(vertex_nparr[:,0:3])
            # Transform radii by the equivalent scaling factor (assume it's equal in all dimensions)
            scale = transform(np.ones((1,3)))[0,0]
            vertex_nparr[:,3] *= scale

        self.geometry = Qt3DRender.QGeometry(self)

        position_attrname = Qt3DRender.QAttribute.defaultPositionAttributeName()
        radius_attrname = 'sphereRadius'
        color_attrname = Qt3DRender.QAttribute.defaultColorAttributeName()

        attrspecs = [geom.AttrSpec(position_attrname, column=0, numcols=3),
                     geom.AttrSpec(radius_attrname, column=3, numcols=1),
                     geom.AttrSpec(color_attrname, column=4, numcols=3)]

        self.vtx_attrs = geom.buildVertexAttrs( self, vertex_nparr, attrspecs )
        for va in self.vtx_attrs:
            self.geometry.addAttribute(va)

        # Create qt3d index buffer
        index_nparr = np.arange(len(vertex_nparr),dtype=geom.basetype_numpy_codes[index_basetype])
        self.indexAttr = geom.buildIndexAttr( self, index_nparr )
        self.geometry.addAttribute(self.indexAttr)

        self.renderer = Qt3DRender.QGeometryRenderer(parent)
        self.renderer.setGeometry(self.geometry)
        self.renderer.setPrimitiveType(Qt3DRender.QGeometryRenderer.Points)

        self.addComponent(self.renderer)

class CylinderDecorations(Qt3DCore.QEntity):

    def __init__(self, parent, bildfile, transform=None):
        super().__init__(parent)
        # Draw the arrow bodies as cylinders too
        cylinderlist = bildfile.cylinders + list( bildfile.cylindersFromArrows() )
        num_cylinders = len(cylinderlist)

        if num_cylinders == 0: return

        total_vertices = 2 * num_cylinders
        vertex_basetype = geom.basetypes.Float
        if( total_vertices < 30000 ):
            index_basetype = geom.basetypes.UnsignedShort
        else:
            index_basetype = geom.basetypes.UnsignedInt

        vertex_nparr = np.zeros([total_vertices,7],dtype=geom.basetype_numpy_codes[vertex_basetype])
        for idx, (color, x1, y1, z1, x2, y2, z2, r) in enumerate(cylinderlist):
            if color is None: color = QColor('white')
            vertex_nparr[2*idx,:] = x1, y1, z1, r, color.redF(), color.greenF(), color.blueF()
            vertex_nparr[2*idx+1,:] = x2, y2, z2, r, color.redF(), color.greenF(), color.blueF()

        if( transform ):
            vertex_nparr[:,0:3] = transform(vertex_nparr[:,0:3])
            # Transform radii by the equivalent scaling factor (assume it's equal in all dimensions)
            scale = transform(np.ones((1,3)))[0,0]
            vertex_nparr[:,3] *= scale

        self.geometry = Qt3DRender.QGeometry(self)

        position_attrname = Qt3DRender.QAttribute.defaultPositionAttributeName()
        radius_attrname = 'radius'
        color_attrname = Qt3DRender.QAttribute.defaultColorAttributeName()

        attrspecs = [geom.AttrSpec(position_attrname, column=0, numcols=3),
                     geom.AttrSpec(radius_attrname, column=3, numcols=1),
                     geom.AttrSpec(color_attrname, column=4, numcols=3)]

        self.vtx_attrs = geom.buildVertexAttrs( self, vertex_nparr, attrspecs )
        for va in self.vtx_attrs:
            self.geometry.addAttribute(va)

        # Create qt3d index buffer
        index_nparr = np.arange(len(vertex_nparr),dtype=geom.basetype_numpy_codes[index_basetype])
        self.indexAttr = geom.buildIndexAttr( self, index_nparr )
        self.geometry.addAttribute(self.indexAttr)

        self.renderer = Qt3DRender.QGeometryRenderer(parent)
        self.renderer.setGeometry(self.geometry)
        self.renderer.setPrimitiveType(Qt3DRender.QGeometryRenderer.Lines)

        self.addComponent(self.renderer)

class ConeDecorations(Qt3DCore.QEntity):

    def __init__(self, parent, bildfile, transform=None):
        super().__init__(parent)
        conelist = list( bildfile.conesFromArrows() )
        num_cones = len(conelist)

        if num_cones == 0: return

        total_vertices = 2 * num_cones
        vertex_basetype = geom.basetypes.Float
        if( total_vertices < 30000 ):
            index_basetype = geom.basetypes.UnsignedShort
        else:
            index_basetype = geom.basetypes.UnsignedInt

        vertex_nparr = np.zeros([total_vertices,7],dtype=geom.basetype_numpy_codes[vertex_basetype])
        for idx, (color, x1, y1, z1, x2, y2, z2, r) in enumerate(conelist):
            if color is None: color = QColor('white')
            vertex_nparr[2*idx,:] = x1, y1, z1, r, color.redF(), color.greenF(), color.blueF()
            vertex_nparr[2*idx+1,:] = x2, y2, z2, 0, color.redF(), color.greenF(), color.blueF()

        if( transform ):
            vertex_nparr[:,0:3] = transform(vertex_nparr[:,0:3])
            scale = transform(np.ones((1,3)))[0,0]
            vertex_nparr[:,3] *= scale

        self.geometry = Qt3DRender.QGeometry(self)

        position_attrname = Qt3DRender.QAttribute.defaultPositionAttributeName()
        radius_attrname = 'radius'
        color_attrname = Qt3DRender.QAttribute.defaultColorAttributeName()

        attrspecs = [geom.AttrSpec(position_attrname, column=0, numcols=3),
                     geom.AttrSpec(radius_attrname, column=3, numcols=1),
                     geom.AttrSpec(color_attrname, column=4, numcols=3)]

        self.vtx_attrs = geom.buildVertexAttrs( self, vertex_nparr, attrspecs )
        for va in self.vtx_attrs:
            self.geometry.addAttribute(va)

        # Create qt3d index buffer
        index_nparr = np.arange(len(vertex_nparr),dtype=geom.basetype_numpy_codes[index_basetype])
        self.indexAttr = geom.buildIndexAttr( self, index_nparr )
        self.geometry.addAttribute(self.indexAttr)

        self.renderer = Qt3DRender.QGeometryRenderer(parent)
        self.renderer.setGeometry(self.geometry)
        self.renderer.setPrimitiveType(Qt3DRender.QGeometryRenderer.Lines)

        self.addComponent(self.renderer)

class LineDecoration(Qt3DCore.QEntity):

    def __init__(self, parent, vtx1, vtx2, color ):
        super().__init__(parent)

        total_vertices = 2
        vertex_basetype = geom.basetypes.Float
        index_basetype = geom.basetypes.UnsignedShort

        vertex_nparr = np.zeros([total_vertices,7],dtype=geom.basetype_numpy_codes[vertex_basetype])
        vertex_nparr[0,:] = *vtx1[:], *color[:]
        vertex_nparr[1,:] = *vtx2[:], *color[:]

        self.geometry = Qt3DRender.QGeometry(self)

        position_attrname = Qt3DRender.QAttribute.defaultPositionAttributeName()
        color_attrname = Qt3DRender.QAttribute.defaultColorAttributeName()

        attrspecs = [geom.AttrSpec(position_attrname, column=0, numcols=3),
                     geom.AttrSpec(color_attrname, column=3, numcols=3)]

        self.vtx_attrs = geom.buildVertexAttrs( self, vertex_nparr, attrspecs )
        for va in self.vtx_attrs:
            self.geometry.addAttribute(va)

        # Create qt3d index buffer
        index_nparr = np.arange(2,dtype=geom.basetype_numpy_codes[index_basetype])
        self.indexAttr = geom.buildIndexAttr( self, index_nparr )
        self.geometry.addAttribute(self.indexAttr)

        self.renderer = Qt3DRender.QGeometryRenderer(parent)
        self.renderer.setGeometry(self.geometry)
        self.renderer.setPrimitiveType(Qt3DRender.QGeometryRenderer.Lines)

        self.addComponent(self.renderer)


