#!/bin/bash


# Check if all required arguments are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <iter> <seed>"
    exit 1
fi

# Assign command-line arguments to variables
ITER=$1
SEED=$2
PTH=$(pwd)


# run ue flask app
cd writer/src
python3 ue.py &
INSERT_UE_PID=$!S
echo "insert.py ue pid: $INSERT_UE_PID"
cd $PTH

sleep 3

# run cell flask app
cd writer/src
python3 cell.py &
INSERT_CELL_PID=$!
echo "insert.py cell pid: $INSERT_CELL_PID"
cd $PTH

sleep 3


./deploy_xapps.sh
echo "xApps have been deployed."
# run simulator
cd wireless-network-simulator
python3 test.py --iter $ITER --seed $SEED
cd $PTH

echo "simulator pid: $SIMULATOR_PID"

# deploy xAppa

#cd /home/ubuntu
#
#python3 exptocsv.py --msr 'UEReports' --out "auto_data/ue_${ITER}_seed_${SEED}.csv"
#python3 exptocsv.py --msr 'CellReports' --out "auto_data/cell_${ITER}_seed_${SEED}.csv"
#
#echo "===== Saved simulation reports ====="
# wait $SIMULATOR_PID

# kill process
cd writer/src
pkill -f "python3 ue.py"
pkill -f "python3 cell.py"
cd $PTH

# kill $INSERT_INSERT_CELL_PID
# kill $SIMULATOR_UE_PID

#cd ~
./uninstall.sh

echo "Both Flask apps have been terminated."
