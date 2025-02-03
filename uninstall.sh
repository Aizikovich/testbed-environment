#!/bin/bash

echo " UNinstalling"

cd ~

dms_cli uninstall --xapp_chart_name=ad --namespace=ricxapp
dms_cli uninstall --xapp_chart_name=trafficxapp --namespace=ricxapp
dms_cli uninstall --xapp_chart_name=qp --namespace=ricxapp

rm -r ric-app-ad
rm -r ric-app-qp

kubectl get pod -n ricxapp
