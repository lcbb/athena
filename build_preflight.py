import setuptools_scm
import platform

# Derive a version string from git
athena_version = setuptools_scm.get_version()

version_hunks = athena_version.split('.')
 
print(version_hunks)

assert( hunk.isdigit() for hunk in version_hunks[0:2] )

def writeAthenaVersionFile():
    template = 'version = "{}"\n'
    content = template.format(athena_version)
    filename = 'athena_version.py'
    open(filename,'w+').write(content)
    print('Wrote',filename)

def writeWindowsVersionFile(version_hunks):
    windows_version_template = '''
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=({0}, {1}, {2}, 0),
    prodvers=({0}, {1}, {2}, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904E4',
        [StringStruct(u'CompanyName', u'MIT LCCB Lab'),
        StringStruct(u'FileDescription', u'Athena - a GUI Toolkit for DNA Design'),
        StringStruct(u'FileVersion', u'0, 0, 5, 0'),
        StringStruct(u'InternalName', u'Athena'),
        StringStruct(u'LegalCopyright', u'Copyright © 2019'),
        StringStruct(u'LegalTrademarks', u''),
        StringStruct(u'OriginalFilename', u'Athena.exe'),
        StringStruct(u'ProductName', u'Athena'),
        StringStruct(u'ProductVersion', u'{0}, {1}, {2}, 0')])
      ]), 
    #VarFileInfo([VarStruct(u'Translation', [1033, 1252])])
  ]
)'''
    content = windows_version_template.format(*version_hunks)
    filename = 'version_info.txt'
    open(filename,'w+').write(content)
    print("Wrote windows exe version info to", filename)


writeAthenaVersionFile()
if platform.system() ==  'Windows':
    writeWindowsVersionFile(version_hunks)
