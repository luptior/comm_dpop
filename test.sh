#!/bin/bash
PATH="/usr/local/bin/gdate:$PATH"

#sudo sysctl -w net.inet.udp.maxdgram=65535
script=/Users/gx/Documents/Research_3/dpop/src/run.py
datadir=/Users/gx/Documents/Research_3/python_generator/data
logdir=./log
mkdir -p $logdir

network=True
split=True

# Define a timestamp function, return seconds.nanoseconds
timestamp() {
  date +%s
}

for dom in 10; do
  for repo in 6; do
      for num in 5; do
             name=random_a${num}_d${dom}_r${repo}
             log=$logdir/${name}_split${split}_network${network}.log
             timestamp > $log &&
             echo "start running ${name} split ${split} network ${network}" &&
             python $script --input $datadir/${name}.xml --network $network --split $split >> $log &&
             echo "finish running ${name}" &&
             timestamp >> $log &&
             python src/read_log.py $log
        done
    done
done