## How to run the FastAPI Server

```bash
cd app
```
```bash
docker compose up -d
```

## How to run tests

```bash
cd app
```
```bash
python -m pytest
```
(pytest must be installed on your system first)

## How to use the API

In order to use the API you have to call **POST /login** (a fake login endpoint) to get a JWT, which you can then set as **Authorization Header** to call the protected routes (the required permissions for each route is mentioned in the OpenAPI docs which can be found at http://localhost:8000/docs after running the server)