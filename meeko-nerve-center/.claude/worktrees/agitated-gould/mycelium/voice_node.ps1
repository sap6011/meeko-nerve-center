Add-Type -AssemblyName System.speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$intel = Get-Content "C:\Solarpunk-Prime\data\harvested_knowledge\latest_intel.json" | ConvertFrom-Json

foreach ($node in $intel) {
    if ($node.category -match "GRANT|LEGAL") {
        $message = "High priority Solarpunk node detected: $($node.title)"
        $speak.Speak($message)
    }
}
