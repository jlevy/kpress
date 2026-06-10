---
title: A Comparative Analysis of Unladen Airspeed Velocity in Avian Species, with Emphasis on Swallows and Martins
description: A long-form academic test document — footnotes, tables, and deep heading structure — for exercising KPress layout, TOC, footnotes, and reading flow at length.
author: KPress e2e
---
# A Comparative Analysis of Unladen Airspeed Velocity in Avian Species, with Emphasis on Swallows and Martins

## I. Introduction: Understanding Avian Airspeed Velocity

Airspeed, the velocity of a bird relative to the airmass through which it moves, is a
fundamental parameter in ornithology.
It critically influences energetic expenditure during flight, the efficiency of foraging
strategies, the success and routing of migratory journeys, outcomes of predator-prey
dynamics, and a species’ overall capacity to exploit diverse ecological niches.[^4]
Consequently, a comprehensive understanding of the range of airspeeds employed by
different avian taxa, and the multifaceted factors that determine these speeds, is
indispensable for robust ecological, physiological, and biomechanical investigations.
The predominant focus in ornithological literature on *cruising flight speed* indicates
a scientific consensus that this metric offers the most ecologically relevant and sturdy
basis for inter-species comparisons of typical flight performance.
This emphasis likely stems from the fact that cruising speeds are sustained over
significant durations, particularly during migration and extended foraging bouts, making
them more representative of average energy budgets and movement patterns than
specialized or burst speeds, although extreme records like dive speeds hold their own
distinct significance.[^7]

This technical report is dedicated to an analysis of *unladen airspeed*. This term
refers to a bird’s speed relative to the surrounding air under conditions where it is
not encumbered by external loads, such as prey items or substantial nesting materials,
which are known to significantly alter flight performance and increase energetic
demands. While internal loads, such as subcutaneous fat reserves accumulated for
migration, inherently affect a bird’s body mass and thus its flight dynamics, the term
“unladen” in this context primarily serves to distinguish from flight burdened by
externally carried objects.
It is crucial to differentiate between a bird’s airspeed and its groundspeed (velocity
relative to the Earth’s surface).
These two metrics can differ substantially due to the influence of wind, a factor of
paramount importance in studies of avian migration where wind conditions are a
significant and highly variable environmental parameter.[^7] Many studies, particularly
those employing radar, directly measure groundspeed and subsequently derive airspeed by
vectorially subtracting the wind velocity at the bird’s flight altitude, underscoring
the potential for a bird’s propulsive effort to be decoupled from its actual progress
over the ground.[^7]

The principal objective of this report is to provide ornithologists with a concise yet
detailed comparative analysis of unladen airspeed velocity across a spectrum of
well-documented avian species.
A particular focus will be directed towards the Hirundinidae family—swallows and
martins—given their highly aerial lifestyles and sophisticated flight capabilities.
This document will critically review the extant literature concerning the methodologies
employed for airspeed measurement, explore the fundamental aerodynamic principles that
govern avian flight speed, and delineate areas where scientific understanding is
well-established alongside those characterized by ongoing research and inherent
uncertainties. Furthermore, it will synthesize available data to identify the fastest,
slowest, and typical airspeeds documented for various species.
In adherence to rigorous scientific practice, all quantitative information presented
herein will be meticulously attributed to its original source through footnotes.

## II. Methodologies for Measuring Unladen Airspeed in Birds

The endeavor to accurately quantify avian airspeed has witnessed a significant evolution
in methodologies, progressing from early, often qualitative, observational estimations
and rudimentary techniques, such as vehicle-based pursuits,[^10] to the contemporary
application of sophisticated remote sensing technologies and direct tracking devices.
Each method presents a distinct array of advantages and inherent limitations, and its
appropriateness is frequently dictated by the specific research question, the target
species, and the environmental context of the study.
A persistent challenge, particularly for remote sensing techniques applied to nocturnal
migrants, is the precise and reliable identification of the species being tracked.[^13]
This methodological landscape reveals a clear trade-off: large-scale techniques like
weather radar are invaluable for characterizing broad migratory movements and estimating
groundspeeds over extensive geographical areas,[^15] while fine-scale methods such as
wind tunnel experiments or ornithodolite observations yield highly precise airspeed and
kinematic data for individual birds, often under controlled conditions.[^17] A
comprehensive understanding of avian flight often necessitates the integration of data
derived from multiple methodologies.

### 2.1 Radar Ornithology

Radar systems have become indispensable tools in ornithology for monitoring bird
movements, especially during migration.

**Weather Surveillance Radar (WSR):** Systems like the WSR-88D, as well as C-band and
S-band radars, are increasingly employed for large-scale, synoptic monitoring of avian
migration and other aerial movements of biological targets.
These radars provide data on the direction, groundspeed (from which airspeed can be
derived if concurrent wind data are available), altitude, and relative density of these
targets.[^13] Their primary application lies in studying the broad spatial-temporal
dynamics of migration, particularly nocturnal movements, and quantifying the biomass of
organisms aloft.[^15]

A significant operational challenge in interpreting WSR data for ornithological studies
is the effective discrimination between birds and insects, as these taxa frequently
co-occur in the airspace and can produce overlapping radar signals.[^15] Several
analytical approaches have been developed to address this bird-insect separation
problem:

* *Fixed Airspeed Thresholds:* A common, albeit often criticized, method involves
  applying a fixed self-powered airspeed threshold, frequently cited as 5 m s–1. Targets
  detected flying below this speed are presumptively classified as insects.[^15] This
  approach is acknowledged as potentially crude, as it can lead to misclassification
  (e.g., fast-flying insects or slow-flying birds) and a consequent loss of valuable
  biological data.[^15]

* *Radial Velocity Variability:* Migrating birds generally exhibit greater spatial
  variability in their radial velocities (often characterized by a standard deviation
  exceeding 2 m s–1) compared to insects, which may be more passively transported by
  wind currents.[^15] This technique, measuring the “texture” of the velocity field, has
  shown promise, particularly with C-band radars.
  However, its efficacy with S-band systems or in scenarios with mixed biological
  targets of comparable magnitudes requires further validation.[^15]

* *Advanced Analytical Methods:* More recent and sophisticated approaches aim to
  partition vertical profiles of biological reflectivity into distinct bird and insect
  components. These methods employ minimal, yet biologically informed, assumptions
  regarding the respective airspeeds and flight behaviors of the two taxa, thereby
  seeking to retain more of the spatial-temporal complexity inherent in the data.[^15]

The persistent challenge of achieving accurate species identification in remote sensing
data, especially for nocturnal migrants detected by radar,[^13] acts as a significant
constraint in ornithological studies.
This limitation has been a catalyst for the development of multi-modal approaches, such
as combining radar with complementary acoustic data from nocturnal flight call
monitoring,[^16] and for the refinement of analytical techniques for signal processing
and target classification.[^15] Without reliable species identification, airspeed data
obtained from such targets may only be categorized broadly (e.g., “small passerine-sized
bird”), which limits its utility in precise comparative analyses or detailed ecological
modeling.

**Tracking Radar:** Specialized radar systems, such as the SPANDAR and FPS-16, possess
the capability to lock onto and follow individual birds or flocks over considerable
distances. These systems record detailed parameters including range, elevation, and
bearing to the target, as well as characteristics of the radar signature (e.g.,
Automatic Gain Control voltage fluctuations), which can be utilized to reconstruct
flight paths and determine speeds with high precision.[^7] Accurate airspeed
determination using tracking radar necessitates careful selection of flight tracks
(ideally, straight and level flight segments) and meticulous correction for wind
velocity at the bird’s flight altitude, typically measured by concurrently tracking
meteorological balloons.[^7] However, the radar signature of a bird can exhibit
significant variability due to changes in its orientation relative to the radar beam
(aspect angle) and alterations in its wing-beat pattern and frequency.
This variability can complicate consistent tracking and, crucially, species
identification based on the signature alone.[^13]

**Doppler Radar (Short-Range):** Portable Doppler radar units can be effectively
employed for short-range airspeed measurements.
These devices provide direct readings of a target’s ground speed.
Airspeed is then calculated by correcting for local wind conditions, typically measured
simultaneously.[^21] For instance, Schnell (1978) utilized a portable Doppler radar unit
(FTB-X(1)) to measure the ground speeds of various bird species flying at relatively
close ranges (25 to 120 yards) and low altitudes (not exceeding 20 yards above the
ground).
Wind speeds were concurrently measured with a hand-held anemometer to facilitate
the calculation of airspeed.[^21]

### 2.2 Wind Tunnel Experiments

Wind tunnels provide a highly controlled laboratory environment for investigating avian
flight performance, including parameters such as power consumption, detailed wing and
body kinematics, and aerodynamic force production, across a precisely manipulated range
of airspeeds.[^3] In a typical wind tunnel experiment, birds are trained to fly steadily
within the tunnel’s test section, where the airflow is maintained at a uniform and known
velocity. Flight behavior is often recorded using synchronized high-speed video cameras,
and energetic costs can be quantified using respirometry techniques, such as doubly
labeled water validation studies or direct mask respirometry during flight.[^4]

Despite the precision afforded by wind tunnels, a persistent concern in the field is the
extent to which flight behavior observed in such an artificial and confined environment
accurately reflects natural, free-flight dynamics.
Stress induced by the experimental conditions can potentially alter a bird’s behavior
and physiology.[^4] Furthermore, extrapolating findings from one species to another, or
from controlled wind tunnel conditions to the complexities of flight in the wild, must
be approached with caution.[^4] The physical dimensions of the wind tunnel can also
impose constraints on the natural flight styles of larger bird species or those that
characteristically employ wide-ranging aerial maneuvers.

### 2.3 Direct Observation and Timing

**Historical Approaches:** Early attempts to quantify bird flight speeds often relied on
direct observation. This included timing individuals as they traversed known distances,
sometimes using stopwatches in conjunction with theodolites for angular measurements to
estimate altitude and range.
More rudimentary methods involved “chasing” birds with automobiles and noting
speedometer readings.[^10] While these methods were foundational in the study of bird
flight, they are now generally considered to possess questionable accuracy and precision
by contemporary ornithological standards, primarily due to difficulties in maintaining
consistent observation, accounting for wind, and the parallax errors inherent in visual
estimation.[^10]

**Ornithodolite:** The modern ornithodolite represents a significant advancement in
observational techniques.
Instruments such as the Vectronix Vector 21 Aero integrate a laser rangefinder with an
electronic compass and inclinometer.
This combination allows for precise measurements of angles (azimuth and elevation) and
distances to a target bird.
From these data, the bird’s three-dimensional position can be calculated over time, and
subsequently, its ground speed vector can be determined.
When used in conjunction with an anemometer to accurately measure wind speed and
direction at the bird’s flight altitude, reliable airspeed can be derived.[^18]
Pennycuick et al. (2013) effectively employed an ornithodolite to measure the airspeeds
of various migrating bird species, demonstrating its utility in field settings.[^18]

### 2.4 Telemetry and Biologging

The development of miniaturized electronic tags has revolutionized the study of animal
movement, including avian flight.

**GPS (Global Positioning System) Tracking:** GPS loggers attached to birds can provide
highly accurate geographical location data (latitude, longitude, and often altitude) at
frequent intervals. From these sequential positional data, groundspeed and detailed
flight paths can be precisely calculated.
Airspeed can then be derived if concurrent, altitude-specific wind data are available
from meteorological sources (e.g., weather balloons, atmospheric models) or co-deployed
sensors.[^24] While some studies mention the use of GPS tracking for species like the
Purple Martin, their primary focus was often on migratory strategies or habitat use
rather than providing direct, instantaneous airspeed data.[^24]

**Geolocators (Light-Level Loggers):** These small, lightweight devices record ambient
light levels, allowing for the estimation of a bird’s geographical position based on day
length (for latitude) and the time of solar noon (for longitude).
Geolocators are primarily used for tracking long-distance movements, particularly entire
migratory routes and identifying key stopover locations.[^26] While average travel rates
(groundspeed over extended periods, often days or weeks) can be calculated from
geolocator data, these devices do not typically provide the high-resolution,
instantaneous airspeed data necessary for detailed aerodynamic analysis or fine-scale
behavioral studies.

**Nocturnal Flight Call (NFC) Monitoring:** This acoustic technique is employed to
monitor avian movements during nocturnal migration by identifying species-specific
flight calls.[^16] While NFC data primarily provide information on species presence,
relative abundance, and the timing of migration, they can be powerfully correlated with
data from other sensors, such as radar, which directly measure parameters like speed and
altitude.[^16] Thus, NFC serves as a valuable complementary tool for species
identification and activity patterns, rather than a direct method for airspeed
measurement.

The operational definition and measurement of “unladen” airspeed present inherent
nuances. While the intention is to measure speed without the influence of external loads
like prey, internal factors such as a bird’s fuel load (i.e., fat reserves accumulated
for migration) can significantly alter body mass and, consequently, flight dynamics and
energetic costs. This internal “laden” state is not always explicitly controlled for or
reported in field studies of migrating birds.
For example, studies measuring the airspeeds of migrating birds are observing
individuals that are, by necessity, internally laden with varying amounts of fuel.[^7]
This implies that “unladen airspeed” is a relative term, and its precise meaning can
vary depending on the study’s context (e.g., a foraging bird versus a migrating bird).
This distinction is important when comparing airspeed data across different studies and
behavioral contexts.

### 2.5 Illustrative Challenges from Controlled Environments (Poultry Housing)

Although not directly pertaining to wild bird research, studies conducted in commercial
poultry houses offer pertinent insights into the complexities of airspeed measurement
and its inherent variability.
Research has demonstrated a high degree of airspeed variation across the cross-section
of a tunnel-ventilated poultry house.
This variability is influenced by numerous factors, including the smoothness of the
interior walls, the number and operational status of ventilation fans, and even the
presence, size, and density of the birds themselves.[^29] Specifically, accurately
measuring airspeed at “bird level” (i.e., near the floor where the birds reside) proves
exceptionally difficult due to the high turbulence and significant spatial and temporal
variability in airflow patterns in this region.[^29] This example from a highly managed
environment underscores the general principle that micro-environmental factors can
substantially impact local air movement.
It highlights the challenge of obtaining a single, representative airspeed value even in
ostensibly controlled settings, a difficulty that is considerably magnified in the
dynamic and complex atmospheric conditions encountered by free-flying wild birds.

The historical trajectory of airspeed measurement techniques clearly reflects a
continuous scientific endeavor towards greater accuracy, reduced invasiveness, and the
capacity to study birds in more natural and ecologically relevant contexts.
This evolution has progressed from potentially biased early methods, such as
car-chasing,[^10] to less intrusive remote sensing technologies and highly precise
laboratory setups, culminating in the current era of sophisticated biologging.

## III. Aerodynamic Principles Governing Avian Airspeed

Avian flight is a complex phenomenon governed by the interplay of aerodynamic forces and
the bird’s ability to generate power and modulate its morphology and kinematics.
The power required to sustain flight (P) is intrinsically linked to the bird’s airspeed
(V), a relationship often depicted as a "power curve."[^4] This relationship is
fundamental to understanding flight strategies, as the total metabolic power consumption
during steady flapping flight can be substantial, ranging from 10 to as much as 20 times
the bird’s basal metabolic rate.[^4]

### 3.1 The Power Curve (P(V) function) – Theoretical Ideals and Empirical Realities

Classical aerodynamic theory generally predicts a U-shaped relationship between the
mechanical power output required for flight and the airspeed of a flying animal.[^5]
This U-shaped curve is significant because it implies the existence of two
characteristic speeds: a speed of minimum power (V&lt;sub>mp&lt;/sub>), at which the
energy expenditure per unit time is lowest, and a typically faster maximum range speed
(V&lt;sub>mr&lt;/sub>), at which the energy cost per unit distance traveled is
minimized.[^5] These speeds are theoretically optimal for different flight objectives,
such as endurance versus long-distance travel.

However, despite the analytical appeal of the U-shaped power curve, its empirical
validation across a wide range of bird species and flight conditions has proven
surprisingly challenging.[^4] Experimental studies have yielded varied results.
Some investigations have confirmed U-shaped power-speed relationships, for example, in
Cockatiels (*Nymphicus hollandicus*).[^8] Conversely, other studies have reported weakly
U-shaped, J-shaped (where power decreases to a minimum and then rises), L-shaped (where
power continuously decreases with speed), or even relatively flat power curves for
certain species or within specific airspeed ranges.
Examples include findings in Ringed Turtle-Doves (*Streptopelia risoria*), Black-billed
Magpies (*Pica pica*), and various hummingbird species.[^4] Notably, Engel et al.
(2006) documented that flight costs in Rosy Starlings (*Pastor roseus*) remained
independent of flight speed despite a 55% increase in speed,[^8] and Berger (1985) found
J-shaped relationships in Sparkling Violetear (*Colibri coruscans*) and Green Violetear
(*C. thalassinus*), where flight metabolism did not vary significantly between hovering
and forward flight up to 7 m·s-1.[^8]

This variability suggests that bird flight is a highly adaptable phenomenon.
The “optimal” flight speed is likely context-dependent, influenced by factors beyond
simple energy minimization for a given airspeed, such as foraging strategy or migratory
demands. Birds may employ sophisticated kinematic and physiological strategies to
modulate their energy expenditure, altering the apparent shape of the power-speed
relationship. The existence of “flat” power curves in some species is particularly
intriguing, as it implies advanced mechanisms to maintain near-constant energetic costs
across a functional range of flight speeds, which could be highly adaptive for certain
ecological niches.[^8] A fundamental, yet unresolved, question is whether the power
curve is indeed perceived by a bird as a continuous, smooth function of airspeed, a
hypothesis that has not been formally tested.[^4] Discrepancies between theoretical
predictions and empirical observations may stem from several factors, including
differences in the specific component of power being measured (e.g., metabolic power
input versus calculated mechanical power output), the inherent limitations and potential
stresses of experimental conditions (particularly in wind tunnels), and the complexities
of accurately modeling the efficiency of converting metabolic energy to mechanical
work.[^4]

### 3.2 The Components of Aerodynamic Drag

The total aerodynamic drag experienced by a flying bird is primarily composed of three
main components. The sum of the power required to overcome these drag components gives
the total mechanical power required for steady level flight.[^5]

* **Induced Drag:** This component of drag is an unavoidable consequence of generating
  lift. It arises from the redirection of air downwards by the wings, which creates
  wingtip vortices. Induced drag is inversely related to airspeed; as airspeed increases,
  induced drag decreases.
  Consequently, the power required to overcome induced drag (Pind​) is highest at low
  speeds.[^5] Conceptually, Pind​ is proportional to
  (Weight)2/(Airspeed×Wingspan2×Air\_density).

* **Parasite Drag:** This refers to the drag exerted by the bird’s body (fuselage drag),
  distinct from the wings.
  It is caused by the pressure distribution around the body and skin friction as the
  bird moves through the air.
  Parasite drag (Dpar​) increases with the square of the airspeed, following the
  relationship Dpar​=21​ρV2Sb​CD,par​, where ρ is air density, V is airspeed, Sb​ is the
  body’s frontal area, and CD,par​ is the parasite drag coefficient.[^5] Consequently,
  the power required to overcome parasite drag (Ppar​) increases with the cube of the
  airspeed (Ppar​=Dpar​×V).[^5]

* **Profile Drag:** This component arises from the friction and pressure drag of the
  wings themselves as they move through the air.
  It is the drag associated with the wing’s profile, even when not generating net lift
  (i.e., at zero angle of attack relative to the local airflow).
  Profile power (Ppro​) also generally increases with airspeed, particularly at higher
  speeds.[^5]

### 3.3 The Influence of Wing and Tail Morphology and Flight Kinematics

The intricate interplay between a bird’s morphology and its flight kinematics is
fundamental to its aerodynamic capabilities.
Morphological adaptations provide the anatomical “toolkit,” while kinematics represent
the dynamic strategies employed to use that toolkit effectively.

**Wing Function and Specializations:** Avian wings are sophisticated aerofoils
responsible for generating both lift and thrust, primarily through complex flapping
motions.[^30] The primary feathers, located on the outer part of the wing (the “hand”),
are crucial for generating most of the thrust, especially during the downstroke.
The secondary feathers, located on the inner part of the wing (the “arm”), contribute
significantly to the wing’s aerofoil shape and thus to lift generation.[^30] The alula,
a small group of feathers on the anterior edge of the wing corresponding to the bird’s
“thumb,” acts as a leading-edge slat.
It deploys at high angles of attack to delay aerodynamic stall, particularly at low
airspeeds or during landing maneuvers, by maintaining smoother airflow over the wing’s
upper surface.[^30]

**Wing Morphing Capabilities:** Birds possess a remarkable ability to dynamically alter
their wing shape and area during flight, a capability known as wing morphing.
This includes active changes in wing chord (width), span (length), sweep (angle
backwards or forwards), twist (variation in angle of attack along the span), and camber
(curvature of the aerofoil).
These adjustments are achieved through coordinated movements of the elbow and wrist
joints and the precise control of the flight feathers.
Such morphing allows birds to optimize aerodynamic performance across a wide range of
airspeeds and flight modes (e.g., flapping, gliding, soaring, maneuvering).
It helps to maintain attached airflow over the wings, reduce induced drag (especially at
the wingtips by modifying vortex shedding), and efficiently modulate lift and thrust
production.[^30] Recent research also indicates that covert feathers—the smaller
feathers overlying the base of the primary and secondary flight feathers—may play an
active aerodynamic role by forming rows of deployable flaps that can improve lift and
reduce drag, particularly when the wing is operating near its stalling angle.[^32] This
suggests an even finer level of aerodynamic control than previously appreciated.

**Tail Function in Flight Control:** The tail in birds is not merely a passive
stabilizer but an integral and active component of the lifting and control system.
Its position relative to the wings and its ability to be spread, fanned, depressed,
elevated, and tilted allow it to contribute significantly to stability, balance,
maneuverability, and lift enhancement.
These functions are particularly important during slow flight, take-off, and landing,
where the tail can act like an aircraft’s elevator and rudder, and also augment lift by
interacting with the airflow from the wings.[^30]

**Kinematic Adjustments for Varying Airspeeds:** Birds continuously and dynamically
adjust their wingbeat kinematics—including stroke amplitude (the angle through which the
wing sweeps), flapping frequency (wingbeats per second), and the mean elevation and
inclination of the wingbeat plane—to meet the changing thrust-to-lift requirements at
different airspeeds.[^31] For instance, research has shown that flapping with a greater
ventral (downward) than dorsal (upward) excursion of the wings is an aerodynamically
efficient strategy for increasing thrust, which is particularly important at higher
speeds where drag is greater.[^31] These kinematic adjustments demonstrate a
sophisticated level of active control to maintain or optimize aerodynamic efficiency.

**The Strouhal Number (St) as an Efficiency Indicator:** The Strouhal number, a
dimensionless parameter defined as St=fA/V (where f is wingbeat frequency, A is wingtip
stroke amplitude, and V is airspeed), is often used to characterize the unsteady
aerodynamics of flapping flight and is considered an indicator of propulsive efficiency.
Many flying animals, including birds, appear to modulate their kinematics to maintain
the Strouhal number within a relatively narrow range, typically cited as 0.2–0.4.[^2]
Operating within this range is associated with high propulsive efficiency in flapping
propulsion. However, some research suggests a more nuanced role for St.
While propulsive efficiency (ηp​, the efficiency of converting metabolic power into
useful thrust power) may peak within this St range, the overall efficiency of generating
aerodynamic force (considering the costs of producing both lift and thrust
simultaneously) might decrease with increasing St.
This implies that the optimal Strouhal number for a bird may represent a compromise,
depending on the relative costs and demands for generating thrust versus lift in a given
flight scenario.[^31] The active regulation of kinematics to operate within a certain St
range suggests a sensory feedback mechanism allowing birds to perceive their aerodynamic
state and adjust accordingly.

### 3.4 Persistent Uncertainties and Frontiers in Avian Flight Research

Despite significant advances in the study of avian flight, several areas remain
characterized by ongoing research and unresolved questions.
The precise, mechanistic relationship between the complex, three-dimensional kinematics
of flapping wings and the resultant aerodynamic forces and overall flight performance is
still an active and challenging area of investigation.
Current aerodynamic models often rely on simplifications (such as quasi-steady
assumptions) of these intricate and highly unsteady kinematics.[^31]

Disentangling the individual aerodynamic effects of multiple kinematic parameters that
birds often adjust simultaneously (e.g., frequency, amplitude, angle of attack, wing
twist, wing deformation) is a complex analytical task.[^31] This difficulty has spurred
the use of innovative experimental tools, such as dynamically scaled robotic wings and
advanced computational fluid dynamics (CFD) modeling.[^31] These approaches allow
researchers to systematically vary individual kinematic parameters while holding others
constant, enabling a more direct assessment of their aerodynamic consequences and a
shift from purely correlative studies in live birds towards a more causative
understanding of flight mechanics.
This, in turn, has significant biomimetic implications for the design of more efficient
flapping-wing micro air vehicles (FWAVs).[^33]

Furthermore, the internal physiological processes occurring within a bird during flight,
and how these processes (e.g., muscle efficiencies, metabolic pathways, heat
dissipation) interface with and constrain aerodynamic power output, are still not fully
understood.[^4] The specific aerodynamic roles and quantitative benefits of certain
subtle morphological features, such as the detailed function of different rows of covert
feathers, are also still being actively investigated and quantified.[^32]

## IV. Literature Synthesis: A Comparative Analysis of Airspeed Velocity

The study of avian airspeed reveals a remarkable diversity across taxa, reflecting a
wide array of morphological adaptations, flight styles, and ecological requirements.
Comprehensive tracking radar studies, particularly the work by Alerstam et al.
(2007) which encompassed 138 bird species, indicate that mean cruising airspeeds during
migration typically fall within a range of approximately 8 m/s to 23 m/s.[^7]

While fundamental aerodynamic theory predicts that cruising flight speed should scale
positively with body mass (approximately as (body mass)1/6) and wing loading
(approximately as (wing loading)1/2),[^7] empirical data from extensive field studies
have shown that the actual scaling exponents are significantly smaller.
Alerstam and colleagues reported exponents of approximately 0.12 for body mass and 0.32
for wing loading.[^6] This phenomenon, often described as a “compression of the speed
range,” suggests that evolutionary pressures have acted to counteract the development of
excessively slow flight speeds in species with low wing loading and excessively fast
speeds in those with high wing loading.[^6] This implies that factors beyond simple
aerodynamic scaling are at play in determining a species’ characteristic airspeed.

Indeed, phylogeny emerges as a highly significant factor in explaining interspecific
variation in airspeed, often exerting a stronger influence than body mass or wing
loading alone. Species within the same evolutionary lineage tend to exhibit similar
characteristic flight speeds, suggesting that shared ancestry and associated functional
flight adaptations play a crucial role.[^6] For instance, the Alerstam et al.
(2007) study found that birds of prey and herons, on average, fly slower than would be
predicted solely by their mass and wing loading, whereas songbirds and shorebirds tend
to fly faster.[^6]

It is generally accepted that many bird species possess at least two distinct modes of
flight speed: a “normal” or “cruising” rate utilized for everyday activities such as
foraging and for sustained migratory flight, and an “accelerated” speed.
This accelerated speed, which can sometimes be nearly double the normal rate, is
typically employed for short durations during specific situations such as predator
evasion or prey pursuit.[^14] Furthermore, migratory flight is often considered to be
undertaken at higher average airspeeds than non-migratory “cruising” flight.
This is likely an adaptation to optimize time or energy expenditure over the vast
distances covered during migration.[^10]

### 4.1 The Fastest Flyers – Records and Verifications

The avian world boasts some truly remarkable speedsters, with different species holding
records for dive speeds versus sustained level flight.

Dive Speeds (Stoops) – The Realm of Raptors:

The highest airspeeds achieved by any bird occur during the high-speed hunting dives, or
“stoops,” characteristic of several raptor species.

* **Peregrine Falcon (*Falco peregrinus*):** This species is universally recognized as
  the fastest animal on the planet during its stoop.

  + Popular accounts and some sources state that it can exceed 320 km/h (approximately
    89 m/s).[^1]

  + A maximum speed of 389 km/h (approximately 108 m/s) was reported in a National
    Geographic television program; however, the primary scientific publication detailing
    the measurement methodology for this specific extraordinary figure is often not
    readily cited in accessible peer-reviewed literature.[^1]

  + More rigorously documented radar measurements by Peter and Kestenholz (1998), cited
    by Alerstam, recorded a maximum dive airspeed of 51 m/s (184 km/h) for a Peregrine
    Falcon.[^43] While this value is considerably lower than some popular accounts, it
    represents a scientifically measured and published speed.
    Research by Ponitz et al.
    (2014), detailed in a study by Fischer et al.
    (2014), provides further support for dive speeds exceeding 320 km/h and includes
    details on wing morphing strategies employed by peregrines during different phases
    of their dive.[^39] In one specific experiment tracking a diving falcon with
    high-speed cameras, a maximum diving velocity of 22.5 m s-1 (81 km/h) was reached at
    a flight path angle of 50.75°, though this was in a controlled setting and not
    representative of maximum natural stoop speeds.[^39]

* **Golden Eagle (*Aquila chrysaetos*):** This large raptor has been recorded achieving
  impressive dive speeds of up to 322 km/h (approximately 89 m/s).[^1]

* **Saker Falcon (*Falco cherrug*):** Another powerful falcon, the Saker is capable of
  dive speeds up to 320 km/h (approximately 89 m/s).[^1]

* **Gyrfalcon (*Falco rusticolus*):** The largest of the falcons, the Gyrfalcon,
  achieves dive speeds in the range of 187–209 km/h (approximately 52-58 m/s).[^1]

Level Flight (Maximum Horizontal Airspeed) – A Realm of Swifts and Other Fast Flyers:

Determining the absolute fastest bird in sustained, powered level flight is subject to
some debate, largely due to the challenges of verification and standardization of
measurement methods.

* **White-throated Needletail (*Hirundapus caudacutus*):** This large swift is
  frequently cited in popular and ornithological literature as the fastest bird in level
  flight.

  + Reported top speeds are typically around 169 km/h (approximately 46.9 m/s)[^1] or
    occasionally stated as 170 km/h.[^40]

  + A crucial caveat consistently accompanies this record: the measurement methods used
    to obtain this speed have reportedly never been published or scientifically
    verified.[^1] This lack of peer-reviewed documentation means the 169-170 km/h figure
    should be treated with caution by the scientific community.
    More recent tracking studies on this species have focused on migratory routes rather
    than verifying maximum airspeeds.[^45] Some sources provide a slightly lower, but
    still impressive, figure of up to 130 km/h.[^46]

* **Common Swift (*Apus apus*):** This species holds the record for the fastest
  *confirmed* level flight speed by a bird.

  + A maximum horizontal flying speed of 111.5 km/h (approximately 31.0 m/s or 69.3 mph)
    has been reliably documented.[^1] This speed is often cited in reference to the work
    of Bruderer and colleagues, whose radar studies provided extensive data on swift
    flight. While the specific primary paper by Bruderer confirming this exact value was
    not fully detailed in the provided snippets, the consistency of this figure across
    multiple reputable sources, including those referencing Guinness World Records,[^1]
    lends it strong credibility.

  + During specialized social flight displays known as “screaming parties,” Common
    Swifts have been recorded achieving even higher instantaneous airspeeds.
    Henningsson et al. (2010) used stereo high-speed cameras to measure horizontal speeds
    averaging 20.9 m/s (75.2 km/h), with a maximum recorded horizontal speed of 31.1 m/s
    (112.0 km/h).[^43] This is the highest directly measured self-powered flight speed
    for this species.

* **Other Notably Fast Species in Level Flight:**

  + **Eurasian Hobby (*Falco subbuteo*):** A small, agile falcon known to prey on swifts
    and swallows, it can reportedly reach maximum airspeeds of 159 km/h (approximately
    44.2 m/s).[^1]

  + **Frigatebirds (*Fregata* spp.):** These highly aerial seabirds, known for their
    soaring capabilities and kleptoparasitism, can achieve airspeeds up to 153 km/h
    (approximately 42.5 m/s).[^1]

  + **Spur-winged Goose (*Plectropterus gambensis*):** This large waterfowl has been
    recorded at airspeeds up to 143 km/h (approximately 39.7 m/s).[^1]

  + **Grey-headed Albatross (*Thalassarche chrysostoma*):** Recorded at a maximum
    horizontal speed of 127 km/h (approximately 35.3 m/s), often achieved while
    utilizing strong winds during storms.[^1]

  + **Diving Ducks (Anatidae):** Several species of diving ducks are known for their
    rapid flight. The Red-breasted Merganser (*Mergus serrator*) can reach 130 km/h
    (approx. 36.1 m/s),[^1] the Canvasback (*Aythya valisineria*) 128 km/h (approx.
    35.6 m/s),[^1] and the Common Eider (*Somateria mollissima*) 123 km/h (approx.
    34.2 m/s).[^1] Alerstam et al.
    (2007) noted that diving ducks, as a group, achieved the fastest mean speeds in
    their extensive radar study, with several species exceeding 20 m/s (72 km/h), up to
    a maximum of 23 m/s (82.8 km/h).[^7]

### 4.2 The Slowest Flyers – Considerations and Examples

Identifying the “slowest” flying bird is less straightforward than identifying the
fastest, as flight speed is highly dependent on context (e.g., foraging, landing,
hovering) and can be intentionally reduced.
However, some species are characteristically slower in their typical cruising or
foraging flight.

* **General Observations:** Alerstam et al.
  (2007) found that birds of prey, herons, gulls, terns, and songbirds generally had
  flight speeds in the lower part of the 8–23 m/s range observed for migrating
  birds.[^7] Larger bird species, in practice, tend to employ airspeeds slower than
  their theoretically optimal speed for maximizing horizontal travel if they are
  prioritizing minimizing altitude loss per distance covered, for instance, when gliding
  between thermals.[^12]

* **Specific Examples of Relatively Slow Flight:**

  + **Osprey (*Pandion haliaetus*):** Schnell (1978) recorded airspeeds for this species
    that were considered “characteristically rather slow,” which is expected for a large
    bird engaged in short flights or circling while hunting.[^21] Average airspeeds were
    around 27-29 mph (approximately 12-13 m/s) across or into the wind, but dropped to
    an average of 17 mph (approximately 7.6 m/s) with a tailwind.[^21] Tucker and
    Schmidt-Koenig (1971) recorded circling airspeeds for an Osprey varying from 9 to 16
    mph (approximately 4.0 to 7.2 m/s).[^21]

  + **Black-necked Stilt (*Himantopus mexicanus*):** In Schnell’s (1978) study, this
    species exhibited average airspeeds around 19-20 mph (approximately 8.5-8.9
    m/s).[^21]

  + **American Woodcock (*Scolopax minor*):** While not extensively detailed in the
    provided snippets regarding cruising speed, this species is famously known for its
    very slow, fluttering display flights, sometimes cited as one of the slowest flying
    birds during these specific maneuvers, though quantitative airspeed data for this
    behavior were not present in the provided materials.

  + **Hummingbirds (Trochilidae):** While capable of rapid, agile movements and
    relatively fast burst speeds for their size[^1], their ability to hover (zero
    airspeed) and fly very slowly is a hallmark of the family.
    Their flight speeds are often perceived as faster due to their small size and high
    wingbeat frequencies.[^50]

  + **Some Passerines:** Early observations suggested that some smaller passerine birds
    engage in ordinary flight at speeds less than 20 mph (approximately 8.9 m/s).[^14]
    The Alerstam et al. (2007) dataset, with a minimum mean airspeed of 8 m/s for some
    species, supports the idea that many smaller birds, including songbirds, operate at
    the lower end of the avian airspeed spectrum during migration.[^7] For example, in a
    study by Pennycuick et al.
    (2013) using an ornithodolite, the Common Tern (*Sterna hirundo*) had a mean
    airspeed of 11.0 m/s, and the Black-headed Gull (*Larus ridibundus*) 11.4 m/s.[^18]
    The Pied Wagtail (*Motacilla alba*) was recorded at 13.3 m/s.[^18]

It is important to note that many of the slower reported speeds are often average
cruising speeds or speeds recorded during specific behaviors like foraging or circling,
and most birds can achieve faster burst speeds when necessary.
The lower end of the 8 m/s (approx.
28.8 km/h) mean airspeed found by Alerstam et al.
(2007) for migrating birds likely represents a practical minimum for efficient sustained
travel for many species.[^7]

## V. Airspeed Velocity in Swallows (Hirundinidae) and Swifts (Apodidae)

Swallows, martins (family Hirundinidae), and swifts (family Apodidae, though not closely
related to swallows, share convergent adaptations for highly aerial lifestyles) are
renowned for their exceptional aerial agility and reliance on flight for foraging.
Their flight characteristics have been the subject of numerous studies.

### 5.1 Barn Swallow (*Hirundo rustica*)

The Barn Swallow is a well-studied hirundine, with detailed kinematic data available
from wind tunnel experiments.

* **Wind Tunnel Studies (Park et al., 2001; Hedenström et al.):**

  + Two Barn Swallows were filmed in the Lund wind tunnel at airspeeds ranging from 4
    m/s up to 14 m/s (bird #1) or 13 m/s (bird #2).[^17]

  + Wingbeat frequency exhibited a clear U-shaped relationship with airspeed.
    For bird #1, the minimum frequency was 7.04 Hz[^2] at an airspeed of 8.9 m/s.[^2]
    For bird #2, the minimum frequency was 7.11 Hz[^2] at an airspeed of 8.7 m/s.[^22]
    At these minimum power speeds, Strouhal numbers were calculated to be approximately
    0.18 and 0.19, respectively, which aligns with the typical range (0.2-0.4) observed
    for efficient flight in many animals, though birds often fall on the lower side of
    this range.[^2]

  + Wingbeat amplitude (the angle described by the pivoting of the wing at the shoulder)
    increased with airspeed, from approximately 70° at low speeds to over 120° at high
    speeds.[^17]

  + Mid-downstroke wingspan was observed to decrease with increasing airspeed.[^17]

  + A notable kinematic feature was the appearance of upstroke pauses (brief cessations
    of flapping during the upstroke) at airspeeds exceeding 8 m/s for one bird and 5 m/s
    for the other.[^17]

  + The study by Park et al.
    (2001) concluded that the common method of estimating a bird’s body drag coefficient
    by matching the calculated minimum power speed (V&lt;sub>mp&lt;/sub>) with the
    observed speed of minimum wingbeat frequency was not valid for the Barn Swallow,
    possibly due to the complexities introduced by these upstroke pauses and other
    kinematic adjustments.[^17]

* **Intermittent Flight**[^3]**:**

  + Barn Swallows primarily perform “partial bounds” during intermittent flight.
    This involves brief interruptions of the upstroke, and these pauses are
    progressively prolonged as the flight angle (incline or decline) decreases.[^3]

  + Effective wingbeat frequencies (mean number of wingbeats per second, accounting for
    pauses) for Barn Swallows were reported to range from 2.5 to 8.5 s-1.[^3]

  + Consistent with the wind tunnel findings, wingbeat frequency during continuous
    flapping varied with airspeed in a U-shaped curve, suggesting a minimum power speed
    of roughly 9 m/s.[^3]

These detailed kinematic studies on Barn Swallows highlight a sophisticated modulation
of wingbeat parameters across a range of airspeeds.
The U-shaped power/frequency curve, with minima around 8-9 m/s, suggests an adaptation
for efficient flight across the speeds typically used for their aerial insectivorous
foraging and general transit.

### 5.2 House Martin (*Delichon urbicum*)

The House Martin, another common hirundine, also exhibits specialized flight
adaptations.

* **General Flight Speed:** A typical flight speed for the House Martin is reported as
  11 m/s (approximately 39.6 km/h or 36 ft/s).[^51]

* **Wingbeat Rate:** The House Martin averages approximately 5.3 wingbeats per second,
  which is notably faster than the average of 4.4 beats per second reported for the Barn
  Swallow.[^51]

* **Wind Tunnel Studies (Rosén et al., 2007):**

  + The wingbeat kinematics and wake structure of a trained House Martin were studied in
    free, steady flight in a wind tunnel at airspeeds of 4, 6, 8, and 10 m/s.[^23]

  + A characteristic feature of the House Martin’s wingbeat at higher flight speeds was
    the presence of a distinct pause during the upstroke.[^23]

  + At slow speeds (specifically 4 m/s), the upstroke did not contribute to weight
    support, indicating a different aerodynamic strategy compared to higher speeds where
    the upstroke becomes more aerodynamically significant.[^23]

  + In the wind tunnel, gliding sequences, which were almost absent at the lowest flight
    speeds, increased in both length and frequency as airspeed increased.
    The data presented were selected for steady flapping flight only.[^23]

* **Intermittent Flight**[^3]**:**

  + During descent, House Martins tended to concentrate their wingbeats into bursts,
    performing true gliding flight during the intervening rest phases.
    This contrasts with the partial bounding strategy more typical of Barn Swallows.[^3]

  + Effective wingbeat frequencies for House Martins ranged from 2 to 10.5 s-1.[^3]

  + Similar to the Barn Swallow, the wingbeat frequency of House Martins varied with
    airspeed according to a U-shaped curve, suggesting a minimum power speed of roughly
    9 m/s.[^3]

The differences in intermittent flight strategies observed between Barn Swallows
(primarily partial bounds) and House Martins (true gliding, especially in descent),
despite their similar overall U-shaped frequency curves and ecological roles as aerial
insectivores, suggest subtle variations in aerodynamic optimization or behavioral
preferences. These variations could be related to finer-scale differences in their
typical foraging altitudes, preferred prey types, or slight morphological distinctions
in wing or tail structure not captured by broad airspeed measurements alone.
Both species, however, demonstrate a clear adaptation for efficient flight around a
similar minimum power speed.

### 5.3 Purple Martin (*Progne subis*)

The Purple Martin is the largest swallow species found in North America.[^52]

* **Reported Flight Speed (General):** Popular sources report that Purple Martins can
  reach speeds of up to 40 mph (approximately 17.9 m/s or 64.4 km/h).[^52] It is
  important to note that this figure often comes from general nature center publications
  or similar outreach materials, rather than peer-reviewed primary research employing
  precise measurement techniques like radar or wind tunnels.

* **Migratory Speeds (from Geolocator Studies):**

  + One study utilizing geolocators on Purple Martins reported an impressive average
    flight speed (travel rate) of 600 km/day during a 21-day spring migration for one
    individual.[^26]

  + Another geolocator study documented individuals covering approximately 2414 km (1500
    miles), including a non-stop over-water flight of about 805 km (500 miles), in less
    than a week. One particularly swift individual in this study flew approximately 7081
    km (4,400 miles) in just 13 days, averaging over 538 km/day (more than 300
    miles/day).[^27] These data reflect remarkable endurance and sustained travel rates
    during migration but do not represent instantaneous unladen airspeeds.

* **Flight Behavior and Ecology:** Purple Martins are active during the day, with peak
  activity often observed at dawn and dusk.
  They are colonial nesters and forage by hunting insects in large flocks.[^53] They are
  capable of traveling significant distances, from 2.8 to 664 km, to return to their
  nests.[^53]

* **Altitude Studies:** A study by Shipley et al.
  (2018) using altitude dataloggers found that Purple Martins consistently flew at
  higher altitudes compared to Tree Swallows and Barn Swallows.
  Their flight altitude responded positively to conditions of greater thermal uplift.
  The mean daily altitude recorded for Purple Martins was 119 m, with a maximum recorded
  altitude of 1945 m.[^54] While this study provides valuable information on vertical
  habitat use, it did not directly measure or report airspeeds.

* **GPS Tracking for Migration Strategies:** High-precision GPS tracking has been used
  to study the migration strategies of Purple Martins, confirming their primarily
  diurnal migration pattern but also revealing instances of nocturnal flight,
  particularly during barrier crossings (e.g., over the Gulf of Mexico).[^24] Again, the
  focus of such studies is typically on timing, routing, and behavioral plasticity
  rather than the precise measurement of instantaneous airspeeds.

Compared to the Barn Swallow and House Martin, there is a noticeable lack of detailed,
primary-source unladen airspeed data for the Purple Martin derived from controlled
experimental conditions, such as wind tunnel studies, or from direct radar tracking of
individuals where airspeed is explicitly calculated.
Most available quantitative data for *Progne subis* pertains to impressive migratory
travel rates derived from geolocator or GPS studies, or general speed estimations from
less formal sources.
This represents a potential knowledge gap regarding the fine-scale flight mechanics and
specific cruising airspeeds of Purple Martins under defined conditions, which would be
valuable for a more complete comparative aerodynamic analysis within the Hirundinidae.

## VI. Tabulated Airspeed Data for Selected Bird Species

The following table summarizes unladen airspeed data for a variety of bird species,
drawing from the literature discussed in this report.
It is crucial to consider the measurement method and context, as these factors
significantly influence the recorded speeds.
Speeds are presented as reported in the source material.

| **Common Name** | **Scientific Name** | **Family** | **Average/Typical Horizontal Airspeed** | **Maximum Horizontal Airspeed** | **Maximum Dive Airspeed (Stoop)** | **Measurement Method/Context** | **Sources** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Peregrine Falcon | *Falco peregrinus* | Falconidae | 65–90 km/h (18.1–25 m/s) | 110 km/h (30.6 m/s) | >320 km/h (>88.9 m/s); 389 km/h (108.1 m/s) reported; 51 m/s (184 km/h) radar measured | Observation; Radar; High-speed video (dive stages) | [^1] |
| Saker Falcon | *Falco cherrug* | Falconidae |  | 150 km/h (41.7 m/s) | 320 km/h (88.9 m/s) | Not specified in snippet | [^1] |
| Golden Eagle | *Aquila chrysaetos* | Accipitridae | 45–51 km/h (12.5–14.2 m/s) | 129 km/h (35.8 m/s) | 322 km/h (89.4 m/s) | Observation/Not specified | [^1] |
| Gyrfalcon | *Falco rusticolus* | Falconidae | 80–100 km/h (22.2–27.8 m/s) | 145 km/h (40.3 m/s) | 187–209 km/h (51.9–58.1 m/s) | Not specified in snippet | [^1] |
| White-throated Needletail | *Hirundapus caudacutus* | Apodidae |  | 169 km/h (46.9 m/s) (unconfirmed) |  | Observation (unverified method) | [^1] |
| Common Swift | *Apus apus* | Apodidae | ~11.5 m/s (41.4 km/h) (migration)† | 111.6 km/h (31.0 m/s) (confirmed level); 31.1 m/s (112.0 km/h) (screaming party) |  | Radar (migration); Observation (level); Stereo high-speed camera (screaming party) | [^1] |
| Pacific Swift | *Apus pacificus* | Apodidae |  | 166 km/h (46.1 m/s) |  | Not specified in snippet | [^40] |
| Eurasian Hobby | *Falco subbuteo* | Falconidae |  |  | 159 km/h (44.2 m/s) (likely pursuit/dive) | Not specified in snippet | [^1] |
| Frigatebird | *Fregata* spp. | Fregatidae |  |  | 153 km/h (42.5 m/s) (likely dive/fast glide) | Not specified in snippet | [^1] |
| Spur-winged Goose | *Plectropterus gambensis* | Anatidae |  |  | 143 km/h (39.7 m/s) | Not specified in snippet | [^1] |
| Grey-headed Albatross | *Thalassarche chrysostoma* | Diomedeidae |  | 127 km/h (35.3 m/s) |  | Riding Antarctic storm | [^1] |
| Red-breasted Merganser | *Mergus serrator* | Anatidae | ~20.0 m/s (72 km/h) (migration)† | 130 km/h (36.1 m/s) (escape speed up to 80 mph reported) |  | Radar (migration); Observation | [^1] |
| Canvasback | *Aythya valisineria* | Anatidae |  | 128 km/h (35.6 m/s) |  | Not specified in snippet | [^1] |
| Common Eider | *Somateria mollissima* | Anatidae | ~19.0 m/s (68.4 km/h) (migration)† | 123 km/h (34.2 m/s) |  | Radar (migration); Not specified | [^1] |
| Eurasian Teal | *Anas crecca* | Anatidae | ~17.4 m/s (62.6 km/h) (migration)† | 97 km/h (26.9 m/s) (older report 70 km/h) |  | Radar (migration); Not specified | [^1] |
| Anna’s Hummingbird | *Calypte anna* | Trochilidae |  | 56 km/h (15.6 m/s) | 70 km/h (19.4 m/s) (dive/courtship) | Not specified in snippet | [^1] |
| Barn Swallow | *Hirundo rustica* | Hirundinidae | 8.7-8.9 m/s (min. wingbeat freq. speed) | 13-14 m/s (max. tested in wind tunnel) |  | Wind Tunnel | [^2] |
| House Martin | *Delichon urbicum* | Hirundinidae | 11 m/s (typical); ～9 m/s (min. power speed suggested) | 10 m/s (max. tested in wind tunnel for kinematics) |  | Observation; Wind Tunnel | [^3] |
| Purple Martin | *Progne subis* | Hirundinidae |  | Up to 40 mph (~17.9 m/s or ～64.4 km/h) (general report) |  | Observation (general) | [^52] |
| Osprey | *Pandion haliaetus* | Pandionidae | ~12-13 m/s (across/into wind); 4.0-7.2 m/s (circling) |  |  | Doppler Radar; Observation | [^21] |
| Brown Pelican | *Pelecanus occidentalis* | Pelecanidae | ~~26-27 mph (~~11.6-12.1 m/s) |  |  | Doppler Radar | [^21] |
| Chimney Swift | *Chaetura pelagica* | Apodidae | ~~36.7 mph (~~16.4 m/s) |  |  | Doppler Radar | [^21] |
| American Robin | *Turdus migratorius* | Turdidae | ~~24.7-29.5 mph (~~11.0-13.2 m/s) |  |  | Doppler Radar | [^21] |
| European Starling | *Sturnus vulgaris* | Sturnidae | ~~25.3-28.9 mph (~~11.3-12.9 m/s); ～15.4 m/s (migration)† |  |  | Doppler Radar; Ornithodolite | [^18] |
| House Sparrow | *Passer domesticus* | Passeridae | ~~23.5-29.7 mph (~~10.5-13.3 m/s) |  |  | Doppler Radar | [^21] |
| Rock Pigeon | *Columba livia* | Columbidae | 12.9 ± 1.8 m/s |  |  | GPS Tracking | [^25] |
| Common Tern | *Sterna hirundo* | Laridae | 11.0 m/s (migration)† |  |  | Ornithodolite | [^18] |
| Black-headed Gull | *Larus ridibundus* | Laridae | 11.4 m/s (migration)† |  |  | Ornithodolite | [^18] |
| Kestrel (Common) | *Falco tinnunculus* | Falconidae | 12.6 m/s (migration)† |  |  | Ornithodolite | [^18] |
| Grey Heron | *Ardea cinerea* | Ardeidae | 12.7 m/s (migration)† |  |  | Ornithodolite | [^18] |

Footnotes for Table:

All speeds are unladen airspeeds unless otherwise specified.
Conversions between units are approximate.

† Data from Pennycuick et al.
(2013)18 or Alerstam et al.
(2007)7 often refer to mean equivalent airspeeds (Ue​) during migration, measured by
ornithodolite or tracking radar, respectively.
The Alerstam et al. (2007) study provided a range of 8-23 m/s across 138 species;
specific values for all species are in their Protocol S1, which was not fully available
in the provided snippets, so group trends or specific examples cited in the main text of
Alerstam et al. or secondary sources citing it are used.

The “unconfirmed” status for White-throated Needletail reflects the lack of published,
verifiable measurement methodology for the commonly cited 169 km/h speed.1

Maximum dive speeds are highly specialized behaviors and not representative of typical
flight.

Average/Typical Horizontal Airspeed often refers to cruising speeds, but context varies
(e.g., wind tunnel minimum power speed vs.
observed migratory speed).

## VII. Concluding Remarks

This comparative analysis of unladen airspeed velocity in birds underscores the vast
diversity in flight capabilities across avian taxa, shaped by a complex interplay of
morphology, physiology, ecology, and evolutionary history.
The data reveal a spectrum from the extraordinary dive speeds of raptors like the
Peregrine Falcon, exceeding 320 km/h,[^1] to the more modest, though still impressive,
cruising speeds employed by a multitude of species during migration and foraging,
typically ranging from 8 to 23 m/s.[^7] The title of fastest bird in confirmed level
flight belongs to the Common Swift at 111.5 km/h,[^1] though the White-throated
Needletail is often cited with an unconfirmed speed of 169 km/h.[^1] For swallows and
martins, wind tunnel studies on species like the Barn Swallow and House Martin indicate
typical minimum power or efficient cruising speeds around 8-11 m/s, with sophisticated
kinematic adjustments to maintain performance across a range of operational speeds.[^3]

The measurement of avian airspeed is an inherently complex endeavor, with each
methodology—from radar ornithology and wind tunnel experiments to direct observation and
advanced biologging—possessing its own set of advantages, limitations, and contextual
applicability. Understanding the specific conditions and techniques under which airspeed
data are collected is therefore paramount for accurate interpretation and meaningful
comparison. While general aerodynamic principles provide a robust framework for
understanding bird flight, the specifics of power curves, drag components, and kinematic
strategies exhibit considerable interspecific variation and remain active areas of
scientific inquiry. The relationship between morphology (e.g., wing aspect ratio, tail
design), phylogeny, and ecological pressures (e.g., foraging mode, migratory distance)
clearly shapes the evolution of flight performance, often leading to convergent
solutions for similar aerial lifestyles but also unique adaptations within lineages.

Despite significant progress, several avenues for future research remain pertinent.
There is a continuing need for rigorously verified airspeed data for species with
historically unconfirmed records, such as the White-throated Needletail.
More detailed kinematic and aerodynamic studies, particularly those conducted under
natural free-flight conditions or in advanced, large-scale wind tunnels that can
accommodate a wider range of natural behaviors, would be invaluable for a broader array
of bird species. Specifically for larger hirundines like the Purple Martin, dedicated
studies on unladen cruising airspeed using precise methodologies would fill a current
gap in comparative data.
The ongoing refinement and application of remote sensing technologies, sophisticated
biologging devices (including those integrating accelerometers and air pressure sensors
for direct airspeed estimation), and advanced analytical techniques (such as
computational fluid dynamics) promise to yield even deeper insights into the nuanced
world of avian airspeed, flight behavior, and the remarkable energetic and biomechanical
efficiencies that characterize bird flight.

## Works Cited

[^1]: List of birds by flight speed - Wikipedia, accessed May 16, 2025,
    <https://en.wikipedia.org/wiki/List_of_birds_by_flight_speed>

[^2]: A Revised Unladen Swallow Estimate - style.org, accessed May 16, 2025,
    <https://style.org/unladenswallow/update/>

[^3]: Flexibility in flight behaviour of Barn Swallows (Hirundo rustica) and House
    Martins (Delichon urbica) tested in a wind tunnel | Request PDF - ResearchGate,
    accessed May 16, 2025,
    <https://www.researchgate.net/publication/12058959_Flexibility_in_flight_behaviour_of_Barn_Swallows_Hirundo_rustica_and_House_Martins_Delichon_urbica_tested_in_a_wind_tunnel>

[^4]: Rayner & Ward: Power curves of flying birds, accessed May 16, 2025,
    <https://www.internationalornithology.org/PROCEEDINGS_Durban/Symposium/S31/S31.1.htm>

[^5]: (PDF) Aerodynamics, evolution and ecology of avian flight, accessed May 16, 2025,
    <https://www.researchgate.net/publication/222525244_Aerodynamics_evolution_and_ecology_of_avian_flight>

[^6]: What Determines The Speed At Which Birds Fly?
    - ScienceDaily, accessed May 16, 2025,
      <https://www.sciencedaily.com/releases/2007/07/070717014442.htm>

[^7]: Flight Speeds among Bird Species: Allometric and Phylogenetic Effects - Tethys,
    accessed May 16, 2025,
    <https://tethys.pnnl.gov/sites/default/files/publications/Alerstam%20et%20al.%202007.pdf>

[^8]: Recent Experimental Data on the Energy Costs of Avian Flight Call for a Revision
    of Optimal Migration Theory.
    - BioOne, accessed May 16, 2025,
      <https://bioone.org/journals/the-auk/volume-127/issue-1/auk.2009.09012/Recent-Experimental-Data-on-the-Energy-Costs-of-Avian-Flight/10.1525/auk.2009.09012.full>

[^9]: Flight speeds among bird species: allometric and phylogenetic effects - PubMed,
    accessed May 16, 2025, <https://pubmed.ncbi.nlm.nih.gov/17645390/>

[^10]: Speed and altitude of bird flight (with notes on other animals) - ResearchGate,
    accessed May 16, 2025,
    <https://www.researchgate.net/publication/229716306_Speed_and_altitude_of_bird_flight_with_notes_on_other_animals>

[^11]: Flight Speeds among Bird Species: Allometric and Phylogenetic Effects | PLOS
    Biology, accessed May 16, 2025,
    <https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.0050197>

[^12]: The gliding speed of migrating birds: Slow and safe or fast and risky?
    - ResearchGate, accessed May 16, 2025,
      <https://www.researchgate.net/publication/260912339_The_gliding_speed_of_migrating_birds_Slow_and_safe_or_fast_and_risky>

[^13]: sora.unm.edu, accessed May 16, 2025,
    <https://sora.unm.edu/sites/default/files/journals/nab/v034n05/p00738-p00741.pdf>

[^14]: SPEED OF BIRD FLIGHT, accessed May 16, 2025,
    <https://sora.unm.edu/sites/default/files/journals/auk/v050n03/p0309-p0316.pdf>

[^15]: Analysis of mixtures of birds and insects in weather radar profile …, accessed
    May 16, 2025,
    <https://academic.oup.com/condor/advance-article/doi/10.1093/ornithapp/duaf020/8051150>

[^16]: Evaluation of methods to estimate nocturnal bird migration activity: A comparison
    of radar and nocturnal flight call monitoring in the American West - Oxford
    Academic, accessed May 16, 2025,
    <https://academic.oup.com/condor/article/127/1/duae062/7863690>

[^17]: dspace.stir.ac.uk, accessed May 16, 2025,
    <https://dspace.stir.ac.uk/bitstream/1893/306/1/park2001b.pdf>

[^18]: Air speeds of migrating birds observed by ornithodolite and …, accessed May 16,
    2025, <https://pmc.ncbi.nlm.nih.gov/articles/PMC3730693/>

[^19]: Analysis of mixtures of birds and insects in weather radar data …, accessed May
    16, 2025, <https://www.biorxiv.org/content/10.1101/2024.07.17.601450v1.full-text>

[^20]: Ibis (2001) 143, 178-204 - Flight characteristics of ... - ResearchGate, accessed
    May 16, 2025,
    <https://www.researchgate.net/profile/Bruno-Bruderer-2/publication/227621013_Flight_characteristics_of_birds_I_Radar_measurements_of_speeds/links/5cb97ea5299bf120976fa38a/Flight-characteristics-of-birds-I-Radar-measurements-of-speeds.pdf>

[^21]: sora.unm.edu, accessed May 16, 2025,
    <https://sora.unm.edu/sites/default/files/journals/jfo/v049n02/p0108-p0112.pdf>

[^22]: Flight kinematics of the barn swallow (Hirundo Rustica) over a wide range of
    speeds in a wind tunnel - ResearchGate, accessed May 16, 2025,
    <https://www.researchgate.net/publication/11813382_Flight_kinematics_of_the_barn_swallow_Hirundo_Rustica_over_a_wide_range_of_speeds_in_a_wind_tunnel>

[^23]: Wake structure and wingbeat kinematics of a house-martin Delichon …, accessed May
    16, 2025, <https://royalsocietypublishing.org/doi/10.1098/rsif.2007.0215>

[^24]: Diurnal and crepuscular activity during fall migration for four species of aerial
    foragers | Request PDF - ResearchGate, accessed May 16, 2025,
    <https://www.researchgate.net/publication/341895090_Diurnal_and_crepuscular_activity_during_fall_migration_for_four_species_of_aerial_foragers>

[^25]: Coordinated Behaviour in Pigeon Flocks | PLOS One, accessed May 16, 2025,
    <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0140558>

[^26]: Purple Martin | Ellis Nature Centre, accessed May 16, 2025,
    <https://ellisnaturecentre.ca/purple-martin/>

[^27]: Tracking Purple Martin Migration to Brazil, and Back!, accessed May 16, 2025,
    <https://www.purplemartin.org/uploads/media/18-2-geolocators-345.pdf>

[^28]: Ecological Causes and Consequences of Intratropical Migration in
    Temperate-Breeding Migratory Birds\* | Request PDF - ResearchGate, accessed May 16,
    2025,
    <https://www.researchgate.net/publication/305362454_Ecological_Causes_and_Consequences_of_Intratropical_Migration_in_Temperate-Breeding_Migratory_Birds>

[^29]: Why Measuring Air Speed at Bird Level May Not Be Advisable - Poultry Ventilation,
    accessed May 16, 2025,
    <https://www.poultryventilation.com/resources/why-measuring-air-speed-at-bird-level-may-not-be-advisable/>

[^30]: http://www.epj-conferences.org, accessed May 16, 2025,
    <https://www.epj-conferences.org/articles/epjconf/pdf/2016/09/epjconf_efm2016_01001.pdf>

[^31]: Aerodynamic efficiency explains flapping strategies used by birds - PNAS,
    accessed May 16, 2025, <https://www.pnas.org/doi/10.1073/pnas.2410048121>

[^32]: Bird wings inspire new approach to flight safety - Princeton Engineering,
    accessed May 16, 2025,
    <https://engineering.princeton.edu/news/2024/10/28/bird-wings-inspire-new-approach-flight-safety>

[^33]: Aerodynamic efficiency explains flapping strategies used by birds | Request PDF,
    accessed May 16, 2025,
    <https://www.researchgate.net/publication/385596648_Aerodynamic_efficiency_explains_flapping_strategies_used_by_birds>

[^34]: Aerodynamic efficiency explains flapping strategies used by birds …, accessed May
    16, 2025, <https://www.pnas.org/doi/full/10.1073/pnas.2410048121>

[^35]: Flight Speeds among Bird Species: Allometric and Phylogenetic Effects - PLOS,
    accessed May 16, 2025,
    <https://journals.plos.org/plosbiology/article/file?id=10.1371/journal.pbio.0050197&type=printable>

[^36]: (PDF) Flight Speeds among Bird Species: Allometric and Phylogenetic Effects,
    accessed May 16, 2025,
    <https://www.researchgate.net/publication/6194023_Flight_Speeds_among_Bird_Species_Allometric_and_Phylogenetic_Effects>

[^37]: Moving at the speed of flight: dabbling duck-movement rates and the relationship
    with electronic tracking interval - ResearchGate, accessed May 16, 2025,
    <https://www.researchgate.net/publication/335837894_Moving_at_the_speed_of_flight_dabbling_duck-movement_rates_and_the_relationship_with_electronic_tracking_interval>

[^38]: Moving at the speed of flight: dabbling duck-movement rates and the relationship
    with electronic tracking interval - CSIRO Publishing, accessed May 16, 2025,
    <https://www.publish.csiro.au/wr/pdf/WR19028>

[^39]: Diving-Flight Aerodynamics of a Peregrine Falcon (Falco peregrinus …, accessed
    May 16, 2025, <https://pmc.ncbi.nlm.nih.gov/articles/PMC3914994/>

[^40]: What is the fastest creature on Earth?
    | Unraveling the mysteries of birds Vol.3 | Bird Column, accessed May 16, 2025,
    <https://global.canon/en/environment/bird-branch/bird-column/kids3/>

[^41]: What is the fastest creature on Earth?
    | Unraveling the mysteries of …, accessed May 16, 2025,
    <https://global.canon/en/environment/bird-branch/bird-column/kids3/index.html>

[^42]: en.wikipedia.org, accessed May 16, 2025,
    <https://en.wikipedia.org/wiki/Peregrine_falcon#:~:text=Some%20sources%20state%20that%20it,%2Fh%20(242%20mph).>

[^43]: (PDF) Stoops of peregrine falcon Falco peregrinus and barbary falcon F.
    pelegrinoides, accessed May 16, 2025,
    <https://www.researchgate.net/publication/292549918_Stoops_of_peregrine_falcon_Falco_peregrinus_and_barbary_falcon_F_pelegrinoides>

[^44]: White-throated needletail - Wikipedia, accessed May 16, 2025,
    <https://en.wikipedia.org/wiki/White-throated_needletail>

[^45]: 40,000 km between Japan and Australia!
    The migratory route of the white-throated needletail, accessed May 16, 2025,
    <https://healthist.net/en/biology/2450/>

[^46]: White-throated Needletail - The Australian Museum, accessed May 16, 2025,
    <https://australian.museum/learn/animals/birds/white-throated-needletail/>

[^47]: Common swift - Wikipedia, accessed May 16, 2025,
    <https://en.wikipedia.org/wiki/Common_swift>

[^48]: Gliding for a free lunch: biomechanics of foraging flight in common swifts ( Apus
    apus )., accessed May 16, 2025,
    <https://typeset.io/pdf/gliding-for-a-free-lunch-biomechanics-of-foraging-flight-in-75upey3p79.pdf>

[^49]: How swift are swifts Apus apus ? | Request PDF - ResearchGate, accessed May 16,
    2025,
    <https://www.researchgate.net/publication/248825045_How_swift_are_swifts_Apus_apus>

[^50]: The Speed of Birds | Bird Watcher’s General Store, accessed May 16, 2025,
    <https://www.birdwatchersgeneralstore.com/the-speed-of-birds/>

[^51]: Western house martin - Wikipedia, accessed May 16, 2025,
    <https://en.wikipedia.org/wiki/Western_house_martin>

[^52]: Meet the Purple Martin - Sacramento Audubon Society, accessed May 16, 2025,
    <https://www.sacramentoaudubon.org/kids-corner/meet-the-purple-martin-1>

[^53]: Progne subis (purple martin) - Animal Diversity Web, accessed May 16, 2025,
    <https://animaldiversity.org/accounts/Progne_subis/>

[^54]: Flight Behavior of Individual Aerial Insectivores Revealed by Novel Altitudinal
    Dataloggers, accessed May 16, 2025,
    <https://www.researchgate.net/publication/328661412_Flight_Behavior_of_Individual_Aerial_Insectivores_Revealed_by_Novel_Altitudinal_Dataloggers>

