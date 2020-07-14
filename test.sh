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

rm $logdir/*

# configuration parts
network=True
comp_set=False
mode=list

#for dom in 5 10 30 30 40 50; do
for dom in 5; do
  for network_protocol in TCP; do
#    for repo in 1 2 3 4 5 6 7 8 9 10; do
    for repo in 1; do
      for net_speed in 10; do
        for comp_speed in 100; do
          for num in 5; do
            name=${network_protocol}_a${num}_d${dom}_r${repo}_p0.5p0.5
            log=$logdir/${name}_${mode}_network${network}${net_speed}_comp${comp_set}${comp_speed}.log
            echo "start running ${name} mode ${mode}_network${network}${net_speed}_comp${comp_set}${comp_speed}" &&
            python3 src/properties.py --mode $mode \
                                      --network_protocol ${network_protocol} \
                                      --network $network \
                                      --computation $comp_set \
                                      --comp_speed ${comp_speed} \
                                      --net_speed ${net_speed} \
                                      --log_file ${log} &&
            python3 $script --input $datadir/random_a${num}_d${dom}_r${repo}_p0.5p0.5.xml
            #                 mode=split
            #                 name=random_a${num}_d${dom}_r${repo}
            #                 log=$logdir/${name}_${mode}_network${net_speed}_comp${comp_speed}.log
            #                 echo "start running ${name} mode ${mode}_network${net_speed}_comp${comp_speed}" &&
            #                 python3 $script --input $datadir/${name}.xml \
            #                                --network $network \
            #                                --mode $mode \
            #                                --computation ${comp_set} \
            #                                --comp_speed ${comp_speed} \
            #                                --net_speed ${net_speed} >> $log &&
            #                 echo "finish running ${name}" &&
            #
            #                 mode=pipeline
            #                 name=random_a${num}_d${dom}_r${repo}
            #                 log=$logdir/${name}_${mode}_network${net_speed}_comp${comp_speed}.log
            #                 echo "start running ${name} mode ${mode}_network${net_speed}_comp${comp_speed}" &&
            #                 python3 $script --input $datadir/${name}.xml \
            #                                --network $network \
            #                                --mode $mode \
            #                                --computation ${comp_set} \
            #                                --comp_speed ${comp_speed} \
            #                                --net_speed ${net_speed} >> $log &&
            #                 echo "finish running ${name}" &&
          done
        done
      done
    done
  done
done