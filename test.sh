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



comp_speed=10
net_speed=20
comp_set=True

for repo in 7; do
  for net_speed in 1; do
    for comp_speed in 1 0.5 0.1 0.05 0.025 0.01; do
      for dom in 30; do
          for num in 5; do
                 mode=list
                 name=random_a${num}_d${dom}_r${repo}
                 log=$logdir/${name}_${mode}_network${net_speed}_comp${comp_speed}.log
                 timestamp > $log &&
                 echo "start running ${name} mode ${mode}_network${net_speed}_comp${comp_speed}" &&
                 python $script --input $datadir/${name}.xml \
                                --network $network \
                                --mode $mode \
                                --computation ${comp_set} \
                                --comp_speed ${comp_speed} \
                                --net_speed ${net_speed} >> $log &&
    #             echo "finish running ${name}" &&
                 timestamp >> $log &&
                 python src/read_log.py $log

                 mode=split
                 name=random_a${num}_d${dom}_r${repo}
                 log=$logdir/${name}_${mode}_network${net_speed}_comp${comp_speed}.log
                 timestamp > $log &&
                 echo "start running ${name} mode ${mode}_network${net_speed}_comp${comp_speed}" &&
                 python $script --input $datadir/${name}.xml \
                                --network $network \
                                --mode $mode \
                                --computation ${comp_set} \
                                --comp_speed ${comp_speed} \
                                --net_speed ${net_speed} >> $log &&
    #             echo "finish running ${name}" &&
                 timestamp >> $log &&
                 python src/read_log.py $log

                 mode=pipeline
                 name=random_a${num}_d${dom}_r${repo}
                 log=$logdir/${name}_${mode}_network${net_speed}_comp${comp_speed}.log
                 timestamp > $log &&
                 echo "start running ${name} mode ${mode}_network${net_speed}_comp${comp_speed}" &&
                 python $script --input $datadir/${name}.xml \
                                --network $network \
                                --mode $mode \
                                --computation ${comp_set} \
                                --comp_speed ${comp_speed} \
                                --net_speed ${net_speed} >> $log &&
                 echo "finish running ${name}" &&
                 timestamp >> $log &&
                 python src/read_log.py $log
            done
        done
    done
  done
done