#!/bin/bash
PATH="/usr/local/bin/gdate:$PATH"

#sudo sysctl -w net.inet.udp.maxdgram=65535
script=/Users/luptior/Desktop/Research_3/dpop/src/run.py
datadir=/Users/luptior/Desktop/Research_3/python_generator/data
logdir=./log
mkdir -p $logdir

# Define a timestamp function, return seconds.nanoseconds
timestamp() {
  date +%s
}

for dom in 10; do
  for repo in 0; do
      for num in 5; do
             name=random_a${num}_d${dom}_r${repo}
             log=$logdir/${name}.log
             timestamp > $log &&
             echo "start running ${name}" &&
             python $script --input $datadir/${name}.xml >> $log &&
             echo "finish running ${name}" &&
             timestamp >> $log
             python src/read_log.py $log
        done
    done
done