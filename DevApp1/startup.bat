cls
uvicorn main:app --host 127.0.0.1 --port 8806 --reload --ssl-keyfile=certs/server_unencrypted.key --ssl-certfile=certs/server.crt