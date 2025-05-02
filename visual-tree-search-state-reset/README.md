# VisualTreeSearch Website State Reset

This repo contains the FastAPI server for state reset on the backend database of WebArena shopping website.

## usage


### Setup 


[Setup WebArena shopping website on AWS](./Server_Setup.md)



### start FastAPI server

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

### send http requests

- Test

`curl -N http://xwebarena.pathonai.org:8000/api/hello`

- Test DB status

`curl -N http://xwebarena.pathonai.org:8000/api/db/status`

- Reset account information with DB SQL operations

`curl -N http://xwebarena.pathonai.org:8000/api/sql/restore `

- Reset the whole container 

`curl -N http://xwebarena.pathonai.org:8000/api/container/reset/xwebarena.pathonai.org`


