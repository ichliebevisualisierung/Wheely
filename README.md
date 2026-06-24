

## Zum Testen einer API auf dem Server:
1. In ...Code/Server:
python robot_api.py

 2. Auf persönlichem Laptop (powershell):
Invoke-RestMethod -Method Post `
  -Uri http://wheely.local:8080/move `
  -ContentType "application/json" `
  -Body '{"direction":"backward","speed":7000,"duration_ms":3000}'

This can also be tested with Postman or another request-App.

direction can be backward, forward, left, right.

Idea:
The Robot recieves API requests with things it should do.
In a next step these requests (forward, backward, usw...) should be executed by a LLM with a prompt. This can then run on the local laptop, instead of on the RaspberryPi.



Dokumentation der Fahrttests (Fahrttests wurden erfolgreich durchgeführt): 

(.venv) (base) PS C:\Users\Asus\Desktop\Wheely> $baseUrl = "http://wheely.local:8080"
>> 
>> function Test-Move {
>>     param (
>>         [string]$direction,
>>         [int]$speed = 1200,
>>         [int]$duration = 1000
>>     )
>> 
>>     Write-Host "Teste: $direction"
>>     Invoke-RestMethod -Method Post `
>>         -Uri "$baseUrl/move" `
>>         -ContentType "application/json" `
>>         -Body "{`"direction`":`"$direction`",`"speed`":$speed,`"duration_ms`":$duration}"
>> 
>>     Start-Sleep -Seconds 2
>> }
>> 
>> Test-Move -direction "forward"
>> Test-Move -direction "backward"
>> Test-Move -direction "left"
>> Test-Move -direction "right"
>> 
>> Write-Host "Alle Fahrtests abgeschlossen."
Teste: forward

Teste: backward
  ok result                                                                                  
  -- ------                                                                                  
True @{direction=forward; speed=1200; duration_ms=1000; left_motor=1200; right_motor=1200}   
True @{direction=backward; speed=1200; duration_ms=1000; left_motor=-1200; right_motor=-1200}
Teste: left
True @{direction=left; speed=1200; duration_ms=1000; left_motor=-1200; right_motor=1200}     
Teste: right
True @{direction=right; speed=1200; duration_ms=1000; left_motor=1200; right_motor=-1200}    
Alle Fahrtests abgeschlossen.
