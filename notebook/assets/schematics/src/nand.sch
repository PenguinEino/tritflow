v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
C {TR-1umLIB/MP.sym} 160 100 0 0 {name=XM1
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
C {TR-1umLIB/MP.sym} 380 100 0 0 {name=XM3
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
nrs=0
embed=true}
C {TR-1umLIB/MN.sym} 260 520 0 0 {name=XM2
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
C {TR-1umLIB/MN.sym} 260 640 0 0 {name=XM4
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
nrs=0
embed=true}
C {TR-1umLIB/RR.sym} 300 220 0 0 {name=R1
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
C {TR-1umLIB/RR.sym} 300 370 0 0 {name=R2
w=2.8e-06
R=1
l=30e-06
model=F_RR
spiceprefix=X
tc1=0
tc2=0
m=1
embed=true}
C {devices/iopin.sym} 300 40 0 0 {name=label1 lab=V+}
C {devices/ipin.sym} 100 100 0 0 {name=label2 lab=a}
C {devices/ipin.sym} 320 100 0 0 {name=label3 lab=b}
C {devices/opin.sym} 480 320 0 0 {name=label4 lab=vout}
C {devices/lab_pin.sym} 360 250 0 1 {name=label5 lab=V+}
C {devices/lab_pin.sym} 360 400 0 1 {name=label6 lab=V+}
C {devices/lab_pin.sym} 220 520 0 0 {name=label7 lab=a}
C {devices/lab_pin.sym} 220 640 0 0 {name=label8 lab=b}
C {devices/iopin.sym} 300 700 2 0 {name=label9 lab=V-}
N 200 60 300 60 {lab=V+}
N 300 60 420 60 {lab=V+}
N 200 60 200 70 {lab=V+}
N 420 60 420 70 {lab=V+}
N 200 130 200 180 {lab=#net1}
N 420 130 420 180 {lab=#net1}
N 200 180 300 180 {lab=#net1}
N 300 180 420 180 {lab=#net1}
N 300 180 300 220 {lab=#net1}
N 100 100 160 100 {lab=a}
N 320 100 380 100 {lab=b}
N 300 280 300 320 {lab=vout}
N 300 320 300 370 {lab=vout}
N 300 320 480 320 {lab=vout}
N 320 250 360 250 {lab=V+}
N 320 400 360 400 {lab=V+}
N 300 430 300 490 {lab=#net3}
N 300 550 300 610 {lab=#net2}
N 300 670 300 700 {lab=V-}
N 220 520 260 520 {lab=a}
N 220 640 260 640 {lab=b}
N 200 100 230 100 {lab=V+}
C {devices/lab_pin.sym} 230 100 0 1 {name=body_XM1 lab=V+}
N 420 100 450 100 {lab=V+}
C {devices/lab_pin.sym} 450 100 0 1 {name=body_XM3 lab=V+}
N 300 520 330 520 {lab=V-}
C {devices/lab_pin.sym} 330 520 0 1 {name=body_XM2 lab=V-}
N 300 640 330 640 {lab=V-}
C {devices/lab_pin.sym} 330 640 0 1 {name=body_XM4 lab=V-}
N 300 40 300 60 {lab=V+}
