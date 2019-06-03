#!/bin/bash

for fingers in 1 3 5; do
  for postos in 1 3 5; do
    for pistas in 1 3 5; do
      for espera in 1 2 5 8; do
        #echo $pistas $postos $fingers $espera
        python -O aeroporto.py --pistas $pistas --postos $postos --fingers $fingers --espera $espera >> dados.csv
      done
    done
  done
done
