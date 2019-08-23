#!/bin/bash
PATH="/usr/local/bin/gdate:$PATH"

#sudo sysctl -w net.inet.udp.maxdgram=65535
script=/Users/luptior/Desktop/Research_3/dpop/src/run_w_parser.py
simdir=/Users/luptior/Desktop/Research_3/simulation_data
logdir=$simdir/log
mkdir -p $logdir

# Define a timestamp function, return seconds.nanoseconds
timestamp() {
  date +%s
}

for repo in 0; do
    for num in 5; do
#         for dom in 50; do
          for dom in 50 55 60 65 70 75 80 85 90 95 100; do
             log=$logdir/random_${num}_rep_${repo}_d${dom}.log
             timestamp > $log &&
             echo "start running random_${num}_rep_${repo}_d${dom}" &&
             python $script $simdir/random_${num}_d${dom}/rep_${repo}_random_${num}_d${dom}.xml / >> $log &&
             echo "finish running random_${num}_rep_${repo}_d${dom}" &&
             timestamp >>$log
             python src/read_log.py $log
        done
    done
done

# domance
#for num in 5; do
#    for dom in 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
#        for repo in 0; do
#            log=$logdir/random_${num}_rep_${repo}_d${dom}.log
#            timestamp>$log &&
#            echo "start running random_${num}_rep_${repo}_d${dom}" &&
#            python $script $simdir/random_${num}_d${dom}/rep_${repo}_random_${num}_d${dom}.xml / >>$log &&
#            # echo $simdir/random_${num}/rep_${repo}_random_${num}.xml
#            echo "finish running random_${num}_rep_${repo}_d${dom}" &&
#            timestamp >>$log
#        done
#    done
#done

# f='/Users/luptior/Desktop/Rotation_3/dcop_generator/build/random_p1=0.2_p2=0.0/rep_0_random.xml'
# python simulations/sim_w_parser.py $f