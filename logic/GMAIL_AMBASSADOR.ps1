function Send-SolarPunkEmail {
    param([string]$To, [string]$Subject, [string]$Body)
    $Email = "yourname@gmail.com" # Update this
    $AppPass = "xxxx xxxx xxxx xxxx" # Update this
    $SecPassword = ConvertTo-SecureString $AppPass -AsPlainText -Force
    $Creds = New-Object System.Management.Automation.PSCredential($Email, $SecPassword)
    $Params = @{ From=$Email; To=$To; Subject="[SolarPunk] $Subject"; Body=$Body; SmtpServer="smtp.gmail.com"; Port=587; UseSsl=$true; Credential=$Creds }
    Send-MailMessage @Params
    Write-Host "AMBASSADOR: Email sent to $To" -ForegroundColor Green
}
