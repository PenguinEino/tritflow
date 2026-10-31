v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N 220 -100 220 -70 {lab=VDD}
N 220 -40 270 -40 {lab=VDD}
N 220 -10 220 10 {lab=p}
N 220 70 220 90 {lab=Y}
N 220 80 320 80 {lab=Y}
N 220 150 220 170 {lab=n}
N 220 200 270 200 {lab=VSS}
N 220 230 220 260 {lab=VSS}
N 240 40 270 40 {lab=VDD}
N 240 120 270 120 {lab=VDD}
N 70 80 140 80 {lab=A}
N 140 -40 140 200 {lab=A}
N 140 -40 180 -40 {lab=A}
N 140 200 180 200 {lab=A}
C {TR-1umLIB/MP.sym} 180 -40 0 0 {name=XM1 model=PMOS w=13.5u l=1u m=1 spiceprefix=X}
C {TR-1umLIB/RR.sym} 220 10 0 0 {name=R1 w=2.8e-06 l=30e-06 R=1 model=F_RR spiceprefix=X m=1}
C {TR-1umLIB/RR.sym} 220 90 0 0 {name=R2 w=2.8e-06 l=30e-06 R=1 model=F_RR spiceprefix=X m=1}
C {TR-1umLIB/MN.sym} 180 200 0 0 {name=XM2 model=NMOS w=5u l=1u m=1 spiceprefix=X}
C {devices/iopin.sym} 220 -100 0 0 {name=p1 lab=VDD}
C {devices/iopin.sym} 220 260 0 0 {name=p2 lab=VSS}
C {devices/ipin.sym} 70 80 0 0 {name=p3 lab=A}
C {devices/opin.sym} 320 80 0 0 {name=p4 lab=Y}
C {devices/lab_pin.sym} 270 40 0 1 {name=p5 lab=VDD}
C {devices/lab_pin.sym} 270 120 0 1 {name=p6 lab=VDD}
C {devices/lab_pin.sym} 270 -40 0 1 {name=p7 lab=VDD}
C {devices/lab_pin.sym} 270 200 0 1 {name=p8 lab=VSS}
