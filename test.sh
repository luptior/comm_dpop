#!/bin/bash

# read this script path
pushd $(dirname "${0}") > /dev/null
basedir=$(pwd -L)
popd > /dev/null

#sudo sysctl -w net.inet.udp.maxdgram=65535
script=${basedir}/src/run.py
datadir=${basedir}/../python_generator/data
configure=${basedir}/configure
logdir=${basedir}/log
mkdir -p $logdir



# Define a timestamp function, return seconds.nanoseconds
timestamp() {
  date +%s
}

# configuration parts
network=False
comp_set=False
mode=list

for repo in 1; do
  for net_speed in 1; do
    for comp_speed in 1; do
      for dom in 10; do
        for num in 5; do
          mode=list
          name=random_a${num}_d${dom}_r${repo}
          log=$logdir/${name}_${mode}_network${net_speed}_comp${comp_speed}.log
          timestamp >$log &&
            echo "start running ${name} mode ${mode}_network${net_speed}_comp${comp_speed}" &&
            python3 src/properties.py --mode $mode --network_protocol $network_protocol --network $network --computation $comp_set --comp_speed ${comp_speed} --net_speed ${net_speed}
            python3 $script --input $datadir/${name}.xml >>$log &&
            #             echo "finish running ${name}" &&
            timestamp >>$log &&
            python3 src/read_log.py $log

          #                 mode=split
          #                 name=random_a${num}_d${dom}_r${repo}
          #                 log=$logdir/${name}_${mode}_network${net_speed}_comp${comp_speed}.log
          #                 timestamp > $log &&
          #                 echo "start running ${name} mode ${mode}_network${net_speed}_comp${comp_speed}" &&
          #                 python3 $script --input $datadir/${name}.xml \
          #                                --network $network \
          #                                --mode $mode \
          #                                --computation ${comp_set} \
          #                                --comp_speed ${comp_speed} \
          #                                --net_speed ${net_speed} >> $log &&
          #    #             echo "finish running ${name}" &&
          #                 timestamp >> $log &&
          #                 python3 src/read_log.py $log
          #
          #                 mode=pipeline
          #                 name=random_a${num}_d${dom}_r${repo}
          #                 log=$logdir/${name}_${mode}_network${net_speed}_comp${comp_speed}.log
          #                 timestamp > $log &&
          #                 echo "start running ${name} mode ${mode}_network${net_speed}_comp${comp_speed}" &&
          #                 python3 $script --input $datadir/${name}.xml \
          #                                --network $network \
          #                                --mode $mode \
          #                                --computation ${comp_set} \
          #                                --comp_speed ${comp_speed} \
          #                                --net_speed ${net_speed} >> $log &&
          #                 echo "finish running ${name}" &&
          #                 timestamp >> $log &&
          #                 python3 src/read_log.py $log
        done
      done
    done
  done
done