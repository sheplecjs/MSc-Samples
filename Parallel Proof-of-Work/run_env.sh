# Build and run the container
docker run -it -p 8888:8888 -v ${PWD}:/home/appuser $(docker build -q .)

# Run an existing container
# docker run -it -p 8888:8888 -v ${PWD}/coursework:/home/appuser a8e808ba05c2
