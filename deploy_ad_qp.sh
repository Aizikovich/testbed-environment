#!/bin/bash

echo "========> Clone xapps"
cd ~
git clone https://github.com/Aizikovich/ric-app-ad.git
git clone https://github.com/Aizikovich/ric-app-ad.git



docker run -d -p 5000:5000 --name local-registry registry:2

# Build and push xapp ad
cd ~/ric-app-ad
docker build -t 127.0.0.1:5000/ric-app-ad:1.0 .
docker push 127.0.0.1:5000/ric-app-ad:1.0

# Build and push xapp qp
cd ~/ric-app-qp
docker build -t 127.0.0.1:5000/ric-app-qp:1.0 .
docker push 127.0.0.1:5000/ric-app-qp:1.0

# prepare chartmuseum and dms_cli
cd ~
chmod 777 $(pwd)/charts
docker run --rm -u 0 -it -d -p 8090:8080 -e DEBUG=1 -e STORAGE=local -e STORAGE_LOCAL_ROOTDIR=/charts -v $(pwd)/charts:/charts chartmuseum/chartmuseum:latest
sleep 2
export CHART_REPO_URL=http://127.0.0.1:8090

# install ad
dms_cli onboard --config_file_path=ric-app-ad/xapp-descriptor/config.json --shcema_file_path=appmgr/xapp_orchestrater/dev/docs/xapp_onboarder/guide/embedded-schema.json
dms_cli install --xapp_chart_name=ad --version=1.0.0 --namespace=ricxapp

echo "========> install xapp ad"
sleep 1

# install qp
dms_cli onboard --config_file_path=ric-app-qp/xapp-descriptor/config.json --shcema_file_path=appmgr/xapp_orchestrater/dev/docs/xapp_onboarder/guide/embedded-schema.json
dms_cli install --xapp_chart_name=qp --version=0.0.5 --namespace=ricxapp

echo "========> install xapp qp"
sleep 1

kubectl get pods -n ricxapp