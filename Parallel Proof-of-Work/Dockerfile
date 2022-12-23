FROM intel/intel-optimized-tensorflow

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

# required for black eztension
ENV JUPYTERHUB_SINGLEUSER_APP jupyter_server.serverapp.ServerApp

# this seems to fix a problem with permissions when we designate a volume on a mounted dir
ENV JUPYTER_ALLOW_INSECURE_WRITES 1

# Run system updates
RUN apt-get update && apt-get install -y --no-install-recommends gcc && apt-get install -y git

# Install application into container
COPY . .

# Install additional deps
RUN pip install -r requirements.txt

# Create and switch to a new user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Open port used by jupyterlab by default
EXPOSE 8888

# Run jupyter lab
CMD ["jupyter-lab", "--ip", "0.0.0.0", "--no-browser"]