uvicorn InventoryServer:app --host 192.168.1.18 --port 8892 --reload --ssl-keyfile=certs/server_unencrypted.key --ssl-certfile=certs/server.crt
