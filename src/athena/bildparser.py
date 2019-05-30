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
    def __init__(self, scale_factor):
        self.colors = dict() # maps normalized bild strings to QColors
        self.current_color = None
        self.spheres = list()
        self.cylinders = list()
        self.arrows = list()
        self.scale_factor = scale_factor / 3.2

    def addColor( self, tokens ):
        color_key = ' '.join(tokens)
        if color_key not in self.colors:
            if color_key in colorTable.colors:
                self.colors[color_key] = QColor( *colorTable.colors[color_key] )
            else:
                self.colors[color_key] = QColor( *(float(x)*255 for x in tokens) )
        self.current_color = self.colors[color_key]

    def addSphere( self, tokens ):
        self.spheres.append( Sphere( self.current_color, *(float(x)*(self.scale_factor) for x in tokens) ) )

    def addCylinder( self, tokens ):
        self.cylinders.append( Cylinder( self.current_color, *(float(x)*(self.scale_factor) for x in tokens) ) )

    def addArrow( self, tokens ):
        self.arrows.append( Arrow( self.current_color, *(float(x)*(self.scale_factor) for x in tokens) ) )

    def debugSummary( self ):
        pattern =  'parsed BILD: {0} unique colors, {1} spheres, {2} cylinders, {3} arrows' +\
                   '\n           unknown keywords/counts: {4}' +\
                   '\n           comment lines: {5}'
        return pattern.format( len(self.colors), len(self.spheres), len(self.cylinders), len(self.arrows),
                               self.unknown_keyword_map, len(self.other_line_list) )


def parseBildFile( filename, scale_factor ):
    results = OutputDecorations(scale_factor)
    with open(filename,'r') as bild:
        unknown_keyword_map = dict()
        other_line_list = list()
        for line in bild:
            tokens = line.split()
            token0 = tokens[0]
            if( token0 == '.arrow' ):
                results.addArrow( tokens[1:] )
            elif( token0 == '.color' ):
                results.addColor( tokens[1:] )
            elif token0 == '.cylinder':
                results.addCylinder( tokens[1:] )
            elif token0 == '.sphere':
                results.addSphere( tokens[1:] )
            elif( tokens[0].startswith('.')):
                v = unknown_keyword_map.get(tokens[0],0)
                unknown_keyword_map[tokens[0]] = v + 1
            else:
                other_line_list.append(tokens)
        results.unknown_keyword_map = unknown_keyword_map
        results.other_line_list = other_line_list
    return results
