Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

rootDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = rootDir

Set env = shell.Environment("PROCESS")
env("PYTHONPATH") = rootDir & "\src"

Set processes = GetObject("winmgmts:\\.\root\cimv2").ExecQuery("SELECT ProcessId, CommandLine FROM Win32_Process WHERE Name = 'pythonw.exe'")
For Each process In processes
    If Not IsNull(process.CommandLine) Then
        processCommand = LCase(CStr(process.CommandLine))
        If InStr(processCommand, "-m app.gui") > 0 Then
            shell.AppActivate process.ProcessId
            shell.Popup "Kwork Lead Funnel is already open. Close it first, then run the shortcut again to load an update.", 4, "Kwork Lead Funnel", 64
            WScript.Quit 0
        End If
    End If
Next

pythonw = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python310\pythonw.exe"
If Not fso.FileExists(pythonw) Then
    pythonw = "pythonw.exe"
End If

command = """" & pythonw & """ -m app.gui"
shell.Run command, 0, False
