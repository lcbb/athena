import numpy as np

from PySide2.QtGui import QColor, QVector3D as vec3d
from PySide2.QtCore import QByteArray, Qt
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender

from athena.bildparser import Sphere, Cylinder, Arrow
from athena import geom


class SphereDecorations(Qt3DCore.QEntity):

    def __init__(self, parent, spherelist):
        super().__init__(parent)
        num_spheres = len(spherelist)

        total_vertices = num_spheres
        vertex_basetype = geom.basetypes.Float
        if( total_vertices < 30000 ):
            index_basetype = geom.basetypes.UnsignedShort
        else:
            index_basetype = geom.basetypes.UnsignedInt

        vertex_nparr = np.zeros([total_vertices,7],dtype=geom.basetype_numpy_codes[vertex_basetype])

        for idx, (color, x, y, z, r) in enumerate(spherelist):
            vertex_nparr[idx,:] = x, y, z, r, color.redF(), color.greenF(), color.blueF()

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

    def __init__(self, parent, cylinderlist):
        super().__init__(parent)
        num_cylinders = len(cylinderlist)

        total_vertices = 2 * num_cylinders
        vertex_basetype = geom.basetypes.Float
        if( total_vertices < 30000 ):
            index_basetype = geom.basetypes.UnsignedShort
        else:
            index_basetype = geom.basetypes.UnsignedInt

        vertex_nparr = np.zeros([total_vertices,7],dtype=geom.basetype_numpy_codes[vertex_basetype])
        for idx, (color, x1, y1, z1, x2, y2, z2, r) in enumerate(cylinderlist):
            vertex_nparr[2*idx,:] = x1, y1, z1, r, color.redF(), color.greenF(), color.blueF()
            vertex_nparr[2*idx+1,:] = x2, y2, z2, r, color.redF(), color.greenF(), color.blueF()
        
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

