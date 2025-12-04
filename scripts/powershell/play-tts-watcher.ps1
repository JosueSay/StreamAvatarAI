$scriptDir = $PSScriptRoot
$projectRoot = Split-Path (Split-Path $scriptDir -Parent) -Parent

# Ruta a data/audio relativa al proyecto
$folder = Join-Path $projectRoot "data\audio"

Write-Host "TTS Watcher iniciado. Monitoreando: $folder"

$fsw = New-Object IO.FileSystemWatcher $folder -Property @{
    NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite'
    Filter = "*.mp3"
    EnableRaisingEvents = $true
}

Register-ObjectEvent $fsw Created -Action {
    $path = $Event.SourceEventArgs.FullPath
    Write-Host "Nuevo audio detectado: $path"
    try {
        # Abre el archivo con el reproductor por defecto de Windows
        Start-Process -FilePath $path
    } catch {
        Write-Host "Error al reproducir audio: $_"
    }
}

while ($true) {
    Start-Sleep -Seconds 1
}
