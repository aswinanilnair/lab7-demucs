FROM python:3.10-slim

ENV TORCH_HOME=/data/models
ENV OMP_NUM_THREADS=1

RUN  apt-get update && apt-get install -y --no-install-recommends ffmpeg git \
     && rm -rf /var/lib/apt/lists/*
# The extra index provides CPU-only torch on amd64, leaving out the large GPU libraries
RUN  pip3 install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
     demucs==4.0.1 torch==1.13.1 torchaudio==0.13.1 numpy==1.26.4 \
     redis==8.1.0 boto3==1.43.123 requests==2.34.2

# Include the default model so that it isn't downloaded each time a pod starts
RUN  python3 -c "from demucs.pretrained import get_model; get_model('htdemucs')"

WORKDIR /srv
COPY    worker-server.py /srv
CMD [ "python3", "worker-server.py"]
