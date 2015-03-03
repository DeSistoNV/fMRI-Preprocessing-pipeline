#!/bin/bash

autogrive() {
while true
do
grive /home/nick/Desktop/grive
sleep 250
done



## arg1 is dir of maps args 2 is dir of data arg 3 is name to name
function run {
echo fugueing $2 $3
cd /media/nick/10259e32-b12f-4a45-a7aa-c73d797b1566/Fugue/$1
fugue -i /media/nick/10259e32-b12f-4a45-a7aa-c73d797b1566/July.2014.Imagery.RF/Naselaris_$2/$3*/*nii --loadfmap=phRadPerMs.nii --dwell=.00032 --unwarpdir=z -u $3
echo 'done fugueing' $2 $3 
date

}


function all {
run tn_fugue/tn1 TN 1_008
run tn_fugue/tn1 TN 1_010
run tn_fugue/tn1 TN 1_012

run tn_fugue/tn1 TN 1_014
run tn_fugue/tn1 TN 1_016
run tn_fugue/tn1 TN 1_018

run tn_fugue/tn1 TN 1_020
run tn_fugue/tn1 TN 1_022

run tn_fugue/tn2 TN2 1_008
run tn_fugue/tn2 TN2 1_010
run tn_fugue/tn2 TN2 1_012
run tn_fugue/tn2 TN2 1_014
run tn_fugue/tn2 TN2 1_020
run tn_fugue/tn2 TN2 1_022
run tn_fugue/tn2 TN2 1_024
run tn_fugue/tn2 TN2 1_026
run tn_fugue/tn2 TN2 1_028
run tn_fugue/tn2 TN2 1_030
run tn_fugue/tn3 TN3 1_006
run tn_fugue/tn3 TN3 1_008
run tn_fugue/tn3 TN3 1_010
run tn_fugue/tn3 TN3 1_020

run tn_fugue/tn4 TN4 1_008
run tn_fugue/tn4 TN4 1_010
run tn_fugue/tn4 TN4 1_012

run co_fugue/m1 CO 1_008
run co_fugue/m1 CO 1_010
run co_fugue/m1 CO 1_012
run co_fugue/m1 CO 1_014
run co_fugue/m1 CO 1_020
run co_fugue/m1 CO 1_022
run co_fugue/m1 CO 1_024
run co_fugue/m1 CO 1_026


run co_fugue/m2 CO2 1_006
run co_fugue/m2 CO2 1_008
run co_fugue/m2 CO2 1_010
run co_fugue/m2 CO2 1_012
run co_fugue/m2 CO2 1_023
run co_fugue/m2 CO2 1_028
run co_fugue/m2 CO2 1_030
run co_fugue/m2 CO2 1_032
run co_fugue/m2 CO2 1_034


run tj_fugue/m1 TJ 1_006
run tj_fugue/m1 TJ 1_008
run tj_fugue/m1 TJ 1_010
run tj_fugue/m1 TJ 1_012
run tj_fugue/m1 TJ 1_014
run tj_fugue/m1 TJ 1_016
run tj_fugue/m1 TJ 1_022
run tj_fugue/m1 TJ 1_024


run tj_fugue/m2 TJ2 1_006
run tj_fugue/m2 TJ2 1_008
run tj_fugue/m2 TJ2 1_010
run tj_fugue/m2 TJ2 1_012
run tj_fugue/m2 TJ2 1_014
run tj_fugue/m2 TJ2 1_016
run tj_fugue/m2 TJ2 1_024
run tj_fugue/m2 TJ2 1_026
}




function get_maps { 
cd /media/nick/10259e32-b12f-4a45-a7aa-c73d797b1566/Fugue/$2*/$1

bet mag.nii magStrip.nii -m
echo $2 $1 max
fslstats phase.nii -R
fslmaths phase.nii -sub 4092 -mul 3.14159 -div 4092 phRad -odt float
prelude -p phRad.nii -a magStrip.nii -m magStrip_mask.nii -o phRadUnwrap
fslmaths phRadUnwrap.nii -div 1.02 phRadPerMs



}
get_maps m1 co
get_maps m1 tj
get_maps m2 co
get_maps m2 tj
get_maps tn1 tn
get_maps tn2 tn
get_maps tn3 tn
get_maps tn4 tn
