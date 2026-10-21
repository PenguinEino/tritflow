## 2. 三値のINV

TritFlowのINVは、VDDとVSSの間にPMOS、抵抗、抵抗、NMOSを直列につないだ回路で、出力Yは2本の抵抗の間からとる。

| A | Y |
|---|---|
| −1（−5 V） | +1（+5 V） |
| 0（0 V） | 0（0 V） |
| +1（+5 V） | −1（−5 V） |

入力が±5 Vのときは片方のMOSだけがオンになり、Yはそちら側のレールに引かれる。入力が0 Vでは両方のMOSがオンになり、Yは上下の分圧で決まる。0のレベルは、上下の強さの釣り合いで作る。

<!-- asset: notebook/assets/schematics/INV.svg | テープアウトした回路図（Xschem） -->

### 手計算

オンのMOSを線形領域の抵抗 $r_{on} = 1/\left(\mu C_{ox} (W/L)(|V_{GS}|-|V_{th}|)\right)$ で近似する。$\mu$、$C_{ox}$、$V_{th}$ はPDKのモデルファイルから読む。上側を $R_u = r_{on,P} + R_{RP}$、下側を $R_d = r_{on,N} + R_{RN}$ とすると、入力0 Vでは

$$V_Y = V_{SS} + (V_{DD}-V_{SS})\frac{R_d}{R_u+R_d},\qquad I = \frac{V_{DD}-V_{SS}}{R_u+R_d}$$

<!-- code: hand -->

### SPICEで確かめる

同じ回路を、ngspiceとPDKのモデルでDC解析する。ボタンで入力を選ぶと、オンのMOSと電流の経路を示す。

<!-- code: inv_spice -->

### 寸法を変える

MOSの幅と長さ、抵抗の長さを変えると、0のレベルと静的電流が動く。スライダーは、テープアウトした寸法を含む90通りをSPICEで事前に計算した記録から選ぶ。記録は、回路、モデル、解析コードのハッシュで照合してから読む。

<!-- code: sizing -->
