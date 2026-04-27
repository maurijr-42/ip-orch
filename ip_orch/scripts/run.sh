#!/bin/bash
#SBATCH --nodes 1
#SBATCH --cpus-per-task 5
#SBATCH --time 1-00:00:00
#SBATCH --job-name atom-eval
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1

source ~/.bashrc
conda activate benchmark

ip-orch --run isolated_atom_energies.py --parallel 10 --models allegro-mp-l,chgnet,dpa-3.1-3m-ft,dpa-3.1-mptrj,eqnorm-mptrj,grace-1l-oam,grace-2l-mp-r6,grace-2l-oam,hienet,m3gnet,mace-mp,mace-mp-0,mace-mpa-0,matris-10m-mp,matris-10m-oam,mattersim-v1,nequip-mp-l,nequip-oam-l,nequix-mp,nequix-mp-pft,orb-v2,orb-v2-mptrj,orb-v3,pet-oam-xl,sevennet-l3i5,sevennet-omni,tace-v1-oam-m --models-path /home/p.zanineli/pretrained/models
