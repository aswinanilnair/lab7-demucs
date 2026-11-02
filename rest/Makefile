VERSION=v1
DOCKERUSER=aswinanilnair

build:
	docker build -f Dockerfile-rest -t $(DOCKERUSER)/demucs-rest:$(VERSION) .

#
# GKE nodes are usually amd64, publishing images for both architectures
#
push:
	docker buildx build --platform linux/amd64,linux/arm64 -f Dockerfile-rest \
		-t $(DOCKERUSER)/demucs-rest:$(VERSION) -t $(DOCKERUSER)/demucs-rest:latest --push .
