v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N 320 60 320 160 {lab=VDD}
N 320 190 430 190 {lab=VDD}
N 430 110 430 190 {lab=VDD}
N 320 110 430 110 {lab=VDD}
N 320 220 320 270 {lab=#net1}
N 190 190 280 190 {lab=vin}
N 190 190 190 550 {lab=vin}
N 100 370 190 370 {lab=vin}
N 190 550 280 550 {lab=vin}
N 320 330 320 410 {lab=vout}
N 320 370 540 370 {lab=vout}
N 340 300 450 300 {lab=VDD}
N 340 440 450 440 {lab=VDD}
N 320 470 320 520 {lab=#net2}
N 320 580 320 670 {lab=VSS}
N 320 550 430 550 {lab=VSS}
N 430 550 430 630 {lab=VSS}
N 320 630 430 630 {lab=VSS}
C {TR-1umLIB/MP.sym} 280 190 0 0 {name=XM1
model=PMOS
w=13.5u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {devices/iopin.sym} 320 60 0 0 {name=label1 lab=VDD}
C {devices/ipin.sym} 100 370 0 0 {name=label2 lab=vin}
C {TR-1umLIB/RR.sym} 320 270 0 0 {name=R1
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1}
C {TR-1umLIB/RR.sym} 320 410 0 0 {name=R2
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1}
C {devices/opin.sym} 540 370 0 0 {name=label3 lab=vout}
C {devices/lab_pin.sym} 450 300 0 1 {name=label4 lab=VDD}
C {devices/lab_pin.sym} 450 440 0 1 {name=label5 lab=VDD}
C {TR-1umLIB/MN.sym} 280 550 0 0 {name=XM2
model=NMOS
w=5u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {devices/iopin.sym} 320 670 0 0 {name=label6 lab=VSS}
