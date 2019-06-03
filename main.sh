#!/bin/bash

for espera in 30 60 90 ; do
  echo "tmp_total,pistas,fingers,postos" > "$espera-espera.csv"
  for pistas in 1 3 5; do
    for fingers in 1 3 5; do
      for postos in 1 3 5; do
        python aeroporto.py --pistas $pistas --postos $postos --fingers $fingers --espera $espera >> "$espera-espera.csv"
      done
    done
  done
done
