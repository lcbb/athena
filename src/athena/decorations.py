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
