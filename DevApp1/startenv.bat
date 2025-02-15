
cls
cd C:\DevApps\pyProj\LIVE\DevApp0
call C:\DevApps\pyProj\LIVE\envIAM\Scripts\activate.bat


echo uvicorn main:app --host 10.16.67.27 --port 8806 --reload --ssl-keyfile=certs/server_unencrypted.key --ssl-certfile=certs/server.crt