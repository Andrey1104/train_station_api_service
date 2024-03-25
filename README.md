# train_station_api_service

  API service for train station management written on DRF

## Installing using Github

PostgreSQL must be already installed and database must be created

```shell
git clone https://github.com/Andrey1104/train_station_api_service
cd train_station_API
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
create .env file
set POSTGRES_DB=YOUR_POSTGRES_DB
set POSTGRES_USER=YOUR_POSTGRES_USER
set POSTGRES_PASSWORD=YOUR_POSTGRES_PASSWORD
set POSTGRES_HOST=YOUR_POSTGRES_HOST
set POSTGRES_PORT=YOUR_POSTGRES_PORT
python manage.py migrate
python manage.py runserver
```

## Run with Docker

Docker must be already installed

```shell
docker-compose build
docker-compose up
```

## Getting access

- create user via /api/user/register
- get access token via /api/user/token
