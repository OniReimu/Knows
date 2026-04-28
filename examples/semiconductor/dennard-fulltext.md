\[3\]E.J.Boleky.“Subnanosecond switching delays using CMOS/ SOS silicon-gate technology,”in 1971 Int.Solid-State Circuit Conf.,Dig.Tech.Papers,p.225.

\[4\]E.J.Boleky and J.E.Meyer,“High-performance low-power CMOS memories using silicon-on-sapphire technology," IEEE J.Solid-State Circuits (Special Issue on Micropower Electronics)，vol. SC-7,pp.135-145,Apr.1972.

\[5\]R.W.Bower,H.G.Dill,K.G.Aubuchon,and S.A.Thompson,“MOS field effect transistors by gate masked ion implantation,”IEEE Trans.Electron Devices,vol.ED-15,pp. 757-761,Oct. 1968.

\[6\] J.Tihanyi，“Complementary ESFI MOS devices with\_ gate selfadjustment by ion implantation,”in Proc.5th Int.Conf. Microelectronics in Munich，Nov.27-29,1972.MinchenWien,Germany:R.Oldenbourg Verlag，pp.437-447.

\[7\]E.J.Boleky，“The performance of\_complementary MOS transistors on insulating substrates,”RCA Rev.,vol. 30,pp. 372-395,1970.

\[8\] K.Goser,“Channel formation in an insulated gate field effect transistor(IGFET）and its equivalent circuit,”Siemens Forschungs- und Entwicklungsberichte,no.1,pp.3-9,1971.

\[9\]A.E.Ruehli and P.A.Brennan,“Accurate metallization capacitances for integrated circuits and packages,”IEEEJ. Solid-State Circuits (Corresp.)，vol. SC-8,pp.289-290,Aug. 1973.

10\] SINAP (Siemens Netzwerk Analyse Programm Paket), Siemens AG,Munich,Germany.

:11\]K.Goser and K.Steinhubl,“Aufteilung der Gate-KanalKapazitat auf Source und Drain im Ersatzschaltbild eines MOS-Transistors." Siemens Forschungs- und Entwicklungsberichte1,no.3,pp.284-286,1972.

\[12\] J.R. Burns,“Switching response of complementary-symmetry MOS transistors logic circuits,”RCA Rev.，vol.25, pp.627-681,1964.

\[13\] R.W.Ahrons and P.D.Gardner,“Introduction of technology and performance in complementary symmetry circuits,IEEE J.Solid-State Circuits(Special Issue on Technology for Integrated-Circuit Design),vol. SC-5,pp.24-29, Feb.1970.

\[14\]F.F.Fang and H. Rupprecht,“High performance MOS integrated circuitsusing ion implantation technique,” presented at the 1973 ESSDERC,Munich,Germany. Michael Pomper,for a photograph and biography，please see p.

238 of this issue. Jeno Tihanyi, for a photograph and biography，please see p.

238 of this issue.

# Design of Ion-Implanted MOSFET's with Very Small Physical Dimensions

ROBERT H. DENNARD, MEMBER, IEEE,FRITZ H. GAENSSLEN,HWA-NIEN YU, MEMBER, IEEE,V. LEC RIDEOUT, MEMBER, IEEE, ERNEST BASSOUS, AND ANDRE R. LEBLANC, MEMBER, IEEE

Abstract-This paper considers the design，fabrication，and characterization of very small MOSFET switching devices suitable for digital integrated circuits using dimensions of the order of $\\textbf { 1 } \\mu .$ Scaling relationships are presented which show how a conventional MOSFET can be reduced in size.An improved small device structure is presented that uses ion implantation to provide shallow source and drain regions and a nonuniform substrate doping profile.One-dimensional models are used to predict the substrate doping profile and the corresponding threshold voltage versus source voltage characteristic.A two-dimensional current transport model is used to predict the relative degree of short-channel effects for different device parameter combinations. Polysilicon-gate MOSFET's with channel lengths as short as $\\mathbf { 0 . 5 ~ } \_ { \\mu }$ were fabricated, and the device characteristics measured and compared with predicted values.The performance improvement expected from using these very small devices in highly miniaturized integrated circuits is projected.

Manuscript received May 20,1974；revised July 3,1974. The authors are with the IBM T.J.Watson Research Center, Yorktown Heights,N.Y.10598.

LIST OF SYMBOLS

$\\alpha$ （20 Inverse semilogarithmic slope of subthreshold characteristic.

$\\mathcal { D }$ （204号 Width of idealized step function profile for channel implant.

（204号 $\\Delta W \_ { f }$ （204号 Work function difference between gate and substrate.

$\\epsilon \_ { \\mathrm { s i } } , \\epsilon \_ { \\mathrm { o x } }$ （204号 Dielectric constants for silicon and silicon dioxide.

${ \\cal I } \_ { d }$ （20 Drain current.

$\\boldsymbol { k }$ （204号 Boltzmann's constant.

$\\kappa$ （204 Unitless scaling constant.

$L$ （20 MOSFET channel length.

$\\mu \_ { \\mathrm { e f f } }$ （204号 Effective surface mobility.

$n \_ { \\imath }$ Intrinsic carrier concentration.

$\\smash { { N \_ { s } } }$ （20 Substrate acceptor concentration.

$\\Psi \_ { s }$ （204号 Band bending in silicon at the onset of strong inversion for zero substrate voltage. $\\Psi \_ { b }$ （204号 Built-in junction potential.

$q$ （20 Charge on the electron.

$Q \_ { \\textrm { e f f } }$ （204号 Effective oxide charge.

（20 $t \_ { \\mathrm { o x } }$ （20 Gate oxide thickness.

（204号 $\\boldsymbol { T }$ （20号 Absolute temperature.

$\\dot { V } \_ { d } , V \_ { s } , V \_ { o } , V \_ { \\mathrm { s u b } }$ （20 Drain, source,gate and substrate voltages.

（20 $V \_ { d s }$ Drain voltage relative to source.

Vs-sub Source voltage relative to substrate.

$\\boldsymbol { V } \_ { t }$ （20 Gate threshold voltage.

$w \_ { s } , w \_ { d }$ （20 Source and drain depletion layer widths.

W MOSFET channel width.

# INTRODUCTION

TEWHIGH resolution lithographic techniques for forming semiconductor integrated circuit patterns offera decreasein linewidthof fivetotentimes over the optical contact masking approach which is commonly used in the semiconductor industry today.Of the new techniques,electron beam pattern writing has been widely used for experimental device fabrication \[1\]-\[4\] while X-ray lithography \[5\] and optical projection printing \[6\] have also exhibited high-resolution capability. Full realization of the benefits of these new high-resolution lithographic techniques requires the development of new device designs,technologies，and structures which can be optimized for very small dimensions.

This paper concerns the design,fabrication,and characterization of very small MOSFET switching devices suitable for digital integrated circuits using dimensions of the order of $\\mathrm { ~ \\bf ~ { ~ 1 ~ } ~ } \_ { \\mu }$ .It is known that reducing the sourceto-drain spacing (i.e.，the channel length） of an FET leads to undesirable changes in the device characteristics. These changes become significant when the depletion regions surrounding the source and drain extend over a large portion of the region in the silicon substrate under the gate electrode.For switching applications,the most undesirable“short-channel”effect is a reduction in the gate threshold voltage at which the device turns on,which is aggravated by high drain voltages.It has been shown that these short-channel effects can be avoided by scaling down the vertical dimensions (e.g.，gate insulator thickness，junction depth，etc.） along with the horizontal dimensions，while also proportionately decreasing the applied voltages and increasing the substrate doping concentration \[7\]，\[8\].Applying this scaling approach to.a properly designed conventional-size MOSFET shows that a $2 0 0 \\mathrm { - } \\dot { \\mathrm { \\AA } }$ gate insulator is required if the channel length is to be reduced to $\\mathrm { ~ i ~ } \_ { \\mu }$

A major consideration of this paper is'to show how the use of ion implantation leads to an improved design for very small scaled-down MOSFET's.First,the ability of ion implantation to accurately introduce a low concentration of doping atoms allows the substrate doping profile in the channel region under the gate to be increased in a controlled manner.When combined with a relatively lightly doped starting substrate,this channel implant reduces the sensitivity of the threshold voltage tochanges in the source-to-substrate("backgate")bias. Thisreduced“substrate sensitivity"can then be traded off for a thicker gate insulator of 35O-A thickness which tends to be easier to fabricate reproducibly and reliably. Second,ion implantation allows the formation of very shallow source and drain regions which are more favorablewith respect to short-channel effects，while maintaining an acceptable sheet resistance.The combination of these features in an all-implanted design gives a switching device which can be fabricated witha thicker gateinsulatorif desired,which has well-controlled threshold characteristics,and which has significantly reduced interelectrode capacitances (e.g.,drain-to-gate or drainto-substrate capacitances).

![](http://stanford.edu/class/cs114/readings/images/a912a88d300a16a993c0cb45f8149f4d1778b9fd49795a2f725feb2149b9f989.jpg)

Fig.1.Illustration of device scaling principles with $\\kappa = 5$ (a） Conventional commercially available device structure.(b) Scaled-down device structure.

This paper begins by describing the scaling principles which are applied to a conventional MOSFET to obtain a very small device structure capable of improved performance. Experimental verification of the scaling approach is then presented.Next，the fabrication process for an improved scaled-down device structure using ion implantation is described.Design considerations for this all-implanted structure are based on two analytical tools: asimple one-dimensional model that predicts the substrate sensitivity for long channel-length devices,and a two-dimensional current-transport model that predicts the device turn-on characteristics as a function of channel length.The predicted results from both analyses are compared with experimental data.Using the two-dimensional simulation，the sensitivity of the design to various parameters is shown.Then,detailed attention is given to 'an alternate design,intended for zero substrate bias,which offers some advantageswith respect to threshold control.Finally，the paper concludes with a discussion of the performance improvements to be expected from integrated circuits that use these very small FET's.

# DEVICE SCALING

The principles of device scaling \[7\]，\[8\] show in a concise manner the general design trends to be followed in decreasing the size and increasing the performance of MOSFET switching devices.Fig.1 compares a state-ofthe-art n-channel MOSFET \[9\] with a scaled-down device designed following the device scaling principles to be described later.The larger structure shown in Fig 1(a)is reasonably typical of commercially available devices fabricated by using conventional diffusion techniques.It uses a 1ooo-A gate insulator thickness with a substrate doping and substrate bias chosen to give a gate threshold voltage $\\boldsymbol { \\mathrm { J } } \_ { t \_ { t } } ^ { \\star }$ of approximately $2 \\mathrm { ~ V ~ }$ relative to the source potential.A substrate doping of $5 \\times 1 0 ^ { 1 5 }$ $\\mathrm { c m } ^ { - 3 }$ is low enough to give an acceptable value of substrate sensitivity.The substrate sensitivity is an important criterion in digital switching circuits employing source followers because the design becomes difficult if the threshold voltage increases by more than a factor of two over the full range of variation of the source voltage. For the device illustrated in Fig. 1(a)，the design parametcrs limit the channel length $L$ to about $5 ~ \\mu$ This restriction arises primarily from the penetration of the depletion region surrounding the drain into the area normally controlled by the gate electrode.For a maximum drain voltage of approximately $1 2 \\mathrm { - } 1 5 \\mathrm { ~ V ~ }$ this penetration will modify the surface potential and significantly lower the threshold voltage.

In order to design a new device suitable for smaller values of $L$ ，the device is scaled by a transformation in three variables: dimension，voltage，and doping. First, all linear dimensions are reduced by a unitless scaling factor $\\pmb { \\kappa }$ ,e.g.， ${ t \_ { \\mathrm { { o x } } } } ^ { \\prime } \\doteq { t \_ { \\mathrm { { o x } } } } / \\kappa$ ，where the primed parameters refer to the new scaled-down device.This reduction includes vertical dimensions such as gate insulator thickness，junction depth，etc.，as well as the horizontal dimensions of channel length and width.Second,the voltagesapplied to the device are reduced by the same factor (e.g., $V \_ { d s } ^ { \\prime } = V \_ { d s } / \\kappa$ ).Third, the substrate doping concentration is increased,again using the same scaling factor (i.e., $N \_ { a } ^ { ~ \\prime } = \\kappa N \_ { a } ^ { ~ \\prime }$ .The design shown in Fig. 1(b)was obtained using $\\kappa = 5$ which corresponds to the desired reduction in channel length to $1 \ \\mu$

The scaling relationships were developed by observing that the depletion layer widths in the scaled-down device arc reduced in proportion to the device dimensions due to the reduced potentials and the increased doping.For example,

$$
w \_ { s } ^ { ~ \\prime } = { \[ 2 \\epsilon \_ { \\scriptscriptstyle \\mathrm { S I } } ( { \\psi } \_ { b } ^ { ~ \\prime } + V \_ { s - s u b } / \\kappa ) \] / q \\kappa N \_ { a } } ^ { 1 / 2 } \\simeq w \_ { s } / \\kappa .
$$

p-type substrates） the work function difference $\\Delta \\left\[ V \_ { f } \\right\]$ is of opposite sign，and approximately canccls out ${ \\psi } \_ { s } ^ { \\prime }$ ， ${ \\psi \_ { s } } ^ { \\prime }$ is the band bending in the silicon (i.e.,the surface potential）at the onset of strong inversion for zero substrate bias.It would appear that the $\\psi ^ { \\prime }$ terms appearing in (1) and (2） prevent exact scaling since they remain approximately constant,actually increasing slightly due to the increased doping since $\\psi \_ { b } ^ { ~ \\prime } \\simeq \\psi \_ { s } ^ { ~ \\prime } = ~ ( 2 k T / q )$ lm $( N \_ { a } ^ { \\prime } / n \_ { \\imath } )$ ： However, the fixed substrate bias supply normally used with n-channel devices can bc adjusted so that $( \\psi \_ { s } ^ { ~ \\prime } ~ +$ $V \_ { \\mathrm { s u b } ^ { \\prime } } ) ~ = ~ ( \\psi \_ { s } ~ + ~ V \_ { \\mathrm { s u b } } ) / \\kappa$ . Thus,by scaling down the applied substrate bias more than the other applied voltages, the potential drop across the source or drain junctions, or across the depletion region under the gate,can be reduced by $\\kappa$ ，

All of the cquations that describe the MOSFET device characteristics may be scaled as demonstrated above.For example,the MOSFET current equation \[9\] given by

$$
I \_ { d } ^ { \\prime } = \\frac { \\mu \_ { \\mathrm { e f f } } \\epsilon \_ { \\mathrm { o x } } } { t \_ { \\mathrm { o x } } / \\kappa } \\bigg ( \\frac { W / \\kappa } { L / \\kappa } \\bigg ) \\bigg ( \\frac { V \_ { o } - V \_ { t } - V \_ { d } / 2 } { \\kappa } \\bigg ) ( V \_ { d } / \\kappa ) = I \_ { d } / \\kappa
$$

is seen to be reduced by a factor of $\\kappa$ ,for any given set of applied voltages，assuming no change in mobility. Actually,the mobility is reduced slightly due to increased impurity scattering in the heavier doped substrate.

It is possible to generalize the scaling approach to include electric field patterns and current density.The electric field distribution is maintained in the scaleddown device except for a change in scale for the spatial coordinates.Furthermore,the electric field strength at any corresponding point is unchanged because $V / x =$ $\\mathrm { V ^ { \\prime } } / { x ^ { \\prime } }$ .Thus,the carrier velocity at any point is also unchanged due to scaling and，hence，any saturation velocity effects will be similar in both devices,neglecting microscopic differences due to the fixed crystal lattice dimensions.From (3),since the device current is reduced by $\\kappa$ ,the channel current per unit of channel width W is unchanged by scaling.This is consistent with the same shcet density of carriers (i.e.,electrons per unit gate area) moving at the same velocity.In the vicinity of the drain, the carriers will move away from the surface to a lesser extent in the new device,due to the shallower diffusions Thus,the density of mobile carriers per unit volume will bc higher in the space-charge region around the drain, complementing the higher density of immobile charge due to the heavier doped substrate.Other scaling relationships for power density，delay time，etc.，are given in Table I and will be discussed in a subsequent section on circuit performance.

The threshold voltage at turn-on \[9\] is also decreased in direct proportion to the reduced device voltages so that the devicc will function properly in a circuit with reduced voltage levels.This is shown by the threshold voltage equation for the scaled-down device.

$$
\\begin{array} { r } { V \_ { t } ^ { \\prime } = ( t \_ { \\mathrm { o x } } / \\kappa \\epsilon \_ { \\mathrm { o x } } ) \\lbrace - Q \_ { \\mathrm { e f f } } + \[ 2 \\epsilon \_ { \\mathrm { s } , q \\kappa } N \_ { a } ( \\psi \_ { s } ^ { \\prime } + V \_ { s - \\mathrm { s u b } } / \\kappa ) \] ^ { 1 / 2 } \\rbrace } \ { + ( \\Delta W \_ { f } + \\psi \_ { s } ^ { \\prime } ) \\simeq V \_ { t } / \\kappa . \\qquad ( \\mathrm { i } } \\end{array}
$$

In (2）the reduction in $\\boldsymbol { \\mathrm { J } } \_ { \\mathrm { ~ t ~ } } ^ { \\mathsf { ^ { \* } } }$ is primarily due to the decreased insulator thickness, $t \_ { \\mathrm { o x } } / \\kappa$ ，while the changes in the voltage and doping tcrms tend to cancel out.In most cases of interest (i.e.，polysilicon gates of doping type opposite to that of the substrate or aluminum gates on

In order to verify the scaling relationships, two sets of experimental deyices were fabricated with gate insulators of 1000 and $2 0 0 \\textup { \\AA }$ (i.e., $\\kappa = 5$ ).The mcasured drain voltage characteristics of these devices,normalized to $W / L = 1$ are shown in Fig.2. The two sets of characteristics are quite similar when plotted with voltage and current scales of the smaller device reduced by a factor of five,which confirms the scaling predictions.In Fig.2，the exact match on the current scale is thought to be fortuitous since there is some experimental uncertainty in the magnitude of the channcl length used to normalize the characteristics (see Appendix).More accurate data from devices with largcr width and length dimensions on the same chip shows an approximate reduction of ten pcrcent in mobility for deviccs with the heavier dopcd substratc.That the threshold voltage also scales corrcctly by a factor of five is verified in Fig.3,which shows the expcrimcntal $\\sqrt { I \_ { d } }$ versus $\\boldsymbol { V } \_ { g }$ turn-on characteristics for thc original and the scaled-down devices.For the cases shown，thc drain voltage is large enough to cause pinchoff and the characteristics exhibit thc cxpccted linear relationship. Whcn projected to interccpt thc gate voltage axis this linear relationship defines a threshold voltage useful for most logic circuit design purposcs.

![](http://stanford.edu/class/cs114/readings/images/01fd825686f60128e7c6d9ae726ed54d9a24167f9b9f49789b210df277f3ff32.jpg)

Fig.2. Expcrimental drain voltage characteristics for (a） conventional,and (b)scaled-down structures shown in Fig.1 normalized to $W / L = 1$ ·

![](http://stanford.edu/class/cs114/readings/images/f3766dd3672ada9647ef95b4b3591181e4f86171f574a7cbdf522d4989023229.jpg)

Fig.3. Experimental turn-on characteristics for conventional and scaled-down devices shown in Fig.1 normalized to $W / L$ $= 1$ ：

Oncarca in which the devicc characteristics fail to scale is in the subthrcshold or weak inversion region of the turn-oncharactcristic.Belowthrcshold, $\\boldsymbol { I } \_ { d }$ is exponentially dependent on $\\boldsymbol { V } \_ { g }$ with an inversc scmilogarithmic slope, $\\alpha$ ，\[10\],\[11\]which for thc scaled-down dcvice is given by

$$
\\begin{array} { r l r } { { \\alpha ^ { \\prime } \\Big ( \\frac { \\mathrm { v o l t s } } { \\mathrm { d c e a d e } } \\Big ) = \\frac { d { V \_ { g } } ^ { \\prime } } { d \\log \_ { 1 0 } I \_ { d } ^ { \\prime } } } } \ & { } & { = ( k T / q \\log \_ { 1 0 } e ) \\Big ( 1 + \\frac { \\epsilon \_ { \\mathrm { s i } } t \_ { \\mathrm { o x } } / \\kappa } { \\epsilon \_ { \\mathrm { o x } } \\psi \_ { d } / \\kappa } \\Big ) , } \\end{array}
$$

which is the same as for the original larger device.The paramctcr α is important to dynamic memory circuits because it determines the gate voltage excursion required to go from the low current“off"state to the high current “on”state \[11\].In an attempt to also extend the linear scaling relationships to α one could reduce the operating temperature in (4) (i.e.,T'= T/κ),but this would cause a significant increase in the effective surface mobility \[12\]and thereby invalidate the current.scaling relationship of (3).In ordcr to design dcvices for operation at room temperature and above,one must accept the fact that the subthrcshold behavior does not scale'as desired. This nonscaling property of the subthreshold characteristic is of particular concern to miniature dynamic memory circuits which require low source-to-drain leakage currents.

![](http://stanford.edu/class/cs114/readings/images/64d68964459acb59c7fc73b067d1fdc4553e435a03b145101f1f5ab9663be4fb.jpg)

Fig.4.Detailed cross sections for (a） scaled-down device structure，and (b) corresponding ion-implanted device structure.

# ION-IMPLANTED DEVICE DESIGN

The scaling considerations just presented lead to the device structure with a 1- ${ \\bf \\nabla } \\cdot { \\bf \\nabla } \\mu ^ { \\mathrm { ~ ~ } }$ channel length shown in Fig 4(a).In’contrast， the corresponding improved design utilizing the capability afforded by ion implantation is shown in Fig. 4(b).The ion-implanted device uses an initial substrate doping that is lower by about a factor of.four,and an implanted boron surface layer having a concentration·somewhat greater than the concentration used throughout the unimplanted structure of Fig.4(a). The.concentration and the depth of the implanted surface layer are chosen so that this heavier doped region will be completely within the surface depletion layer when the device is turned on with the source grounded. Thus,when:the source is biased above ground potential, the'depletion'·layer will extend deeper into the lighter doped substrate，and the additional exposed “bulk" charge will be reasonably small and will cause only a modest increase in the gate-to-source voltage required to turn on the device.With this improvement in substrate sensitivity the'gate insulator thickness can be increased toasmuch as 35oAand still maintain a reasonable gate threshold voltagc as will be shown later.

Another aspect of the design philosophy is to use shallow implanted 'n+regions of depth comparable to the implanted p-type surface layer. The depletion regions under the gate electrode at the edges of the source and drain are then inhibited by the heavier doped surface layer,roughly pictured in Fig.4(b)，for the case of a turned-off device.The depletion regions under the source and drain extend much further into the lighter doped substrate.With deeper junctions these depletion regions would tend to merge in the lighter doped material which would cause a loss of threshold control or, in the extreme, punchthrough at high drain voltages.However,the shallower junctions give a more favorable electric field pattern which avoids these effects when the substrate doping concentration is properly chosen (i.e.,when it is not too light).

The device capacitances are reduced with the ion-implanted structure due to the increased depletion layer width separating the source and drain from the substrate \[cf.Figs.4(a)and 4(b)\],and due to the natural selfalignment afforded by the ion implantation process which reduces the overlap of: the polysilicon gate over the source and drain regions.The thicker gate insulator also gives reduced gate capacitance，but the performance benefit in this respect is offset by the decreased gate field. To compensate for the thicker gate oxide and the expected threshold increase,a design objective for maximum drain voltage was set at $4 \\mathrm { ~ V ~ }$ for the ion-implanted design in Fig.4(b)，compared to 3 V for the scaled-down device of Fig.4(a).

# FABRICATION OF ION-IMPLANTED MOSFET'S

The fabrication process for the ion-implanted MOSFET's used in this study will now be described. A fourmask process was used to fabricate polysilicon-gate, n-channel MOSFET's on a test chip which contains devices with channel lengths ranging from 0.5 to $1 0 ~ \\mu$ 号 Though the eventual aim is to use electron-beam pattern exposure,it was more convenient to use contact masking with high quality master masks for process development.For this purpose high resolution is required only for the gate pattern which uses lines as small as $1 . 5 ~ \\mu$ which are reduced in the subsequent processing. The starting substrate resistivity was $2 \\cdot \\mathrm { { \\Omega } } \\cdot \\mathrm { { c m } } ^ { \\cdot }$ (i.e.，about $7 . 5 \\times 1 0 ^ { 1 5 } ~ \\mathrm { c m ^ { - 3 } } )$ .Themethod of fabrication for the thick oxide isolation between adjacent FET's is not described as'it is not essential to the work presented here,and because several suitable techniques are available.Following dry thermal growth of the gate oxide，low energy （204号 $( 4 0 \\mathrm { \ k e V } )$ ,lowdose ${ \\bf 6 . 7 \\times 1 0 ^ { 1 1 } }$ atoms/ $\\mathrm { c m } ^ { 2 }$ 一 $\\mathrm { B ^ { 1 1 } }$ ions were implanted into the wafers,raising the boron doping near the silicon surface.All implantations were performed after gate oxide growth in order to restrict diffusion of the implanted regions.

After-the.channel implantation，a 35oo-A thick polysilicon layer was deposited,doped $\\mathrm { n ^ { + } }$ ,and the gate regions delineated. Next, $\\boldsymbol { \\mathrm { n } } ^ { + }$ source and drain regions 2000-A deepwere formed bya high energy $( 1 0 0 \\mathrm { k e V } )$ ,high dose $( 4 ~ \\times ~ 1 0 ^ { 1 5 }$ atoms/ $\\mathrm { { c } \\mathrm { { m } ^ { 2 } } }$ ） $\\mathrm { A s ^ { 7 5 } }$ implantation through the same 35o-A oxide layer.During this step,however, the polysilicon gate masks the channel region from the implant,absorbing all of the $\\mathbf { A } \\mathbf { s } ^ { 7 5 }$ dose incident there.The etching process used to delineate the gates results in a sloping sidewall which allows a slight penetration of $\\mathbf { A } \\mathbf { s } ^ { \\pmb { 7 5 } }$ ions underneath the edges of the gates.The gate-to-drain (or source) overlap is estimated to be of the order of 0.2 $\\mu$ .The high temperature processing steps that follow the implantations include 2O min at $9 0 0 ^ { \\circ } \\mathrm { C }$ ，and11 min at $1 0 0 0 ^ { \\circ } \\mathrm { C }$ ，which is more than adequate to anneal out the implantation damage without greatly spreading out the implanted doses.Typical sheet resistances were $5 0 ~ \\Omega / \\bigtriangledown$ for the source and drain regions,and $4 0 \\Omega / \\bigtriangledown$ for the polysilicon areas.Following the $\\mathbf { A } \\mathbf { s } ^ { 7 5 }$ implant,a final insulating oxide layer $\\mathbf { \\dot { 2 0 0 0 - A } }$ thick was deposited using low-temperature chemical-vapor deposition.Then，the contact holes to the $\\mathfrak { n } ^ { \\star }$ and polysilicon regions were defined,and the metalization was applied and delineated. Electrical contact directly to the shallow implanted source and drain regions was accomplished by a suitably chosen metallurgy to avoid junction penetration due to alloying during the final annealing step.After metalization an annealing step of $4 0 0 ~ ^ { \\circ } \\mathrm { C }$ for $2 0 ~ \\mathrm { m i n }$ in forming gas was performed to decrease the fast-state density.

![](http://stanford.edu/class/cs114/readings/images/119cba62aea5642e5e6537891d8270ba25c3a6457ca376e0a73480f88a079d56.jpg)

Fig.5.Predicted substrate doping profile for basic ion-implanted device design for $4 0 \ \\mathrm { k e V }$ B11 ions implanted through the 350-A gateinsulator.

![](http://stanford.edu/class/cs114/readings/images/b11f7a4824046f69d732b6f2f9e34ab49372da97e151d18687f46612693110d2.jpg)

Fig.6.Calculated and experimental substrate sensitivity characteristics for non-implanted devices with 200- and $3 5 0 \\mathrm { - } \\mathrm { \\AA }$ gate insulators,and for corresponding ion-implanted device with 350-A gate insulator.

# ONE-DIMENSIONAL （LONG CHANNEL） ANALYSIS

The substrate doping profile for the $4 0 { \\mathrm { \ k e V } }$ ${ \\bf 6 . 7 \\times 1 0 ^ { 1 1 } }$ atoms/ $\\mathrm { { c m ^ { 2 } } }$ channel implant incident on the 35O-A gate oxide,is shown in Fig.5.Since the oxide absorbs 3 percent of the incident dose,the active dose in the silicon is $6 . 5 \\times 1 0 ^ { 1 1 }$ atoms/ $\\mathrm { c m ^ { 2 } }$ .The concentration at the time of the implantation is given by the lightly dashed Gaussian function added to the background doping level, ${ { N } \_ { b } }$ For $4 0 { \\mathrm { \ k e V \ B ^ { 1 1 } } }$ ions,the projected range and standard deviation were taken as $1 3 0 0 \\mathrm { ~ \\AA ~ }$ and $5 0 0 \\mathrm { ~ \\AA ~ }$ ，respectively \[13\].After thc heat treatments of the subsequent processing,the boron is redistributed as shown by the heavier dashed line.These predicted profiles were obtained using a computer program developed by F.F.Morehead of our laboratories.The program assumes that boron atoms diffusing in the silicon reflect from the silicon-oxide interface and thereby raise the surface concentration.For modeling purposes it is convenient to use a simple,idealized,step-function representation of the doping profile as shown by the solid line in Fig. 5. The step profile approximates the final predicted profile rather well and offers the advantage that it can be described bya few simple parameters.The three profiles shown in Fig.5 all have the same active dose.

Using the step profle,a model for determining threshold voltage has been developed from piecewise solutions of Poisson's equation with appropriate boundary conditions \[11\].The one-dimensional model considers only the vertical dimension and cannot account for horizontal short-channel effects.Results of the model are shown in Fig.6 which plots the threshold voltage versus sourceto-substrate bias for the ion-implanted step profile shown in Fig.5.For comparison,Fig.6 also shows the substrate sensitivity characteristics for the nonimplanted device with a 2oo-A gate insulator and a constant background doping，and for a hypothetical device having a 350-A gate insulator like the implanted structure and a constant background doping like the nonimplanted structure. The nonimplanted $2 0 0 \ – \ 8$ case exhibits a low substrate sensitivity,but the magnitude of the threshold voltage is also low.On the other hand,the nonimplanted 350-A case showsa highcr threshold,but with an undesirably high substrate sensitivity.The ion-implanted case offers both a sufficiently high threshold voltage and a reasonably low substrate sensitivity，particularly for $V \_ { s - s u b } \ \\geq$ $\_ { 1 \\mathrm { ~ V ~ } }$ .For $V \_ { s \\cdots \\mathbf { s u b } } < \\textbf { 1 V }$ ，a steep slope occurs because the surface inversion layer in the channel is obtained while the depletion region in the silicon under the gate does not exceed $D$ ，the step width of the heavier doped.im planted region.For $V \_ { s \\mathrm { - s u b } } \\geq 1 ~ \\mathrm { V }$ ，atinversion the depletion region now extends into the lighter doped substrate and the threshold voltage then increases relatively slowly with $V \_ { s - \\mathrm { s u b } }$ \[11\].Thus,with a fixed substrate bias of $- 1 \\mathrm { ~ V ~ }$ , the substrate sensitivity over the operating range of the source voltage (e.g.， ground potential to $4 \\mathrm { ~ V ~ }$ is reasonablylow and very similar to the slope of the nonimplanted 2oo-A design.However, the threshold voltage is significantly higher for the implanted design which allows adequate design margin so that,under worst case conditions (e.g.，short-channel effects which reduce the threshold considerably)，the threshold will still be high enough so that the device can be turned off to a negligible conduction level as required for dynamic memory applications.

Experimental results are also given in Fig.6 from measurements made on relatively long devices (i.e., $L =$ $1 0 ~ \\mu )$ ）which have no short-channel effects.These data agree reasonably well with the calculated curve.A $3 5 \\mathrm { k e V }$ 5 $6 \\times 1 0 ^ { 1 1 }$ atoms/ $\\mathrm { ^ { \\prime } c m ^ { 2 } }$ implant was used to achieve this result,rather than the slightly higher design value of $4 0 { \\mathrm { \ k e V } }$ and $6 . 7 \\times 1 0 ^ { 1 1 }$ atoms/ $\\mathrm { ^ { \\circ } c m ^ { 2 } }$

# TWO-DIMENSIONAL （SHORT CHANNEL）ANALYSIS

For dcvices with sufficiently short-channel lengths,the one-dimensional model is inadequate to account for the threshold voltage lowering due to penetration of the drain field into the channel region normally controlled by the gate. While some models have been developed which account for this behavior\[14\]，the problem is complicated for the ion-implanted structure by the nonuniform doping profile which leads to an electric field pattern that is difficult to approximate. For the ionimplanted case,the two-dimensional numerical current transport model of Kennedy and Mock \[15\]，\[16\] was utilized. The computer program was modified by W. Chang and P.Hwang \[17\] to handle the abrupt substrate doping profiles considered for these devices.

The numerical current transport model was used to calculate the turn-on behavior of the ion-implanted device by a point-by-point computation of the device current for increasing values of gate voltage. Calculated results are shown in Fig.7 for two values of channel length in the range of $1 \ \\mu$ ,aswell as for a relatively longchannel device with $L = 1 0 \ \\mu .$ All cases were normalized to a width-to-length ratio of unity,and a drain voltage of $\\textsuperscript { 4 V }$ was uscd in all cases.As the channel length is reduced to the order of ${ \\mathrm { ~ 1 ~ } } \\mu ,$ the turn-on characteristic shifts to a lower gate voltage due to a lowering of the threshold voltage.The threshold voltage occurs at about $1 0 ^ { - 7 }$ A where the turn-on characteristics make a transition from the exponential subthreshold behavior (a linear response on this semilogarithmic plot） to the $I \_ { d } \ \\propto \ V \_ { g } ^ { \\mathrm { ~ 2 ~ } }$ square-law behavior. This current level can also be identified from Fig.3 as the actual current at the projected threshold voltage, $\\boldsymbol { V } \_ { t }$ .When the computed characteristics were plotted in the manner of Fig.3 they gave $4 \\times 1 0 ^ { - 8 }$ A at threshold for all device lengths.The band bending, $\\psi \_ { s , }$ ，at this threshold condition is approximately $0 . 7 5 { \\mathrm { ~ V ~ } }$ .Some of the other device designs considered with heavier'substrate concentrations gave a higher current at threshold,so,for simplicity,the value of $1 0 ^ { - 7 }$ A wasused in all cases with a resultant small error in $\\boldsymbol { V } \_ { t }$

![](http://stanford.edu/class/cs114/readings/images/f21ae0ce9b14cbcccfbd7931b81f961e713dbb5596dc6ab74a0f6276373c85c8.jpg)

Fig.7.Caluculated and experimental subthreshold turn-on characteristic for basic ion-implanted design for various channel lengths with $V \_ { \\mathrm { s u b } } = - 1 \\mathrm { \\Delta V }$ ， $V \_ { d } = 4 ~ \\mathrm { V }$ ：

![](http://stanford.edu/class/cs114/readings/images/aff2ec777f57a6b8218fb4b90dff484dec29f267aef456f36ee91ceb2fb3d375.jpg)

Fig.8.Experimental and calculated dependence of threshold voltage on channel length for basic ion-implanted design with $V \_ { \\textrm s u b } = - 1 ~ \\mathrm { V }$ 5 $V \_ { d } = 4 ~ \\bar { \\mathrm { V } }$ ，

MOSFET's with various channel.lengths were measuredto test the predictionsof the two-dimensional model. The technique for experimentally determining the channel length for very short devices is described in the Appendix. The experimental results are plotted in Fig.7 and show good agreement with the calculated curves, especially considering the somewhat different values of $L$ Another form of presentation of this data is shown in Fig.8 where the threshold voltage is plotted as a function of channel length. The threshold voltage is essentially constant for $L > 2 \ \\mu$ ，and falls by a reasonably small amount as $L$ is decreased from 2 to $\\textbf { 1 } \_ { \\mu }$ ，and then decreases more rapidly with further reductions in $L$ For circuit applications the nominal value of $L$ could be set somewhat greater than $1 ~ \\mu ~ \\mathrm { { s o } }$ that，over an expected range of deviation of $L$ ，the threshold voltage is reasonablywell controlled.For example, $L = 1 . 3 \\pm 0 . 3 \\mu$ would give $V \_ { t } = 1 . 0 \\pm 0 . 1 \ : \\mathrm { V }$ from chip to chip due to this shortchannel effect alone.This would be tolerable for many circuit applications because of the tracking of different devices on a given chip,if indeed this degree of control of $L$ can be achieved.The experimental drain characteristics for an ion-implanted MOSFET witha $1 . 1 \ – \\mu$ channel length are shown in Fig.9 for the grounded source condition.The general shape of the characteristics is the same as those observed for much larger devices.No extraneous short-channel effects were observed for drain voltages as large as $^ \\textrm { \\scriptsize 4 V }$ .The experimental data in Figs. 6-9 were taken from devices using a $\\mathbf { B ^ { 1 1 } }$ channel implantation energy and dose of $3 5 { \\mathrm { \ k e V } }$ and ${ \\bf 6 . 0 ~ \\times ~ 1 0 ^ { 1 1 } }$ atoms/ $\\mathrm { ^ { c m ^ { 2 } } }$ ,respectively.

![](http://stanford.edu/class/cs114/readings/images/f99a8ecb29fd9eaef7d14f85ab423977c39276386d370e0182d30568da4f3403.jpg)

Fig.9. Experimental drain voltage characteristics for basic ionimplanted design with $V \_ { \\mathbf { s u b } } = - 1 \\mathrm { v }$ $L = 1 . 1 \\mu ,$ and $\\mathtt { W } = 1 2 . 2 \ \\mu$ Curve tracer parameters；load resistance $3 0 ~ \\Omega$ ，drain voltage 4 V,gate voltage $\_ { 0 - 4 \\mathrm { ~ V ~ } }$ in 8 steps each $\\mathbf { 0 . 5 \ V }$ apart.

The two-dimensional simulations were also used to test the sensitivity of the design to various parameters.The results are given in Fig. 1O which tabulates values of threshold voltage as a function of channel length for the indicated voltages.Fig.1O(a）is an idealized representation for the basic design that has been discussed thus far. The first perturbation to the basic design was an increase in junction depth to $0 . 4 ~ \\mu$ .This was found to give an appreciable reduction in threshold voltage for the shorter devices in Fig.1O(b).Viewed another way,the minimum device length would have to be increased by 20 percent (from 1.0 to $1 . 2 \ \\mu$ ）to obtain a threshold comparable to the basic design.This puts the value of the shallower junctions in perspective.Another perturbation from the basic design which was considered was the use of a substrate doping lighter by a factor of 2,with a slightly higher concentration in the surface layer to give the same threshold for a long-channel device \[Fig. 10(c)\]. The results for smaller devices proved to be similar to the caseof deeperjunctions.The next possibledeparture from the basic design is the use of a shallower boron implantation in the channel region，only half as deep，with a heavier concentration to give the same long-channel threshold \[Fig.10(d)\].With the shallower profile,and considering that the boron dose implanted in the silicon is about 20 percent less in this case,it was expected that more short-channel effects would occur.However，the calculated valucs show almost identical thresholds compared to the basic design.With the shallower implantation it is possible to use zero substrate bias and still have good substrate sensitivity since the heavier doped region iscompletely depletedat turn-onwitha grounded source. The last design perturbation considers such a case,again witha heavier concentrationto give thesame long-channel threshold\[Fig.1O(e)l.The calculations for this case show appreciably less short-channel effect.In fact，the threshold for this case for a device with $L = 0 . 8 \ \\mu$ is about the same as for an $L = 1 . 0 ~ \\mu$ deviceof the basic design.This important improvement is apparently due to the reduced depletion layer widths around the source and drain with the lower voltage drop across those junctions.Also，with these bias and doping conditions，the depletion layer depth in the silicon under the gate is much less at threshold,particularly near thc source where only the band bending, $\\psi \_ { s }$ ,appears across this depletion region，which may help prevent the penetration of field lines from the drain into this region where the device turn-on is controlled.\
\
![](http://stanford.edu/class/cs114/readings/images/33e7ea2243472624d02e27a84833f20a6bacf7f9860908d22e18945a679b42f7.jpg)\
\
Fig.10. Threshold voltage calculated using two-dimensional current transport model for various parameter conditions. A fatbandvoltageof $- 1 . 1 \\mathrm { \\Delta V }$ is assumed.\
\
![](http://stanford.edu/class/cs114/readings/images/cbc043592d21bde28a3c1ac14580d564fcf8b26af3f560d25719df60f81bd444.jpg)\
\
Fig.11.Experimental and calculated dependence of threshold voltage on channel length for ion-implanted zero substrate bias design.\
\
# CHARACTERISTICS OF THE ZERO SUBSTRATE BIAS DESIGN\
\
Since the last design shown in Fig.10(e) appears to bebetterbehaved intermsof short-channel effects,itis worthwhile to review its properties more fully.Experimental devices corresponding to this design were built and tested with various channel lengths.In this case a $2 0 { \\mathrm { \ k e V } }$ ， $6 . 0 \\times 1 0 ^ { 1 1 }$ atoms/ $\\bf { c m ^ { 2 } \ B ^ { 1 1 } }$ implant was used to obtain a shallower implanted layer of approximately 1000-A depth \[11\].Data on threshold voltage for these devices with $^ { 4 \\mathrm { ~ V ~ } }$ applied to the drain is presented in Fig. 1l and corresponds very well to the calculated values. Data for a small drain voltage is also given in this figure, showing much less variation of threshold with channel length,as expected.The dependence of threshold voltage on source-to-substrate bias is shown in Fig.12 for different values of $L$ .The drain-to-source voltage was held at a constant low value for this measurement.The results show that the substrate sensitivity is indeed about the same for this design with zero substrate bias as for the original design with $V \_ { \\mathrm { s u b } } = - 1 ~ \\mathrm { T }$ V.Note that the smaller devices show a somewhat flatter substrate sensitivity characteristic with relatively lower thresholds at high values of source (and drain) voltage.\
\
The turn-on characteristics for the zero substrate bias design，both experimental and calculated，are shown in Fig.13 for different values of $L$ . The relatively small shiftin threshold for the short-channel devices is evident; however,the turn-on rate is considerably slower for this case than for the $V \_ { \\mathrm { s u b } } = - 1 ~ \\mathrm { V }$ case shown in Fig.7.This is due to the fact that the depletion region in the silicon under the gate is very shallow for this zero substrate bias case so that a large portion of a given gatevoltage change is dropped across the gate insulator capacitance rather than across the silicon depletion layer capacitance.This is discussed in some detail for these devices in another paper \[11\].The consequence for dynamic memory applications is that,even though the zero substrate bias design offers improved threshold control for strong inversion,this advantage is offset by the flatter subthreshold turn-on characteristic.For such applications the noise margin with the turn-on characteristic of Fig.13 is barely suitable if the device is turned off by bringing its gateto ground.Furthermore，elevated temperatureaggravates the situation \[18\].Thus,for dynamic memory, the basic design with $\\bar { V } \_ { \\mathbf { s u b } } = - 1 \\mathrm { ~ V ~ }$ presented earlier is preferred.\
\
![](http://stanford.edu/class/cs114/readings/images/485dcd98afcebaef37b83b1f72d29b17ddc1d46cffef65006a40b4676dd6464a.jpg)\
\
Fig.12.Substrate sensitivity characteristics for ion-implanted zero substrate bias design with channel length as parameter.\
\
# CIRCUIT PERFORMANCE WITH SCALED-DOWN DEVICES\
\
The performance improvement expected from using very small MOSFET's in integrated circuits of comparably small dimensions is discussed in this section. First,the performance changes due to size reduction alone are obtained from the scaling considerations given earlier. The influence on the circuit performance due to the structural changes of the ion-implanted design is then discussed.\
\
Table Ilists the changes in integrated circuit performance which follow from scaling the circuit dimensions, voltages,and substrate doping in the same manner as the device changes described with respect to Fig. 1. These changes are indicated in terms of the dimensionless scaling factor $\\pmb { \\kappa }$ .Justifying these results here in great detail would be tedious,so only a simplified treatment is given. It is argued that all nodal voltages are reduced in the miniaturized circuits in proportion to the reduced supply voltages.This follows because the quiescent voltage levels in digital MOSFET circuits are either the supply levels or some intermediate level given by a voltage divider consisting of two or more devices,and because the resistance $V / I$ of each device is unchanged by scaling. An assumption is made that parasitic resistance elements are either negligible or unchanged by scaling,which will be examined subsequently.The circuits operate properly at lower voltages because the device threshold voltage $\\boldsymbol { V } \_ { t }$ scales as shown in (2)，and furthermore because the tolerance spreads on $\\boldsymbol { V } \_ { t }$ should be proportionately reduced aswell if each parameter in (2） is controlled to the same percentage accuracy.Noise margins are reduced,but at the same time internally generated noise coupling voltages are reduced by the lower signal voltage swings.\
\
![](http://stanford.edu/class/cs114/readings/images/f1c7e0f6fcd763f3d01a8e38b94612b0e7e2b0d1af87074bdb932cb23d683a52.jpg)\
\
Fig.13．Calculated and experimental subthreshold turn-on characteristics for ion-implanted zero substrate bias design.\
\
TABLE I SCALING RESULTS FOR CIRCUIT PERFORMANCE\
\
|     |     |\
| --- | --- |\
| Device or Circuit Parameter | Scaling Factor |\
| Device dimension tox,L,W | 1/k |\
| Doping concentration Na | K |\
| Voltage V | 1/k |\
| Current I Capacitance eA/t | 1/k |\
| Delay time/circuit VC/I | 1/k 1/k |\
| Power dissipation/circuit VI | 1/k2 |\
| PowerdensityVI/A | 1 |\
|  |  |\
\
Due to the reduction in dimensions,all circuit elements (i.e.,interconnection lines as well as devices) will have their capacitances reduced by a factor of $\\pmb { \\kappa }$ .This occurs because of the reduction by $\\kappa ^ { 2 }$ in the area of these components,which is partially cancelled by the decrease in the electrode spacing by $\\pmb { \\kappa }$ due to thinner insulating films and reduced depletion layer widths. These reduced capacitances are driven by the unchanged device resistances $V / I$ giving decreased transition times with a resultant reduction in the delay time of each circuit by $\\mathfrak { a }$ factor of $\\pmb { \\kappa }$ .The power dissipation of each circuit is reduced by $\\kappa ^ { 2 }$ due to the reduced voltage and current levels, so the power-delay product is improved by $\\kappa ^ { 3 }$ .Since the area of a given device or circuit is also reduced by $\\kappa ^ { 2 }$ the power density remains constant. Thus,even if many more circuits are placed on a given integrated circuit chip,the cooling problem is essentially unchanged.\
\
TABLE II SCALING RESULTS FOR INTERCONNECTION LINES\
\
|     |     |\
| --- | --- |\
| Parameter | Scaling Factor |\
| Line resistance,RL = pL/Wt | K |\
| Normalized voltage drop IRL/V | K |\
| Line response time RLC | 1 |\
| Line current density I/A | K |\
\
As indicated in Table II,a number of problems arise from the fact that the cross-sectional area of conductors is decreased by $\\kappa ^ { 2 }$ while the length is decreased only by $\\kappa$ It is assumed here that the thicknesses of the conductors are necessarily reduced along with the widths because of the more stringent resolution requirements (e.g.,on etching,etc.).The conductivity is considered to remain constant which is reasonable for metal films down to very small dimensions (until the mean free path becomes comparable to the thickness)，and is also reasonable for degenerately doped semiconducting lines where solid solubility and impurity scattering considerations limit any increase in conductivity.Under these assumptions the resistance of a given line increases directly with the scaling factor $\\kappa$ 、TheIRdrop in sucha line is therefore constant (with the decreased current levels)，but is $\\pmb { \\kappa }$ times greater in comparison to the lower operating voltages.The response time of an unterminated transmission line is characteristically limited by its time constant $\\dot { R \_ { L } C }$ ,which is unchanged by scaling;however,this makes it difficult to take advantage of the higher switching speeds inherent in the scaled-down devices when signal propagation over long lines is involved.Also,the current density in a scaled-down conductor is increased by κ, which causes a reliability concern．In conventional MOSFET circuits,these conductivity problems are relatively minor，but they become significant for linewidths of micron dimensions.The problems may be circumvented in high performance circuits by widening the power buses and by avoiding the use of $\\mathfrak { n } ^ { + }$ doped lines for signal propagation.\
\
Use of the ion-implanted devices considered in this paper will give similar performance improvement to that of the scaled-down device with $\\kappa = 5$ given in TableI. For the implanted devices with the higher operating yoltages(4V instead of $\_ { 3 \\mathrm { ~ V ~ } }$ ）and higherthreshold voltages （ $0 . 9 \\mathrm { ~ V ~ }$ instead of $\\mathbf { 0 . 4 V } ,$ ,thecurrent level willbereduced in proportion to $( V \_ { g } - V \_ { t } ) ^ { 2 } / t \_ { \\mathrm { o x } }$ to about 80 percent of the current in the scaled-down device.The power dissipation per circuit is thus about the same in both cases.All device capacitances are about a factor of two less in the implanted devices,and $\\mathbf { n } ^ { + }$ interconnection lines will show the same improvement due to the lighter substrate doping and decreased junction depth.Some capacitance elements such as metal interconnection lines would be essentially unchanged so that the overall capacitance improvement in a typical circuit would be somewhat less than a factor of two.The delay time per circuit which is proportional to VC/I thus appears to be about the same for the implanted and for the directly scaled-down micron devices shown in Fig.4.\
\
# SUMMARY\
\
This paper has considered the design,fabrication,and characterization of very small MOSFET switching devices. These considerations are applicable to highly miniaturized integrated circuits fabricated by high-resolution lithographic techniques such as electron-beam pattern writing.A consistent set of scaling relationships were presented that show how a conventional device can be reduced in size；however, this direct scaling approach leads to some challenging technological requirements such as very thin gate insulators.It was then shown how an all ion-implanted structure can be used to overcome these diffculties without sacrificing device area or performance.A two-dimensional current transport model modified for use with ion-implanted structures proved particularly valuable in predicting the relative degree of short-channel effects arising from different device parameter combinations.The general objective of the study was to design an n-channel polysilicon-gate MOSFET with a $1 \_ { - \\mu }$ channel length for high-density source-follower circuits such as those used in dynamic memories. The most satisfactory combination of subthreshold turnon range,threshold control,and substrate sensitivity was achieved by an experimental MOSFET that used a 35 keV, $6 . 0 \\times 1 0 ^ { 1 1 }$ atoms/cm² $\\mathrm { \\dot { B } } ^ { 1 1 }$ channel implant,a 100 keV, $4 ~ \\times ~ 1 0 ^ { 1 5 }$ atoms/ $\\mathrm { c m ^ { 2 } }$ （ $\\mathrm { A s ^ { 7 5 } }$ source/drain implant,a $3 5 0 – \\mathring { \\mathbf { A } }$ gate insulator,and an applied substrate bias of $- 1 \\mathrm { ~ V ~ }$ .Also presented was an ion-implanted design intended for zero substrate bias that is more attractive from the point of view of threshold control but suffers from an increased subthreshold turn-on range.Finally the sizable performance improvement expected from using very small MOSFET's in integrated circuits of comparably small dimensions was projected.\
\
# APPENDIX\
\
# EXPERIMENTAL DETERMINATION OF CHANNEL LENGTH\
\
A technique for determining the effective electrical channel length $\\dot { L }$ for very small MOSFET's from experimental data is described here.The technique is based\
\
![](http://stanford.edu/class/cs114/readings/images/0e147af34322d61b3ddcf285ec5723cc01cef465abb65cc6a5b132519e762060.jpg)\
\
Fig.14.Illustration of experimental technique used to determine channel length, $L$\
\
on the observation that\
\
$$\
W R \_ { \\mathrm { { c h a n } } } = L \\rho \_ { \\mathrm { { c h a n } } }\
$$\
\
where $R \_ { \\mathrm { e h a n } }$ is the channel resistance,and $\\rho \_ { \\mathrm { c h a n } }$ the sheet resistance of the channel.For a fixed value of $V \_ { g } \\mathrm { ~ - ~ } V \_ { t } >$ O,and with the device turned on in the below-pinchoff region，the channel sheet resistance is relatively independent of $L$ .Then,a plot of $W R \_ { \\mathrm { c h a n } }$ versus $L \_ { \\mathrm { m a s k } }$ will intercept the $L \_ { \\mathrm { m a s k } }$ axis at $\\Delta L$ because $\\Delta L = L \_ { \\mathrm { m a s k } } - L$ where $\\varDelta L$ is the processing reduction in the mask dimension due to exposure and etching. An example of this technique is illustrated in Fig.14.\
\
The experimental values of $W$ and $R \_ { \\mathrm { c h a n } }$ used in Fig. 14were obtained as follows.First，the sheet resistance of the ion-implanted $\\boldsymbol { \\mathrm { n ^ { \* } } }$ region was determined using a relatively large four-point probe structure.Knowing the $\\mathrm { n ^ { + } }$ sheet resistance allows us to compute the source and drain resistance $R \_ { s }$ and $\\textstyle R \_ { d }$ ，and to deduce $W$ from the resistance of a long,slender, $\\mathrm { \\Omega \_ { n } } ^ { + }$ line.The channel resistance can be calculated from\
\
$$\
R \_ { \\mathrm { e h a n } } = V \_ { \\mathrm { c h a n } } / I \_ { d } = ( V \_ { d } - I \_ { d } ( R \_ { s } + R \_ { d } + 2 R \_ { c } + R \_ { \\mathrm { l o a d } } ) ) / I \_ { d } ,\
$$\
\
where $\\scriptstyle { R \_ { c } } $ is the contact resistance of the source or drain, and $R \_ { \\mathrm { l o a d } }$ is the load resistance of the measurement circuit. ${ { I } \_ { d } }$ was determined at $V \_ { g } = V \_ { t } + 0 . 5 \ : \\mathrm { V }$ with a small applied drain voltage of 50 or $1 0 0 ~ \\mathrm { m V }$ .The procedure is more simple and accurate if one uses $\\mathfrak { a }$ set of MOSFET's having different values of $L \_ { \\mathrm { m a s k } }$ but all with the same value of $W \_ { \\mathrm { m a s k } }$ .Then one needs only to plot $R \_ { \\mathrm { c h a n } }$ versus $L \_ { \\mathrm { m a s k } }$ in order to determine $\\Delta L$\
\
DENNARD et al.:ION-IMPLANTED MOSFET'S\
\
# ACKNOWLEDGMENT\
\
We wish to acknowledge the valuable contributions of B.L.Crowder and F.F.Morehead who provided the ion implantations and related design information.Also important were the contributions of P.Hwang and W. Chang to two-dimensional device computations. J. J. Walker and V.DiLonardo assisted with the mask preparation and testing activities. The devices were fabricated by the staff of the silicon technology facility at the T.J.Watson Research Center.\
\
# REFERENCES\
\
\[1\] F. Fang, M. Hatzakis,and C. H. Ting,“Electron-beam fabri cationof ionimplanted high-performance FETcircuits, J.Vac.Sci.echnol.,l.10,p.9.\
\
\[2\] J.M. Pankrantz, H. T. Yuan,and L. T.Creagh,“A high. gain,low-noisetransistor fabricated with electron beam lithography,in Tech.Dig. Int.Electron Devices Meeting. Dec.1973,pp.44-46.\
\
\[3\] H. N. Yu, R.H. Dennard, T. H.P.Chang, and M. Hatzakis “Anexperimental high-densitymemoryarryfabricated with electronbeam,inICC Dig.Tech.Papers,Feb.1973. pp.98-99.\
\
\[4\] R.C.Henderson,R.F.W. Pease,A. M. Voshchenkow,P. Mallery，and R.L. Wadsack,“A high speed p-channel randomaccess1024-bit memory made with electron lithography,"in Tech.Dig. Int.Electron Devices Meeting,Dec. 1973, pp.138-140.\
\
\[5l D.L. Spears and H.I. Smith,“X-Ray lithography-a new high resolution replication process,”Solid State Technol., vol.15,p.21,1972.\
\
\[6\] S.Middlehoek,“Projection masking,thin photoresist layers and interference effcts,”IBM J.Res.Develop., vol.14,p. 117, 1970.\
\
\[7\] R.H. Dennard, F.H. Gaensen,L. Kuhn, and H. N. Yu, “Design of micron MOS switching devices," presented at the IEEE Int.Electron Devices Meeting， Washington, D.C., Dec.1972.\
\
\[8\] A.N. Broers and R. H. Dennard,“Impact of electron beam technology on silicon device fabrication, Semicond.Silicon (Electrochem. Soc.Publication),H.R. Huff and R.R.Burgess,eds.，pp.830-841,1973.\
\
\[9\] D.L. Critchlow,R.H. Dennard,and S.E.Schuster,“Design characteristics of n-channel insulated-gate field-effect transistors,"IBJ.Res.Develop.,vol.17,p.430,197.\
\
\[10\] R.M. Swanson and J.D. Meindl,“Ion-implanted complementary MOS transistors in low-voltage circuits,”IEEE J. Sold-State Circuits，vol. SC-7,pp.146-153,April 1972.\
\
\[11\]V.L.Rideout,F.H. Gaensslen,and A.LeBlanc,“Device designconsiderations for ion implanted n-channel MOSFET's,"IBM J.Res.Develop., to be published.\
\
\[12\] F.F. Fang and A.B. Fowler,“Transport properties of electronsin inverted Si surfaces,Phys.Rev.vol.169,p.619, 1968.\
\
\[13\] W.S. Johnson,IBM System Products Division,E.Fishkill, N. Y., private communication.\
\
\[14\] H.S.Lee,“An\_analysis of the threshold voltage for short chanmel IGFET's,”Solid-State Electron.， vol.16,p.1407, 1973.\
\
\[15\] D. P. Kennedy. and P.C. Murley,“Steady state mathematical theory for the insulated gate field effeet transistor,” IBMJ.Res.Develop.,vol.17,p.1,73.\
\
16\] M.S.Mock,“A two-dimensional mathematical modelof the insulated-gate field-effect transistor,”Solid-State Electron.,vol.16,p.601,1973.\
\
17\] W. Chang and P.Hwang, IBM System Products Division, Essex Junction,Vt., private communication.

18l R.R.Troutman, “Subthreshold design considerations for insulated gate field-effect transistors,”IEEE J.Solid-State Circuits,vol.SC-9,p.55,April1974.

![](http://stanford.edu/class/cs114/readings/images/579b5f65d824d029ee481569d3fa843e53a150c6e60492f82e6715b7ed1695ad.jpg)

Robert H. Dennard （M'65）was born in Terrell,Tex.,in 1932.He received the B.S. and M.S.degrees in electrical.engineering from Southern Methodist University,Dallas,Tex.,in 1954 and 1956,respectively,and the Ph.D.degree from Carnegie Institute of Technology,Pittsburgh, $\\mathrm { P a . , }$ in 1958.

In 1958 he joined the IBM Research Division where his experience included study of.new devices and circuits for logic and memory applications,and development of advanced data communication techniques. Since 1963 he has been at the IBM T.J.Watson Research Center，Yorktown Heights, N.Y.,where he worked with a group exploring large-scale integration (LSI),while making contributions in cost and yield models, MOSFET device and integrated circuit design,and FET memory cells and organizations.Since I971 he has been manager of a group which is exploring high density digital integrated circuits using advanced technology concepts such as electron beam pattern exposure.

Fritz H.Gaensslen was born in Tuebingen, Germany,on October 4,193i.He received the Dipl.Ing and Dr.Ing. degrees in electrical.engineering from the Technical University of Munich，Munich,Germany，in 1959 and 1966,respectively.

![](http://stanford.edu/class/cs114/readings/images/7074f0540ec927954cf12787507e66402641011a65f6fe350be21df52af12280.jpg)

Prior to 1966 he served as Assistant Professor in the Department of Electrical Engineering,Technical University of Munich, Munich，Germany.During this period he was working on the synthesis of linear and digital networks.In 1966 he joined the IBM T.J.Watson Research Center,Yorktown Heights,N.Y.,where he is currently a member of a semiconductor device and process design group. His current technical interests involve various aspects of advanced integrated circuits like miniaturization，device simulation，and ion implantation.From September 1973 he was on a one year assignment at the IBM Laboratory,Boeblingen,Germany.

Dr.Gaensslen is a member of the Nachrichtentechnische Gesellschaft.

Hwa-Nien Yu(M'65) was born in Shanghai China,on January 17,i929.He received the B.S.,M.S.,and Ph.D. degrees in electrical engineering from the University of Illinois, Urbana,in1953,1954,and1958,respectively.

While.at the University,he was a Research Assistant in the Digital Computer Laboratory and worked on the design of the Illiac-II computer. Since joining the IBM Research Laboratory in 1957,he has been engaged in various exploratory solid-state device research activities.After working with the Advanced Systems Development Division from 1959 to 1962,he rejoined the Research Division in i962 to work on the ultra-high speed germenium device technology.Since 1967,he has been engaged in advanced silicon LSI device technology research.He is currently the Manager of Semiconductor Technology at the IBM T.J. Watson Research Center,Yorktown Heights,N.Y.

![](http://stanford.edu/class/cs114/readings/images/8b545a651af5865690bf9e6c980b28fd97d2a86f4023942aec36317667d13a53.jpg)

Dr.Yu is a member of Sigma Xi.

![](http://stanford.edu/class/cs114/readings/images/a055add326c4d5457e7945fbd00697a66f2a39e41875368997a2003b5163e121.jpg)

V.Leo Rideout (S'61-M65)was born in N.J.in 1941.He received the B.S.E.E.degree with honors in 1963 from the University of Wisconsin，Madison，the M.S.E.E. degree in 1964 from Stanford University, Stanford，Calif.,and the Ph.D，degree in materials science in 1970 from the University of Southern California (U.S.C.)，Los Angeles.His thesis work at U.S.C.under Prof.C.R.Crowell concerned thermally assisted current transport in platinum silicide Schottky barriers.

From 1963 to 1965 he wasa member of the technical staff of Bell Telephone Laboratories where he worked on high-frequency germanium transistors and.metal-semiconductor Schottky barriers on potassium tantalate.In 1966 he spent a year as a Research Assistant in the department of Materials Science at the Technological University of.Eindhoven,Eindhoven,The Netherlands, studying acoustoelectric effects in cadmium .sulphide.In I970 he joined IBM Research in:the device research group of Dr.L.Esaki where he worked on'fabrication and contact technology for multiheterojunction “superlattice” structuresusing gallium-arsenidephosphide and gallium-aluminum-arsenide.Since 1972 he has been a member of the semiconductor device and circuit design group of Dr.R.Dennard at .the IBM T.J.Watson Research Center, Yorktown Heights,N.Y.His present research interests concern high density silicon FET technology.He is the author or co-author of 20 technical papers and3U.S.Patents.

Dr.Rideout is a member of the Electrochemical Society,Tau Beta Pi,Eta Kappa Nu,Phi Kappa Phi,and Sigma Xi.

Ernest Bassous was born in Alexandria, Egypt, on September 1, 1931.He received the B.Sc.degree in chemistry from the University of London，London，England in 1953，and.the M.S. degree in physical. chemistry from the Polytechnic Institute of Brooklyn，Brooklyn，N.Y.in 1965.

From 1954 to 1959 he taught Chemistry and Physics at the British Boys' School,Alexandria,Egypt.He went to France in

![](http://stanford.edu/class/cs114/readings/images/ca88d69b07361323c603f005c467d504ae0e7305315f6e0162b1074499ca5c4d.jpg)

1959 where he worked for 1 year on infra red detectors at the Centre National d'Etudes des Telecommunications,Issy-lesMoulineaux,Seine.From 1960 to 1964 he worked at the Thomas A.Edison Research Laboratory in West Orange，N.J.,where his activities included studies in arc discharge phenomena,ultra violet absorption spectroscopy，and organic·semiconductors. In 1964 he joined the IBM Research Laboratory，Yorktown Heights,N.Y.,to work on semiconductors.As a member of the Research staff he is presently engaged in·the study of materials and processes used in the fabrication of silicon integrated circuits.

Mr.Bassous is a member of the Electrochemical Society and the American Association for the Advancement of Science.

![](http://stanford.edu/class/cs114/readings/images/5aa079cc87d8fa39059fa86ab17e52a2195878807705cf1ae5282f5a6234ee9f.jpg)

AndreR.LeBlanc(M'74) received the B.S. degree in electrical engineering，andthe M.S.degree in physics from the University of Vermont,Burlington,in 1956 and 1959, respectively,and.the D.Sc.degree in electrical engineering from .the University of New Mexico,Albuquerque,in 1962.

Prior to joining IBM，Essex.Junction, Vt.,in 1957,he was affiliated with G.E.as an electrical engineer and also with Sandia Corporation in conjunction with the University.of New Mexico.In 1959 he took an educational leave of absence to complete his doctorate.He is presentlya member of the Exploratory Memory Group at the IBM Laboratory,Essex Junction,where his current technical interest includes a study of short-channel ·MOSFET devices.He has authored five publications and twelve papers,as well as several IBM Technical Reports.

Dr.LeBlanc is a member of Sigma Xi and Tau Beta Pi.