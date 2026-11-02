VERSION=v1
DOCKERUSER=aswinanilnair

build:
	docker build -f Dockerfile -t $(DOCKERUSER)/demucs-worker:$(VERSION) .

#
# GKE nodes are usually amd64, so publish images for both architectures
#
push:
	docker buildx build --platform linux/amd64,linux/arm64 -f Dockerfile \
		-t $(DOCKERUSER)/demucs-worker:$(VERSION) -t $(DOCKERUSER)/demucs-worker:latest --push .
