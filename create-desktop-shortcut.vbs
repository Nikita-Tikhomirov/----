Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

rootDir = fso.GetParentFolderName(WScript.ScriptFullName)
desktop = shell.SpecialFolders("Desktop")
shortcutPath = desktop & "\Kwork Lead Funnel.lnk"

Set shortcut = shell.CreateShortcut(shortcutPath)
shortcut.TargetPath = shell.ExpandEnvironmentStrings("%WINDIR%") & "\System32\wscript.exe"
shortcut.Arguments = """" & rootDir & "\lead-funnel-gui.vbs" & """"
shortcut.WorkingDirectory = rootDir
shortcut.Description = "Kwork Lead Funnel"
shortcut.Save

MsgBox "Ярлык создан: " & shortcutPath, 64, "Kwork Lead Funnel"
