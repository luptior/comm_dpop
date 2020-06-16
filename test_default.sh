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
mode=default

for dom in 3 4 5 6 7 8 9 10 15 20; do
  for network_protocol in TCP; do
    for repo in 1 2 3 4 5 6 7 8 9 10; do
      for net_speed in 100; do
        for comp_speed in 100; do
          for num in 5; do
            name=${network_protocol}_a${num}_d${dom}_r${repo}_p0.5p0.5
            log=$logdir/${name}_${mode}_network${network}${net_speed}_comp${comp_set}${comp_speed}.log
            timestamp >$log &&
              echo "start running ${name} mode ${mode}_network${network}${net_speed}_comp${comp_set}${comp_speed}" &&
              python src/properties.py --mode $mode --network_protocol $network_protocol --network $network --computation $comp_set --comp_speed ${comp_speed} --net_speed ${net_speed}
              python $script --input $datadir/random_a${num}_d${dom}_r${repo}_p0.5p0.5.xml >> $log &&
              timestamp >> $log &&
              python src/read_log.py $log >>$log

            #                 mode=split
            #                 name=random_a${num}_d${dom}_r${repo}
            #                 log=$logdir/${name}_${mode}_network${net_speed}_comp${comp_speed}.log
            #                 timestamp > $log &&
            #                 echo "start running ${name} mode ${mode}_network${net_speed}_comp${comp_speed}" &&
            #                 python $script --input $datadir/${name}.xml \
            #                                --network $network \
            #                                --mode $mode \
            #                                --computation ${comp_set} \
            #                                --comp_speed ${comp_speed} \
            #                                --net_speed ${net_speed} >> $log &&
            #    #             echo "finish running ${name}" &&
            #                 timestamp >> $log &&
            #                 python src/read_log.py $log
            #
            #                 mode=pipeline
            #                 name=random_a${num}_d${dom}_r${repo}
            #                 log=$logdir/${name}_${mode}_network${net_speed}_comp${comp_speed}.log
            #                 timestamp > $log &&
            #                 echo "start running ${name} mode ${mode}_network${net_speed}_comp${comp_speed}" &&
            #                 python $script --input $datadir/${name}.xml \
            #                                --network $network \
            #                                --mode $mode \
            #                                --computation ${comp_set} \
            #                                --comp_speed ${comp_speed} \
            #                                --net_speed ${net_speed} >> $log &&
            #                 echo "finish running ${name}" &&
            #                 timestamp >> $log &&
            #                 python src/read_log.py $log
          done
        done
      done
    done
  done
done