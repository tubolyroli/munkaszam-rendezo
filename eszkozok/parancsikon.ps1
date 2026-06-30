# Asztali parancsikon (ikon) letrehozasa a Munkaszam-rendezohoz.
# Ezt a parancsikon.bat hivja meg; kozvetlenul nem kell futtatni.
# A fajl UTF-8 BOM-mal mentve, hogy a Windows PowerShell az ekezeteket helyesen olvassa.
$here   = Split-Path -Parent $MyInvocation.MyCommand.Path   # eszkozok\ mappa
$gyoker = Split-Path -Parent $here                          # a repo gyökere
$cel    = Join-Path $gyoker 'indito\inditas.bat'
$ikon   = Join-Path $here 'ikon.ico'

$ws     = New-Object -ComObject WScript.Shell
$asztal = $ws.SpecialFolders('Desktop')
$lnkUt  = Join-Path $asztal 'Munkaszám-rendező.lnk'

$lnk = $ws.CreateShortcut($lnkUt)
$lnk.TargetPath       = $cel
$lnk.WorkingDirectory = $gyoker
$lnk.Description       = 'Munkaszám-rendező indítása'
if (Test-Path $ikon) { $lnk.IconLocation = $ikon }
$lnk.Save()

Write-Host "Kész: a 'Munkaszám-rendező' ikon megjelent az Asztalon."
