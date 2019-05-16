from pathlib import Path

from athena import colorTable

from PySide2.QtGui import QColor

def parseBildFile( filename ):
    with open(filename,'r') as bild:
        unknown_keyword_map = dict()
        other_line_list = list()
        current_color = QColor
        colors = set()
        for line in bild:
            tokens = line.split()
            token0 = tokens[0]
            if( token0 == '.color' ):
                table_key = ' '.join(tokens[1:])
                if table_key in colorTable.colors:
                    current_color = QColor( *colorTable.colors[table_key] )
                else:
                    current_color = QColor( *(float(x)*255 for x in tokens[1:]) )
                colors.add( tuple(tokens[1:]) )
            elif( tokens[0].startswith('.')):
                v = unknown_keyword_map.get(tokens[0],0)
                unknown_keyword_map[tokens[0]] = v + 1
            else:
                other_line_list.append(tokens)
        print(colors)
        print(unknown_keyword_map)
        print(other_line_list)
