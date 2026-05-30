Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

rootDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = rootDir

Set env = shell.Environment("PROCESS")
env("PYTHONPATH") = rootDir & "\src"

pythonw = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python310\pythonw.exe"
If Not fso.FileExists(pythonw) Then
    pythonw = "pythonw.exe"
End If

command = """" & pythonw & """ -m app.gui"
shell.Run command, 0, False
