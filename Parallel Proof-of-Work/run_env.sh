# Run the container
docker run -it -p 8888:8888 -v ${PWD}:/home/appuser parallel-proof

# build and run the container
# docker run -it -p 8888:8888 -v ${PWD}:/home/appuser parallel-proof $(docker build . -t parallel-proof)
