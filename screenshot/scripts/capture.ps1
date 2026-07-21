Add-Type -AssemblyName System.Windows.Forms

# 1. Clear existing clipboard image
[System.Windows.Forms.Clipboard]::Clear()

# 2. Launch Snipping Tool
Start-Process "ms-screenclip:"

# 3. Poll clipboard for new image (timeout 30s)
$timeout = 30
$elapsed = 0
$image = $null

while ($elapsed -lt $timeout) {
    Start-Sleep -Seconds 1
    $elapsed++
    if ([System.Windows.Forms.Clipboard]::ContainsImage()) {
        $image = [System.Windows.Forms.Clipboard]::GetImage()
        break
    }
}

if (-not $image) {
    Write-Error "Timeout: no screenshot captured within ${timeout}s"
    exit 1
}

# 4. Save to temp file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$path = [System.IO.Path]::Combine($env:TEMP, "screenshot_${timestamp}.png")
$image.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
$image.Dispose()

Write-Output $path
