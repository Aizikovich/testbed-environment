#!/bin/bash

echo "========> Clone xapps"
cd ~
git clone https://github.com/Aizikovich/ric-app-ad.git
git clone https://github.com/Aizikovich/ric-app-qp.git


echo "========> Deploy xapps"

cd ~
cd ric-app-ad
docker build -t nexus3.o-ran-sc.org:10002/o-ran-sc/ric-app-ad:1.0.0 .
cd ~

cd ric-app-qp
docker build -t nexus3.o-ran-sc.org:10002/o-ran-sc/ric-app-qp:0.0.5 .
cd ~

cd ts
docker build -t nexus3.o-ran-sc.org:10002/o-ran-sc/ric-app-ts:1.2.5 .
cd ~

echo "========> finish build xappps"

echo "========> onboarding xapps"

docker run --rm -u 0 -it -d -p 8090:8080 -e DEBUG=1 -e STORAGE=local -e STORAGE_LOCAL_ROOTDIR=/charts -v $(pwd)/charts:/charts chartmuseum/chartmuseum:latest
sleep 2
export CHART_REPO_URL=http://0.0.0.0:8090

dms_cli onboard --config_file_path=ric-app-ad/xapp-descriptor/config.json --shcema_file_path=appmgr/xapp_orchestrater/dev/docs/xapp_onboarder/guide/embedded-schema.json
dms_cli onboard --config_file_path=ric-app-qp/xapp-descriptor/config.json --shcema_file_path=appmgr/xapp_orchestrater/dev/docs/xapp_onboarder/guide/embedded-schema.json
dms_cli onboard --config_file_path=ric-app-ts/xapp-descriptor/config-file.json --shcema_file_path=ric-app-ts/xapp-descriptor/schema.json

dms_cli get_charts_list



dms_cli install --xapp_chart_name=ad --version=1.0.1 --namespace=ricxapp
dms_cli install --xapp_chart_name=trafficxapp --version=1.2.5 --namespace=ricxapp
dms_cli install --xapp_chart_name=qp --version=0.0.5 --namespace=ricxapp

echo "========> install xapps"
sleep 2
