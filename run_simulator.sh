#!/bin/bash


# Check if all required arguments are provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 <iter> <mali_cell> <seed>"
    exit 1
fi

# Assign command-line arguments to variables
ITER=$1
MALI_CELL=$2
SEED=$3


# run ue flask app
cd writer/src
python3 ue.py &
INSERT_UE_PID=$!
echo "insert.py ue pid: $INSERT_UE_PID"
cd ../../

sleep 3

# run cell flask app
cd writer/src
python3 cell.py &
INSERT_CELL_PID=$!
echo "insert.py cell pid: $INSERT_CELL_PID"
cd ../../

sleep 3


./deploy_xapps.sh
echo "xApps have been deployed."
# run simulator
cd testbed_environment
python3 test.py --iter $ITER --mali_cell $MALI_CELL --seed $SEED
cd ../

echo "simulator pid: $SIMULATOR_PID"

# deploy xAppa

#cd /home/ubuntu
#
#python3 exptocsv.py --msr 'UEReports' --out "auto_data/ue_${MALI_CELL}_${ITER}_seed_${SEED}.csv"
#python3 exptocsv.py --msr 'CellReports' --out "auto_data/cell_${MALI_CELL}_${ITER}_seed_${SEED}.csv"
#
#echo "===== Saved simulation reports ====="
# wait $SIMULATOR_PID

# kill process
cd writer/src
pkill -f "python3 ue.py"
pkill -f "python3 cell.py"
cd ../../

# kill $INSERT_INSERT_CELL_PID
# kill $SIMULATOR_UE_PID

cd ~
./uninstall.sh

echo "Both Flask apps have been terminated."
