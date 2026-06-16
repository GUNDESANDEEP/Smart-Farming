$adminData = @{
    email = "gundesandeep2005@gmail.com"
    password = "Sandy@7982"
    name = "Sandeep Gunde"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
    "X-Setup-Key" = "initial-setup-key-change-me"
}

$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/bootstrap/create-first-admin" -Method POST -Headers $headers -Body $adminData -UseBasicParsing

Write-Host "Status: $($response.StatusCode)"
Write-Host "Response:"
Write-Host $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
