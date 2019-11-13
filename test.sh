#!/bin/bash
PATH="/usr/local/bin/gdate:$PATH"

#sudo sysctl -w net.inet.udp.maxdgram=65535
script=/Users/gx/Documents/Research_3/dpop/src/run.py
datadir=/Users/gx/Documents/Research_3/python_generator/data
logdir=./log
mkdir -p $logdir

network=True
split=False


# Define a timestamp function, return seconds.nanoseconds
timestamp() {
  date +%s
}



comp_speed=0.5
net_speed=1



for dom in 10; do
  for repo in 1; do
      for num in 5; do
             mode=list
             name=random_a${num}_d${dom}_r${repo}
             log=$logdir/${name}_${mode}_network${network}.log
             timestamp > $log &&
             echo "start running ${name} mode ${mode} network ${network}" &&
             python $script --input $datadir/${name}.xml \
                            --network $network \
                            --mode $mode \
                            --computation True \
                            --comp_speed ${comp_speed} \
                            --net_speed ${net_speed} >> $log &&
#             echo "finish running ${name}" &&
             timestamp >> $log &&
             python src/read_log.py $log

             mode=split
             name=random_a${num}_d${dom}_r${repo}
             log=$logdir/${name}_${mode}_network${network}.log
             timestamp > $log &&
             echo "start running ${name} mode ${mode} network ${network}" &&
             python $script --input $datadir/${name}.xml \
                            --network $network \
                            --mode $mode \
                            --computation True \
                            --comp_speed ${comp_speed} \
                            --net_speed ${net_speed} >> $log &&
#             echo "finish running ${name}" &&
             timestamp >> $log &&
             python src/read_log.py $log

             mode=pipeline
             name=random_a${num}_d${dom}_r${repo}
             log=$logdir/${name}_${mode}_network${network}.log
             timestamp > $log &&
             echo "start running ${name} mode ${mode} network ${network}" &&
             python $script --input $datadir/${name}.xml \
                            --network $network \
                            --mode $mode \
                            --computation True \
                            --comp_speed ${comp_speed} \
                            --net_speed ${net_speed} >> $log &&
#             echo "finish running ${name}" &&
             timestamp >> $log &&
             python src/read_log.py $log
        done
    done
done