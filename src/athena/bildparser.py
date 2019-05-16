from pathlib import Path
from collections import namedtuple

from athena import colorTable

from PySide2.QtGui import QColor, QVector3D as vec3d
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DExtras import Qt3DExtras

Sphere = namedtuple( 'Sphere', 'color, x, y, z, r' )
Cylinder = namedtuple ( 'Cylinder', 'color, x1, y1, z1, x2, y2, z2, r' )
# We'll give defaults for r1, r2, and rho, which are optional in a file.
# This isn't perfect because the default for r2 should be r1*4.  Parser
# code should watch for the case where r1 is given and r2 is not, and update
# the r2 value appropriately.
Arrow = namedtuple ( 'Arrow', 'color, x1, y1, z1, x2, y2, z2, r1, r2, rho', defaults=[0.1,0.4,0.75] )

class OutputDecorations:
    def __init__(self):
        self.colors = dict() # maps normalized bild strings to QColors
        self.current_color = None
        self.spheres = list()
        self.cylinders = list()
        self.arrows = list()

    def addColor( self, tokens ):
        color_key = ' '.join(tokens)
        if color_key not in self.colors:
            if color_key in colorTable.colors:
                self.colors[color_key] = QColor( *colodTable.colors[color_key] )
            else:
                self.colors[color_key] = QColor( *(float(x)*255 for x in tokens) )
        self.current_color = self.colors[color_key]

    def addSphere( self, tokens ):
        self.spheres.append( Sphere( self.current_color, *tokens ) )

    def addCylinder( self, tokens ):
        self.cylinders.append( Cylinder( self.current_color, *tokens ) )

    def addArrow( self, tokens ):
        self.arrows.append( Arrow( self.current_color, *tokens ) )


def parseBildFile( filename, viewer ):
    with open(filename,'r') as bild:
        unknown_keyword_map = dict()
        other_line_list = list()
        current_color = QColor
        current_material = None
        colors = set()
        sphere = Qt3DExtras.QSphereMesh( viewer.rootEntity)
        sphere.setRadius(.04)
        sphere.setSlices(15)
        for line in bild:
            tokens = line.split()
            token0 = tokens[0]
            if( token0 == '.color' ):
                table_key = ' '.join(tokens[1:])
                if table_key in colorTable.colors:
                    current_color = QColor( *colorTable.colors[table_key] )
                else:
                    current_color = QColor( *(float(x)*255 for x in tokens[1:]) )
                current_material = Qt3DExtras.QPhongMaterial(viewer.rootEntity)
                current_material.setDiffuse(current_color)
                colors.add( tuple(tokens[1:]) )
            elif token0 == '.cylinder':
                x1, y1, z1, x2, y2, z2, r = tokens[1:8]
            elif token0 == '.sphere':
                x, y, z, r = (float(x)/(42/3.2) for x in tokens[1:5])
                #m_sphere = Qt3DExtras.QSphereMesh(viewer.rootEntity)
                #m_sphere.setRadius(r)
                #m_sphere.setSlices(15)
                t_sphere = Qt3DCore.QTransform(viewer.rootEntity)
                t_sphere.setTranslation( vec3d( x, y, z ) )
                viewer.addDecoration( [sphere, t_sphere, current_material] )
                
            elif( tokens[0].startswith('.')):
                v = unknown_keyword_map.get(tokens[0],0)
                unknown_keyword_map[tokens[0]] = v + 1
            else:
                other_line_list.append(tokens)
        print(colors)
        print(unknown_keyword_map)
        print(other_line_list)
