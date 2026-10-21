v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
C {TR-1umLIB/MP.sym} 280 190 0 0 {name=XM1
model=PMOS
w=19u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {TR-1umLIB/MP.sym} 620 190 0 0 {name=XM3
model=PMOS
w=19u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
N 320 110 660 110 {lab=V+}
N 320 110 320 160 {lab=V+}
N 660 110 660 160 {lab=V+}
N 320 190 400 190 {lab=V+}
N 400 110 400 190 {lab=V+}
N 660 190 740 190 {lab=V+}
N 740 110 740 190 {lab=V+}
N 660 110 740 110 {lab=V+}
N 320 220 320 270 {lab=#net1}
N 660 220 660 270 {lab=#net1}
N 320 270 660 270 {lab=#net1}
N 460 270 460 320 {lab=#net1}
N 460 60 460 110 {lab=V+}
C {devices/iopin.sym} 460 60 0 0 {name=label1 lab=V+}
N 200 190 280 190 {lab=a}
C {devices/ipin.sym} 200 190 0 0 {name=label2 lab=a}
N 540 190 620 190 {lab=b}
C {devices/ipin.sym} 540 190 0 0 {name=label3 lab=b}
C {TR-1umLIB/RR.sym} 460 320 0 0 {name=R1
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1}
C {TR-1umLIB/RR.sym} 460 460 0 0 {name=R2
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1}
N 460 380 460 460 {lab=vout}
N 460 420 830 420 {lab=vout}
C {devices/opin.sym} 830 420 0 0 {name=label4 lab=vout}
N 480 350 600 350 {lab=V+}
C {devices/lab_pin.sym} 600 350 0 1 {name=label5 lab=V+}
N 480 490 600 490 {lab=V+}
C {devices/lab_pin.sym} 600 490 0 1 {name=label6 lab=V+}
N 460 520 460 570 {lab=#net3}
C {TR-1umLIB/MN.sym} 420 600 0 0 {name=XM2
model=NMOS
w=13u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {TR-1umLIB/MN.sym} 420 710 0 0 {name=XM4
model=NMOS
w=13u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
N 460 630 460 680 {lab=#net2}
N 460 740 460 830 {lab=V-}
N 460 600 580 600 {lab=V-}
N 580 600 580 790 {lab=V-}
N 460 710 580 710 {lab=V-}
N 460 790 580 790 {lab=V-}
N 220 600 420 600 {lab=a}
C {devices/lab_pin.sym} 220 600 0 0 {name=label7 lab=a}
N 220 710 420 710 {lab=b}
C {devices/lab_pin.sym} 220 710 0 0 {name=label8 lab=b}
C {devices/iopin.sym} 460 830 2 0 {name=label9 lab=V-}
