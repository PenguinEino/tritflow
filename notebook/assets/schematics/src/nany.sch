v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
C {TR-1umLIB/MP.sym} 100 100 0 0 {name=XM5
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
nrs=0
embed=true}
[
v {xschem version=3.4.8RC file_version=1.3}
G {}
K {type=pmos
format="@spiceprefix@name @pinlist @model w=@w l=@l @extra nrd=@nrd nrs=@nrs m=@m"
lvs_format="M@name @pinlist @model w=@w l=@l m=@m"
template="name=XM1
model=PMOS
w=3.4u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0"
drc="fet_drc @name @symname @model @w @l"
}
V {}
S {}
F {}
E {}
L 4 20 -20 20 20 {}
L 4 20 0 40 0 {}
L 4 0 0 15 0 {}
L 4 20 -15 40 -15 {}
L 4 40 -30 40 -15 {}
L 4 20 15 40 15 {}
L 4 40 15 40 30 {}
L 4 15 -15 15 15 {}
B 5 38 28 42 32 {name=D dir=inout}
B 5 -2 -2 2 2 {name=G dir=inout}
B 5 38 -32 42 -28 {name=S dir=inout}
B 5 38 -2 42 2 {name=BG dir=inout}
P 4 4 38 0 30 -5 30 5 38 0 {fill=true
}
T {D} 44 21 0 0 0.22 0.22 {layer=13}
T {G} 2 3 0 0 0.22 0.22 {layer=13}
T {S} 44 -29 0 0 0.22 0.22 {layer=13}
T {BG} 44 3 0 0 0.22 0.22 {layer=13}
T {MP_@name} -80 -35 0 0 0.3 0.3 {}
T {w=@w
l=@l
m=@m} 76 15 0 0 0.28 0.28 {}
]
C {TR-1umLIB/MP.sym} 100 220 0 0 {name=XM3
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
nrs=0
embed=true}
C {TR-1umLIB/MN.sym} 100 610 0 0 {name=XM2
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
nrs=0
embed=true}
[
v {xschem version=3.4.8RC file_version=1.3}
G {}
K {type=nmos
format="@spiceprefix@name @pinlist @model w=@w l=@l @extra nrd=@nrd nrs=@nrs m=@m"
lvs_format="M@name @pinlist @model w=@w l=@l m=@m"
template="name=XM1
model=NMOS
w=3.4u
l=1u
m=1
spiceprefix=X
as=0
ad=0
ps=0
pd=0
nrd=0
nrs=0"
drc="fet_drc @name @symname @model @w @l"
}
V {}
S {}
F {}
E {}
L 4 20 15 40 15 {}
L 4 40 15 40 30 {}
L 4 20 0 40 0 {}
L 4 15 -15 15 15 {}
L 4 0 0 15 0 {}
L 4 20 -20 20 20 {fill=true
}
L 4 20 -15 40 -15 {}
L 4 40 -30 40 -15 {name=D dir=inout
}
B 5 38 -32 42 -28 {name=D dir=inout}
B 5 -2 -2 2 2 {name=G dir=inout}
B 5 38 28 42 32 {name=S dir=inout}
B 5 38 -2 42 2 {name=BG dir=inout}
P 4 4 20 -0 26 -4 26 4 20 0 {fill=true
}
T {D} 44 -29 0 0 0.22 0.22 {layer=13}
T {G} 2 3 0 0 0.22 0.22 {layer=13}
T {S} 44 21 0 0 0.22 0.22 {layer=13}
T {BG} 44 3 0 0 0.22 0.22 {layer=13}
T {MN_@name} -80 -35 0 0 0.3 0.3 {}
T {w=@w
l=@l
m=@m} 76 15 0 0 0.28 0.28 {}
]
C {TR-1umLIB/MN.sym} 100 730 0 0 {name=XM1
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
nrs=0
embed=true}
C {TR-1umLIB/RR.sym} 140 310 0 0 {name=R2
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1
embed=true}
[
v {xschem version=3.4.8RC file_version=1.3}
G {}
K {type=poly_resistor
format="@spiceprefix@name @pinlist @model w=@w l=@l R=@R tc1=@tc1 tc2=@tc2 m=@m"
lvs_format="X@name @pinlist @model w=@w l=@l m=@m"
template="name=R1
w=4e-06
R=1
l=13e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1"
drc="res_drc @name @symname @model @w @l"
}
V {}
S {}
F {}
E {}
L 4 10 30 20 30 {}
L 4 0 47 0 60 {}
L 4 -10 45 0 47 {}
L 4 -10 45 10 38 {}
L 4 -10 32 10 38 {}
L 4 -10 32 10 26 {}
L 4 -10 20 10 26 {}
L 4 -10 20 10 15 {}
L 4 0 11 10 15 {}
L 4 0 0 0 11 {}
B 5 -2 -2 2 2 {name=PLUS dir=inout}
B 5 -2 58 2 62 {name=MINUS dir=inout}
B 5 18 28 22 32 {name=SUB dir=inout}
T {PLUS} 5 -12 0 0 0.22 0.22 {layer=13}
T {MINUS} 5 59 0 0 0.22 0.22 {layer=13}
T {SUB} 24 34 0 0 0.22 0.22 {layer=13}
T {RR_@name} -100 -8 0 0 0.3 0.3 {}
T {+} -12 0 0 0 0.22 0.22 {layer=4}
T {RR} -100 12 0 0 0.28 0.28 {layer=4}
T {tcleval(R= [if \{@w ==2.8e-6\} \{ev \{
  -0.1716 * ((@l *1e6) ** 2) + 486.5 * (@l *1e6)  - 3605.5
\}\} elseif \{@w ==4.0e-6\} \{ev \{
  834.54 * ((@l *1e6-9.2) /(@w *1e6-1.09)) + 13.3 * (9.2/(@w *1e6-1.09)+3.38/(@w *1e6-1.8))+ 2.79 - 21.06*3.95 + 615.2
\}\} elseif \{@w ==6.0e-6\} \{ev \{
  834.54 * ((@l *1e6-9.2) /(@w *1e6-1.09)) + 13.3 * (9.2/(@w *1e6-1.09)+3.38/(@w *1e6-1.8))+ 2.79 - 21.0*4.0 + 366.4
\}\} elseif \{@w ==12.0e-6\} \{ev \{
  834.54 * ((@l *1e6-9.2) /(@w *1e6-1.09)) + 13.3 * (9.2/(@w *1e6-1.09)+3.38/(@w *1e6-1.8))+ 2.79 - 21.0*11.9 + 368.9
\}\} elseif \{@w ==20.0e-6\} \{ev \{
  834.54 * ((@l *1e6-9.2) /(@w *1e6-1.09)) + 13.3 * (9.2/(@w *1e6-1.09)+3.38/(@w *1e6-1.8))+ 2.79 - 21.0*20.1 + 495.8
\}\} ])} -100 75 0 0 0.26 0.26 {}
T {w=@w} -100 30 0 0 0.26 0.26 {}
T {l=@l} -100 45 0 0 0.26 0.26 {}
T {m=@m} -100 60 0 0 0.26 0.26 {}
]
C {TR-1umLIB/RR.sym} 140 460 0 0 {name=R1
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1
embed=true}
C {TR-1umLIB/MP.sym} 300 460 0 0 {name=XM6
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
nrs=0
embed=true}
C {TR-1umLIB/MN.sym} 300 580 0 0 {name=XM7
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
nrs=0
embed=true}
C {TR-1umLIB/MP.sym} 500 460 0 0 {name=XM8
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
nrs=0
embed=true}
C {TR-1umLIB/MN.sym} 500 580 0 0 {name=XM9
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
nrs=0
embed=true}
C {devices/iopin.sym} 140 40 0 0 {name=l1 lab=VDD}
C {devices/ipin.sym} 60 100 0 0 {name=lab1 lab=a}
C {devices/ipin.sym} 60 220 0 0 {name=lab2 lab=b}
C {devices/opin.sym} 560 410 0 0 {name=lab3 lab=vout}
C {devices/lab_pin.sym} 200 340 0 1 {name=lab4 lab=VDD}
C {devices/lab_pin.sym} 200 490 0 1 {name=lab5 lab=VDD}
C {devices/lab_pin.sym} 60 610 0 0 {name=label7 lab=a}
C {devices/lab_pin.sym} 60 730 0 0 {name=label8 lab=b}
C {devices/iopin.sym} 140 790 2 0 {name=l4 lab=VSS}
C {devices/iopin.sym} 340 660 0 0 {name=gload lab=VMID}
C {devices/lab_pin.sym} 540 660 0 0 {name=gload1 lab=VMID}
C {devices/lab_pin.sym} 280 460 0 0 {name=label1 lab=a}
C {devices/lab_pin.sym} 480 460 0 0 {name=label2 lab=b}
C {devices/lab_pin.sym} 280 580 0 0 {name=label3 lab=b}
C {devices/lab_pin.sym} 480 580 0 0 {name=label4 lab=a}
C {devices/lab_pin.sym} 370 460 0 1 {name=lab6 lab=VDD}
C {devices/lab_pin.sym} 570 460 0 1 {name=lab7 lab=VDD}
C {devices/lab_pin.sym} 370 580 0 1 {name=lab8 lab=VSS}
C {devices/lab_pin.sym} 570 580 0 1 {name=lab9 lab=VSS}
N 140 40 140 70 {lab=VDD}
N 140 130 140 190 {lab=#net1}
N 140 250 140 310 {lab=#net2}
N 140 370 140 410 {lab=vout}
N 140 410 140 460 {lab=vout}
N 140 410 340 410 {lab=vout}
N 340 410 540 410 {lab=vout}
N 540 410 560 410 {lab=vout}
N 140 520 140 580 {lab=#net3}
N 140 640 140 700 {lab=#net4}
N 140 760 140 790 {lab=VSS}
N 60 100 100 100 {lab=a}
N 60 220 100 220 {lab=b}
N 60 610 100 610 {lab=a}
N 60 730 100 730 {lab=b}
N 160 340 200 340 {lab=VDD}
N 160 490 200 490 {lab=VDD}
N 340 410 340 430 {lab=vout}
N 340 490 340 550 {lab=#net5}
N 340 610 340 660 {lab=VMID}
N 540 410 540 430 {lab=vout}
N 540 490 540 550 {lab=#net6}
N 540 610 540 660 {lab=VMID}
N 140 100 170 100 {lab=VDD}
N 140 220 170 220 {lab=VDD}
N 140 610 170 610 {lab=VSS}
N 140 730 170 730 {lab=VSS}
N 340 460 370 460 {lab=VDD}
N 540 460 570 460 {lab=VDD}
N 340 580 370 580 {lab=VSS}
N 540 580 570 580 {lab=VSS}
N 280 460 300 460 {lab=a}
N 480 460 500 460 {lab=b}
N 280 580 300 580 {lab=b}
N 480 580 500 580 {lab=a}
N 170 60 170 100 {lab=VDD}
N 170 100 170 220 {lab=VDD}
N 140 60 170 60 {lab=VDD}
N 170 610 170 730 {lab=VSS}
N 170 730 170 790 {lab=VSS}
N 140 790 170 790 {lab=VSS}
