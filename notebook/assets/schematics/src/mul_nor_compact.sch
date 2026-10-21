v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
C {TR-1umLIB/MP.sym} 420 190 0 0 {name=XM4
model=PMOS
w=37u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {TR-1umLIB/MP.sym} 420 300 0 0 {name=XM3
model=PMOS
w=37u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
N 460 60 460 160 {lab=V+}
C {devices/iopin.sym} 460 60 0 0 {name=l1 lab=V+}
N 460 220 460 270 {lab=#net3}
N 460 330 460 380 {lab=#net2}
N 460 110 580 110 {lab=V+}
N 580 110 580 300 {lab=V+}
N 460 190 580 190 {lab=V+}
N 460 300 580 300 {lab=V+}
N 220 190 420 190 {lab=a}
C {devices/ipin.sym} 220 190 0 0 {name=lab1 lab=a}
N 220 300 420 300 {lab=b}
C {devices/ipin.sym} 220 300 0 0 {name=lab2 lab=b}
C {TR-1umLIB/RR.sym} 460 380 0 0 {name=R2
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1}
C {TR-1umLIB/RR.sym} 460 530 0 0 {name=R1
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1}
N 460 440 460 530 {lab=vout}
N 460 480 830 480 {lab=vout}
C {devices/opin.sym} 830 480 0 0 {name=lab3 lab=vout}
N 480 410 620 410 {lab=V+}
C {devices/lab_pin.sym} 620 410 0 1 {name=lab4 lab=V+}
N 480 560 620 560 {lab=V+}
C {devices/lab_pin.sym} 620 560 0 1 {name=lab5 lab=V+}
N 460 590 460 640 {lab=#net1}
N 320 640 660 640 {lab=#net1}
N 320 640 320 690 {lab=#net1}
N 660 640 660 690 {lab=#net1}
C {TR-1umLIB/MN.sym} 280 720 0 0 {name=XM2
model=NMOS
w=6.5u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
C {TR-1umLIB/MN.sym} 620 720 0 0 {name=XM1
model=NMOS
w=6.5u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0}
N 200 720 280 720 {lab=a}
C {devices/lab_pin.sym} 200 720 0 0 {name=lab6 lab=a}
N 540 720 620 720 {lab=b}
C {devices/lab_pin.sym} 540 720 0 0 {name=lab7 lab=b}
N 320 750 320 800 {lab=V-}
N 660 750 660 800 {lab=V-}
N 320 800 740 800 {lab=V-}
N 460 800 460 850 {lab=V-}
C {devices/iopin.sym} 460 850 2 0 {name=l4 lab=V-}
N 320 720 400 720 {lab=V-}
N 400 720 400 800 {lab=V-}
N 660 720 740 720 {lab=V-}
N 740 720 740 800 {lab=V-}
