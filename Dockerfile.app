
# Using plain centos base image, add pip to it
#FROM centos:7
FROM centos-7-python:2.7.15 

LABEL Version 1.0

MAINTAINER Stephen Bylo <StephenBylo@gmail.com>

# Set the application directory
WORKDIR /app

# Update
#RUN yum -y update 

# Install python and pip
RUN yum -y install epel-release && yum -y install python-pip && yum -y clean all

# Install requirements.txt
ADD requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy code from the current folder to /app inside the container
ADD . /app

# Remove any existing db data
RUN rm -f /app/data/app.db

# Expose the port server listen to
EXPOSE 8080

# Ensure this runs as any non-root user (for OpenShift) 
RUN chmod -R 777 /app
USER 1001

# Define command to be run when launching the container
CMD ["python", "app.py"]

