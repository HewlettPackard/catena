#!/bin/sh

IMAGE_NAME=$1

cd $IMAGE_NAME
docker build --build-arg http_proxy=http://16.46.16.11:8080 --build-arg https_proxy=http://16.46.16.11:8080 -t "hpecatena/${IMAGE_NAME}" .
cd ..
docker push "hpecatena/${IMAGE_NAME}"
