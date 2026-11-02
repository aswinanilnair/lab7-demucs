VERSION=v1
DOCKERUSER=aswinanilnair

#
# You should probably update the docker.io user if you update this
#

build:
	docker build -f Dockerfile -t $(DOCKERUSER)/demucs-logs:$(VERSION) .

#
# The following make rule builds the current code for both amd64 and arm64,
# labels it with the version number specified above and also the "latest" tag,
# and pushes it to hub.docker.io
#
push:
	docker buildx build --platform linux/amd64,linux/arm64 -f Dockerfile \
		-t $(DOCKERUSER)/demucs-logs:$(VERSION) -t $(DOCKERUSER)/demucs-logs:latest --push .
