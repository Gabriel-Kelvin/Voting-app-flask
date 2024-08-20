# Flask-Vote-App
A sample web poll application written in Python (Flask).

Users will be prompted with a poll question and related options. They can vote preferred option(s) and see poll results as a chart. Poll results are then loaded into an internal DB based on sqlite. As alternative, the application can store poll results in an external MySQL database.

[![Docker Repository on Quay](https://quay.io/repository/sjbylo/flask-vote-app/status "Docker Repository on Quay")](https://quay.io/repository/sjbylo/flask-vote-app)

## Local deployment

This application can be deployed locally. On linux, install git and clone the repository:

```
sudo yum install -y git
git clone https://github.com/sjbylo/flask-vote-app
cd flask-vote-app
```

Install the dependencies:

```
pip install flask
pip install flask-sqlalchemy
pip install mysqlclient
```

and start the application:

```
python app.py
Check if a poll already exists in the db
...
* Running on http://0.0.0.0:8080/ (Press CTRL+C to quit)
```

View the app in the browser.  The test script can also be used to test the vote app:

```
./test-vote-app http://localhost:8080
```

Poll question and options are loaded from a JSON file called ``seed_data.json`` under the ``./seeds`` directory. 
This file is filled with default values, change it before starting the application.

The DB data file is called ``app.db`` and is located under the ``./data`` directory. 
To use an external MySQL database, set the environment variables by editing the ``flask.rc`` file under the application directory.

```
nano flask.rc
export PS1='[\u(flask)]\> '
export ENDPOINT_ADDRESS=db
export PORT=3306
export DB_NAME=vote
export MASTER_USERNAME=voteuser
export MASTER_PASSWORD=password
export DB_TYPE=mysql
```

Make sure an external MySQL database server is running according to the parameters above.

Source the file and restart the application:

```
source flask.rc
python app.py
```

Cleanup:

```
rm -f data/app.db    # optionally remove the database 
```

## Docker deployment

The app can be run by pulling the image from quay.io and curling localhost:8080

```
docker run -d --rm -p 8080:8080 --name=vote-app quay.io/sjbylo/flask-vote-app
curl http://localhost:8080/
```

Stop the container with Ctrl+C

## Docker build and deployment

A Dockerfile is provided in the repository to build a docker image and run the application as linux container.

On Linux, install and start Docker:

```
sudo yum install -y docker
systemctl start docker
```

Install git and clone the repository:

```
sudo yum install -y git
git clone https://github.com/sjbylo/flask-vote-app
cd flask-vote-app
```

Build a Docker image:

```
docker build -t vote-app:latest .
docker images
REPOSITORY            TAG                 IMAGE ID            CREATED             SIZE
vote-app              latest              e6e0578f5f2d        2 minutes ago       695.4 MB
```

Start the container:

```
docker run -d -p 8080:8080 --name=vote-app vote-app:latest
```

Seed data directory, containing the seed data file ``seed_data.json``, can be mounted as an external volume under the host ``/mnt`` directory:

```
cp flask-vote-app/seeds/seed_data.json /mnt
docker run -d -p 8080:8080 -v /mnt:/app/seeds --name=vote-app vote-app:latest
```

An external MySQL database can be used instead of the internal sqlite by setting the desired env variables:

```
docker run -e ENDPOINT_ADDRESS=db \
           -e PORT=3306 \
           -e DB_NAME=vote \
           -e MASTER_USERNAME=voteuser \
           -e MASTER_PASSWORD=password \
           -e DB_TYPE=mysql \
           -d -p 8080:8080  --name=vote-app vote-app:latest
```

Cleanup:

```
docker stop vote-app && docker rm vote-app
```
