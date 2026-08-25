[CmdletBinding()]
param(
    [string]$VideoPath = "artifacts/demo/closeout-demo.webm",
    [string]$NarrationSource = "docs/demo-narration.ssml",
    [string]$OutputPath = "artifacts/demo/closeout-demo-narrated.webm",
    [ValidateRange(-10, 10)]
    [int]$SpeechRate = 2
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

function Resolve-ProjectPath {
    param([Parameter(Mandatory)][string]$Path)

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $projectRoot $Path))
}

$videoFullPath = Resolve-ProjectPath $VideoPath
$narrationSourceFullPath = Resolve-ProjectPath $NarrationSource
$outputFullPath = Resolve-ProjectPath $OutputPath
$narrationAudioPath = [System.IO.Path]::ChangeExtension(
    $outputFullPath,
    ".narration.wav"
)

foreach ($requiredPath in @($videoFullPath, $narrationSourceFullPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required media source does not exist: $requiredPath"
    }
}

New-Item -ItemType Directory -Force -Path (
    Split-Path -Parent $outputFullPath
) | Out-Null

Add-Type -AssemblyName System.Speech
$synthesizer = [System.Speech.Synthesis.SpeechSynthesizer]::new()

try {
    $englishVoice = $synthesizer.GetInstalledVoices() |
        Where-Object {
            $_.Enabled -and $_.VoiceInfo.Culture.Name -eq "en-US"
        } |
        Select-Object -First 1

    if (-not $englishVoice) {
        throw "An enabled en-US System.Speech voice is required."
    }

    $synthesizer.SelectVoice($englishVoice.VoiceInfo.Name)
    $synthesizer.Rate = $SpeechRate
    $synthesizer.Volume = 100
    $synthesizer.SetOutputToWaveFile($narrationAudioPath)
    $synthesizer.SpeakSsml(
        (Get-Content -LiteralPath $narrationSourceFullPath -Raw)
    )
}
finally {
    $synthesizer.Dispose()
}

$ffmpegResult = & uv run --with imageio-ffmpeg==0.6.0 python -c (
    "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
)
$ffmpegPath = @($ffmpegResult)[-1].Trim()

if (-not (Test-Path -LiteralPath $ffmpegPath -PathType Leaf)) {
    throw "Could not resolve the imageio-ffmpeg executable."
}

& $ffmpegPath `
    -hide_banner `
    -loglevel error `
    -y `
    -i $videoFullPath `
    -i $narrationAudioPath `
    -map "0:v:0" `
    -map "1:a:0" `
    -c:v copy `
    -c:a libopus `
    -b:a 96k `
    -af "apad=pad_dur=5" `
    -shortest `
    $outputFullPath

if ($LASTEXITCODE -ne 0) {
    throw "FFmpeg failed with exit code $LASTEXITCODE."
}

$outputItem = Get-Item -LiteralPath $outputFullPath
$outputHash = Get-FileHash -Algorithm SHA256 -LiteralPath $outputFullPath

[pscustomobject]@{
    Voice = $englishVoice.VoiceInfo.Name
    SpeechRate = $SpeechRate
    Output = $outputItem.FullName
    Bytes = $outputItem.Length
    SHA256 = $outputHash.Hash.ToLowerInvariant()
} | ConvertTo-Json
