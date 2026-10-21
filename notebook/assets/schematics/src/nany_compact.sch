v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N -110 -490 -110 -390 {lab=VDD}
N -110 -330 -110 -280 {lab=#net1}
N -110 -220 -110 -170 {lab=#net2}
N -110 -440 10 -440 {lab=VDD}
N 10 -440 10 -250 {lab=VDD}
N -110 -360 10 -360 {lab=VDD}
N -110 -250 10 -250 {lab=VDD}
N -240 -360 -150 -360 {lab=a}
N -240 -250 -150 -250 {lab=b}
N -110 -110 -110 -10 {lab=vout}
N -90 -140 50 -140 {lab=VDD}
N -90 20 50 20 {lab=VDD}
N -110 50 -110 100 {lab=#net3}
N -110 160 -110 250 {lab=#net4}
N -110 310 -110 400 {lab=VSS}
N -110 130 10 130 {lab=VSS}
N 10 130 10 360 {lab=VSS}
N -110 280 10 280 {lab=VSS}
N -110 360 10 360 {lab=VSS}
N -240 130 -150 130 {lab=a}
N -240 280 -150 280 {lab=b}
N -110 -70 -30 -70 {lab=vout}
N -30 -70 140 -70 {lab=vout}
N 300 -60 300 -40 {lab=vout}
N 140 -70 300 -70 {lab=vout}
N 300 -70 300 -60 {lab=vout}
N 300 -30 300 -10 {lab=vout}
N 300 -40 300 -30 {lab=vout}
N 300 50 300 140 {lab=#net5}
N 300 200 300 260 {lab=VMID}
N 600 -30 600 -10 {lab=vout}
N 600 50 600 140 {lab=#net6}
N 600 200 600 260 {lab=VMID}
N 300 -70 470 -70 {lab=vout}
N 600 -70 600 -30 {lab=vout}
N 470 -70 690 -70 {lab=vout}
N 170 20 260 20 {lab=a}
N 470 20 560 20 {lab=b}
N 170 170 260 170 {lab=b}
N 470 170 560 170 {lab=a}
N 300 20 380 20 {lab=VDD}
N 600 20 680 20 {lab=VDD}
N 300 170 380 170 {lab=VSS}
N 600 170 680 170 {lab=VSS}
C {TR-1umLIB/MP.sym} -150 -250 0 0 {name=XM3
model=PMOS
w=34u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {devices/iopin.sym} -110 -490 0 0 {name=l1 lab=VDD}
C {devices/ipin.sym} -240 -360 0 0 {name=lab1 lab=a}
C {devices/ipin.sym} -240 -250 0 0 {name=lab2 lab=b}
C {TR-1umLIB/RR.sym} -110 -170 0 0 {name=R2
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1}
C {TR-1umLIB/RR.sym} -110 -10 0 0 {name=R1
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1}
C {devices/opin.sym} 690 -70 0 0 {name=lab3 lab=vout}
C {devices/lab_pin.sym} 50 -140 0 1 {name=lab4 lab=VDD}
C {devices/lab_pin.sym} 50 20 0 1 {name=lab5 lab=VDD}
C {TR-1umLIB/MN.sym} -150 130 0 0 {name=XM2
model=NMOS
w=11u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {TR-1umLIB/MN.sym} -150 280 0 0 {name=XM1
model=NMOS
w=11u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {devices/lab_pin.sym} -240 130 0 0 {name=label7 lab=a}
C {devices/lab_pin.sym} -240 280 0 0 {name=label8 lab=b}
C {devices/iopin.sym} -110 400 2 0 {name=l4 lab=VSS}
C {TR-1umLIB/MP.sym} -150 -360 0 0 {name=XM5
model=PMOS
w=34u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {TR-1umLIB/MP.sym} 260 20 0 0 {name=XM6
model=PMOS
w=14u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {TR-1umLIB/MN.sym} 260 170 0 0 {name=XM7
model=NMOS
w=8u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {devices/iopin.sym} 300 260 0 0 {name=gload lab=VMID}
C {TR-1umLIB/MP.sym} 560 20 0 0 {name=XM8
model=PMOS
w=14u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {TR-1umLIB/MN.sym} 560 170 0 0 {name=XM9
model=NMOS
w=8u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {devices/lab_pin.sym} 600 260 0 0 {name=gload1 lab=VMID}
C {devices/lab_pin.sym} 170 20 0 0 {name=label1 lab=a}
C {devices/lab_pin.sym} 470 20 0 0 {name=label2 lab=b}
C {devices/lab_pin.sym} 170 170 0 0 {name=label3 lab=b}
C {devices/lab_pin.sym} 470 170 0 0 {name=label4 lab=a}
C {devices/lab_pin.sym} 380 20 0 1 {name=lab6 lab=VDD}
C {devices/lab_pin.sym} 680 20 0 1 {name=lab7 lab=VDD}
C {devices/lab_pin.sym} 380 170 0 1 {name=lab8 lab=VSS}
C {devices/lab_pin.sym} 680 170 0 1 {name=lab9 lab=VSS}
