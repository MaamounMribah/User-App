# Use an official PyTorch runtime as a parent image
FROM python:3.10   

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install  Flask requests google-cloud-storage gunicorn --progress-bar off

# Make port 5000 available to the world outside this container
EXPOSE 5000



# Run app.py when the container launches
ENTRYPOINT ["python3", "user-app/app.py"]
