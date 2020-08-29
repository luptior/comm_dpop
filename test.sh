#!/bin/bash

#maximize the size of UDP buffer
#sudo sysctl -w net.inet.udp.maxdgram=65535

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
ber=0.0001
rtt=0.02
drop=0.01

#for mode in pipeline default; do
for mode in pipeline; do
#  for dom in 5 10 20 30 40 50 60 70 80 90 100; do
  for dom in 100; do
#    for network_protocol in TCP UDP RUDP_FEC; do
    for network_protocol in TCP UDP; do
      for repo in 0 1 2 3 4 5 6 7 8 9; do
#      for repo in 0; do
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
                                      --log_file "${log}" \
                                      --ber ${ber} \
                                      --rtt ${rtt} \
                                      --drop ${drop}&&
            python3 $script --input $datadir/random_a${num}_d${dom}_r${repo}_p0.5p0.5.xml
          done
        done
      done
    done
  done
done