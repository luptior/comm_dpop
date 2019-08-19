#!/usr/bin/env bash

#domain
#for d in 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
#    python read_log.py "../simulation_data/log/random_5_rep_0_d${d}.log"
#done

#agents

for num in 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
    for d in 2; do
        python read_log.py "../simulation_data/log/random_${num}_rep_0_d${d}.log"
    done
done