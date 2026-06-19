

## Zum Testen einer API auf dem Server:
1. In ...Code/Server:
python robot_api.py

 2. Auf persönlichem Laptop:
Invoke-RestMethod -Method Post `
  -Uri http://wheely.local:8080/move `
  -ContentType "application/json" `
  -Body '{"direction":"backward","speed":700,"duration_ms":300}'

