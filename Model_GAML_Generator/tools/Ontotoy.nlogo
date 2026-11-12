;; Extensions
;; ==========
extensions [array table]

;; to start with
; set pfile "parameterDefault10.txt"
; set pfile "parameterDefault9v2offtakev3landuse.txt"
; set pfile "parameterDefault9v2offtakev5landuse.txt"
; init2
; repeat 10 [ step]

;; Globals
;; =======
globals [
  ;; parameter file to open
  pFile
  ;; scenario file to open
  sFile
  ;; tracing
  trace?

  ;; initialization data read from file
  environment-data
  season-data
  biophysical-data
  zootechnical-data
  production-unit-data
  economic-data
  infrastructure-data

  ;; scenarization parameters
  clCropSurface
  clGrassSurface
  clForageSurface
  clSylvopastoralgSurface
  clSylvopastoralfSurface
  clAgroforestrySurface
  sharedMilkery?
  sharedSlaughterhouse?
  milkeryContribution
  slaughterContribution
  ;; global tables
  land-cover-colors
  land-covers
  production-unit-types
  ;; parameters
  plot-surface  ; normally fixed to 1 ha
  ;; common land
  ;; global season
  season-name     ; season name
  pluviometry     ; quantity of rain in l/ha/year
  season-index    ; the place in the season list
  season-sequence ; the list of season
  common-plots
  ;; initial water and nutrients
  initialWater
  ;; production-unit parameters
  production-unitNumber  ; number of production-units and for each production-unit:
  cropSurface            ; - its crop surface
  grassSurface           ; - its forage surface
  forageSurface          ; - its grass surface
  sylvopastoralgSurface  ; - its grass sylvopastoral surface
  sylvopastoralfSurface  ; - its forage sylvopastoral surface
  agroforestrySurface    ; - its agroforestry surface
  walk                   ; - walk per day
  initialCash            ; - the initial cash level
  fertilizer             ; - bought fertilizer
  cropFertilization      ;   - part for crop
  grassFertilization     ;   - part for grass
  forageFertilization    ;   - part for forage
  concentrate            ; - part of concentrate feed
  concentrateMax         ; - max part of concentrate feed
  pasture                ; - part of pasture feed
  forage                 ; - part of forage feed
  nleaf                  ; - part of natural leaf feed
  cleaf                  ; - part of cultivated leaf feed
  residue                ; - part of crop residue feed
  rawMilk                ; - part of sold raw milk
  processedMilk          ; - part of sold processed milk
  milkeryMilk            ; - part of milk sold to the milkery
  liveAnimal             ; - part of sold animals
  carcass                ; - part of sold carcasses
  shAnimal               ; - part of sanimals sold to the slaughterhouse
  ;; biophysical parameters
  tree2lbiomass ; leaf biomass per tree
  tree2tbiomass ; ligneous biomass per tree
  tbiomass2C    ; from ligneous biomass to carbon stock
  ewc           ; contribution of evaporation to water change
  bwc           ; contribution of biomass to water change
  ;; N dynamics
  Nfixation     ; atmospheric N fixation rate
  glbiomass2N   ; grass litter to nitrogen        (kgN/kgDM)
  flbiomass2N   ; forage litter to nitrogen       (kgN/kgDM)
  llbiomass2N   ; leaves litter to nitrogen       (kgN/kgDM)
  livestock2N   ; livestock dung to nitrogen      (kgN/kgDM)
  ;; C dynamics
  c-emission    ; spontaneous emission of soilC (%kgC/year)
  glbiomass2C   ; grass litter to carbon        (kgC/kgDM)
  flbiomass2C   ; forage litter to carbon       (kgC/kgDM)
  llbiomass2C   ; leaves litter to carbon       (kgC/kgDM)
  livestock2C   ; livestock dung to carbon      (kgC/kgDM)
  gmineralization  ; grass mineralization proportion (%)
  fmineralization  ; forage mineralization proportion(%)
  lmineralization  ; leaf mineralization proportion  (%)
  dmineralization  ; dung mineralization proportion  (%)
  c2co2         ; C to CO2 conversion factor (kgCO2/kgC)
  ;; gaz emission dynamics
  f1  ; kg CH4 per kg of metabolic weight
  f2  ; kg CH4 per kg of ingested OM
  ; CO2 equivalence
  co2
  ch4toco2  ; equivalence of methan
  n2otoco2  ; equivalence of nitrogen
  ;; zootechnical parameters
  ; animal maintenance
  UFLm      ; energy need per kg of animal weight and day   (kgCal/kg/day)
  Nm        ; nitrogen need per kg of animal weight and day (kgN/kg/day)
  ; others
  relative-biomass-need   ; the needed biomass per 100kg for animals
  metabolic-weight-ratio  ; ration of metabolic weight on total weight
  ;; global demographic data
  male-structure   ; male age class description
  female-structure ; female age class description
  male-max         ; male max age
  female-max       ; female max age
  milking-min-age  ; the age min for milking
  milking-max-age  ; the age max for milking
  ;; arrays from 0 to max age to manage demography dynamics
  male-weight         ; male weight vector
  male-mortality      ; male mortality vector
  male-slaughtering   ; male slaughtering vector
  male-size           ; male initial number
  female-weight       ; female weight vector
  female-mortality    ; female mortality vector
  female-slaughtering ; female slaughtering vector
  female-fecundity    ; female fecundity vector
  female-size         ; female initial number
  ; feed properties per source of feed
  feed-data

  adult-maintenance-ufl  ; UFL needed to maintain an adult
  young-maintenance-ufl  ; UFL needed to maintain a young
  adult-maintenance-n    ; nitrogenic matter needed to maintain an adult
  young-maintenance-n    ; nitrogenic matter needed to maintain a young
  UFL2liter              ; UFL needed for a liter of milch
  literMax               ; maximum possible production per cow
  N2liter                ; nitrogen needed for a liter of milch
  UFLw                   ; UFL needed for walking (per m)
  sp                     ; % metabolic energy need for chewing
  ; underfeeding behaviour
  rLimit
  dLimit
  rMortality
  dMortality
  ; manure gaz emission
  manure-ch4-emission
  manure-n2o-emission
  ; market data
  concentratePrice       ; $/kg
  fertilizerPrice ; $/kg
  milkPrice       ; $/l
  processedPrice  ; $/l
  diaryPrice      ; $/l
  cowPrice        ; $/head
  meatPrice       ; $/head
  shPrice         ; $/head
  ;; for display
  ; biomass limits
  maxWater
  maxNutrient
  maxC
  maxGBiomass
  maxLBiomass
  maxTBiomass
  maxDung
  ;; The indicators
  ;; ==============
  used-plots   ; the plots with a land-cover
  ; environmental
  average-gbiomass
  average-gbiomass-grass
  average-gbiomass-crop
  average-gbiomass-forage
  average-gbiomass-agroforestry
  average-gbiomass-sylvogpastoral
  average-gbiomass-sylvofpastoral
  average-lbiomass
  average-lbiomass-grass
  average-lbiomass-crop
  average-lbiomass-forage
  average-lbiomass-agroforestry
  average-lbiomass-sylvogpastoral
  average-lbiomass-sylvofpastoral
  average-tbiomass
  average-water
  average-nutrient
  average-fertilizer
  average-manure
  average-gliter
  average-lliter
  grass-livestock
  crop-livestock
  forage-livestock
  agroforestry-livestock
  sylvogpastoral-livestock
  sylvofpastoral-livestock
  ; the water and pollution at the runoff of the environment (kg of excess nutrient)
  total-c-sequestration
  total-plot-emission
  total-production-unit-emission
  average-domi2ch4
  ; production
  average-cattle ; total
  average-born
  average-male-born
  average-male-young
  average-male-subadult
  average-male-adult
  average-female-born
  average-female-young
  average-female-subadult
  average-female-adult
  average-death
  average-young-death
  average-subadult-death
  average-adult-death
  average-starved
  average-young-starved
  average-subadult-starved
  average-adult-starved
  average-killed
  average-young-killed
  average-subadult-killed
  average-adult-killed
  average-bought
  average-young-bought
  average-subadult-bought
  average-adult-bought
  average-old-male-killed
  average-old-female-killed
  average-old-killed
  average-live-sold
  average-carcass-sold
  average-sh-sold
  average-biomass-need
  average-pasture-need
  average-residue-need
  average-nleaf-need
  average-cleaf-need
  average-concentrate-need
  average-forage-need
  average-pasture-consumed
  average-residue-consumed
  average-nleaf-consumed
  average-cleaf-consumed
  average-forage-consumed
  average-cpasture-consumed
  average-cresidue-consumed
  average-cnleaf-consumed
  average-ccleaf-consumed
  average-cforage-consumed
  average-concentrate-consumed
  average-milk-production
  average-rmilk-sold
  average-pmilk-sold
  average-mmilk-sold
  average-amilk
  nb-cooperative
  average-production-ufl
  ; economy
  average-cash
  average-income
  average-rmilk-income
  average-rmeat-income
  average-tmilk-income
  average-tmeat-income
  average-expense
  average-residue-expense
  average-concentrate-expense
  average-fertiliser-expense
  average-membership-expense
  average-cow-expense
  average-balance
  ;; social
  nb-ss-employee
  nb-in-employee
  nb-cow-employee
  nb-employee
]

;; Environment structure
;; =====================
patches-own [
;; cover
  land-cover       ; either "production-unit", "waterOutput", "nothing" to which covers like "crop", "grass", etc. can be added
;; biomass dynamics
; state variables
  gbiomass         ; herbacious biomass (either grass or crop or forage)
  lbiomass         ; leaf biomass
  tbiomass         ; ligneous biomass
;; livestock dynamics
; state variables
  livestock        ; livestock pressure in animal-day per year
  dung             ; dung generated by the livestock
;; N dynamics
; state variables
  ;; nitrogen dynamics
  soil-n
  grass-n-input
  leaves-n-input
  dung-n-input
;; water dynamics
; state variables
  water            ; stock of water for biomass growth (rain, floor and underground water)
  water-growth     ; annual variation of water
;; carbon dynamics
; state variables
  soil-c           ; quantity of C in the soil
;; GHG dynamics
; state variables
  gaz-emission     ; annual gaz emission in kg of CO2
]

;; Entity structure
;; ================

breed [production-units production-unit]

production-units-own [
  ;; parameters
  plots              ; the owned plots
  ;; state variables
  males              ; vector of males per year
  females            ; vector of females per year
  ;; the need from each source of feed
  biomass-need
  pasture-need   ; non-cultivated grass
  forage-need    ; cultivated-grass
  nleaf-need     ; non-cultivated leaf
  cleaf-need     ; cultivated leaf
  residue-need   ; crop residue
  concentrate-need      ; concentrate
  ;; actual consumption from each source of feed
  pasture-consumed  ; private non-cultivated grass
  forage-consumed   ; private cultivated grass
  nleaf-consumed    ; private non-cultivated leaf
  cleaf-consumed    ; private cultivated leaf
  residue-consumed  ; private crop residue
  cpasture-consumed  ; common non-cultivated grass
  cforage-consumed   ; common cultivated grass
  cnleaf-consumed    ; common non-cultivated leaf
  ccleaf-consumed    ; common cultivated leaf
  cresidue-consumed  ; common crop residue
  concentrate-consumed     ; concentrate
  ;; bought fertilizer
  boughtFertiliser
  starved-prop      ; additional % of death from starving
  starved           ; death from starving (by age class)
  death             ; natural death (by age class)
  old-male-killed
  old-female-killed
  killed            ; total slaughtered (by age class)
  births            ; number of new borns
  bought            ; number of bought animals
  ;; production
  production-UFL    ; ufl usable for production
  milk-production   ; total milk production
  ;; economical data
  cash
  rmilk-income
  rmeat-income
  tmilk-income
  tmeat-income
  dmilk-income
  shmeat-income
  residue-expense
  concentrate-expense
  fertiliser-expense
  membership-expense
  cow-expense
  ;; gaz emission
  DOMI2CH4          ; for control !
  co2-emission
]

;; Structure access
;; ================

;; Cover descriptors from within patch

to-report cover-rain2gbiomass
  let parameters table:get-or-default land-covers land-cover []
  ifelse not empty? parameters [
    report item 0 parameters
  ][
    report 0
  ]
end

to-report cover-nb-trees
  let parameters table:get-or-default land-covers land-cover []
  ifelse not empty? parameters [
    report item 1 parameters
  ][
    report 0
  ]
end

to-report cover-gconsumable
  let parameters table:get-or-default land-covers land-cover []
  ifelse not empty? parameters [
    report item 2 parameters
  ][
    report 0
  ]
end

to-report cover-lconsumable
  let parameters table:get-or-default land-covers land-cover []
  ifelse not empty? parameters [
    report item 3 parameters
  ][
    report 0
  ]
end

to-report cover-soilC
  let parameters table:get-or-default land-covers land-cover []
  ifelse not empty? parameters [
    report item 4 parameters
  ][
    report 0
  ]
end

to-report cover-soilN
  let parameters table:get-or-default land-covers land-cover []
  ifelse not empty? parameters [
    report item 5 parameters
  ][
    report 0
  ]
end

to-report cover-kp
  let parameters table:get-or-default land-covers land-cover []
  ifelse not empty? parameters [
    report item 6 parameters
  ][
    report 0
  ]
end

to-report cover-maxN
  let parameters table:get-or-default land-covers land-cover []
  ifelse not empty? parameters [
    report item 7 parameters
  ][
    report 0
  ]
end

;; feed descriptors (absolute access)

to-report feed-kgDM2kgCal [feed] ; conversion to kgCal
  let parameters table:get-or-default feed-data feed []
  ifelse not empty? parameters [
    report item 0 parameters
  ][
    report 0
  ]
end

to-report feed-kgDM2gN [feed]    ; conversion to N
  let parameters table:get-or-default feed-data feed []
  ifelse not empty? parameters [
    report item 1 parameters
  ][
    report 0
  ]
end

to-report feed-OM [feed]         ; organic matter content (%)
  let parameters table:get-or-default feed-data feed []
  ifelse not empty? parameters [
    report item 2 parameters
  ][
    report 0
  ]
end

to-report feed-digestibility [feed] ; digestibility of OM (%)
  let parameters table:get-or-default feed-data feed []
  ifelse not empty? parameters [
    report item 3 parameters
  ][
    report 0
  ]
end

to-report feed-NDF [feed]        ; g of fiber per kgDM
  let parameters table:get-or-default feed-data feed []
  ifelse not empty? parameters [
    report item 3 parameters
  ][
    report 0
  ]
end

to-report feed-ME [feed]         ; metabolic energy (kgCal/kgDM)
  let parameters table:get-or-default feed-data feed []
  ifelse not empty? parameters [
    report item 4 parameters
  ][
    report 0
  ]
end

;; Various tests
;; =============
to test
end

;; Initialization
;; ==============
to init
  clear-all
  set trace? false
  ;; open file and read parameters
  file-open user-file
  parameters-read
  ;; init all the global parameters and tables and check consistency
  init-environment-parameters
  init-cattle-parameters
  init-production-units-parameters
  check-parameters
  ;; initializes the system
  system-init
  ;; display
  update-indicators
  update-view
  reset-ticks
end

to init2
  clear-all-plots
  clear-patches
  set trace? false
  ;; open file and read parameters
  file-open pFile
  parameters-read
  ;; init all the tables and check consistency
  init-seasons
  init-environment-parameters
  init-cattle-parameters
  init-production-units-parameters
  init-infrastructure-parameters
  ;; init all the globals check consistency
  check-parameters
  ;; initializes the system
  system-init
  ;; display
  update-indicators
  update-view
  reset-ticks
end

;; read the data from an already open file
to parameters-read
  let read []
  ;; init parameter data
  set environment-data     []
  set season-data          []
  set biophysical-data     []
  set zootechnical-data    []
  set production-unit-data []
  set economic-data        []
  set infrastructure-data  []
  ;; read content and put it somewhere
  loop [
    ifelse file-at-end? [
      file-close
      stop
    ] [
      set read file-read
      show read
      ;; for land cover definitions
      if first read = "Environment"    [ set environment-data (but-first read) ]
      ;; for season definitions
      if first read = "Season"         [ set season-data  (but-first read) ]
      ;; for biophysical parameters
      if first read = "Biophysics"     [ set biophysical-data  (but-first read) ]
      ;; for zootechnical parameters
      if first read = "Zootechnics"    [ set zootechnical-data  (but-first read) ]
      ;; for production-unit parameters
      if first read = "Farms"          [ set production-unit-data  (but-first read) ]
      ;; for economic parameters
      if first read = "Economics"      [ set economic-data  (but-first read) ]
      ;; for infrastructure parameters
      if first read = "Infrastructure" [ set infrastructure-data  (but-first read) ]
    ]
  ]
  ;; finished
end

to init-seasons
  set season-index    0
  set season-sequence read-from-string first season-data
  set season-data     but-first season-data
end

to init-environment-parameters
  ;; both patch descriptions and biophysical parameters
  ;; init land cover colors
  set land-cover-colors table:make
  table:put land-cover-colors "nothing"         white
  table:put land-cover-colors "production-unit" red
  table:put land-cover-colors "waterOutput"     blue
  ;; set land-cover table
  set land-covers table:make
  table:put land-covers "nothing"         [0 0 0 0 0 0 0 0 0]
  table:put land-covers "production-unit" [0 0 0 0 0 0 0 0 0]
  table:put land-covers "waterOutput"     [0 0 0 0 0 0 0 0 0]
  ;; set environment parameters
  ifelse not empty? environment-data [
    let max-xcor        item 0 environment-data
    let max-ycor        item 1 environment-data
    resize-world 0 max-xcor 0 max-ycor
    set plot-surface    item 2 environment-data
    set initialWater    item 3 environment-data
    set tree2lbiomass   item 4 environment-data
    set tree2tbiomass   item 5 environment-data
    set environment-data but-n 6 environment-data
    foreach environment-data [ x ->
      table:put land-covers       first x but-first but-first x
      table:put land-cover-colors first x first but-first x
    ]
  ][
    print "land cover definitions are missing!"
  ]
  ;; set biophysical parameters
  ifelse not empty? biophysical-data [
    set ewc             item 0  biophysical-data
    set bwc             item 1  biophysical-data
    set co2             item 2  biophysical-data
    set ch4toco2        item 3  biophysical-data
    set n2otoco2        item 4  biophysical-data
    set Nfixation       item 5  biophysical-data
    set c-emission      item 6  biophysical-data  ; spontaneous evolution of soilC (kgC/year)
    set glbiomass2N     item 7  biophysical-data  ; grass litter to nitrogen   (kgN/kgDM)
    set flbiomass2N     item 8  biophysical-data  ; forage litter to nitrogen  (kgN/kgDM)
    set llbiomass2N     item 9  biophysical-data  ; leaves litter to nitrogen  (kgN/kgDM)
    set livestock2N     item 10 biophysical-data  ; livestock dung to nitrogen (kgN/kgDM)
    set glbiomass2C     item 11 biophysical-data  ; grass litter to carbon   (kgC/kgDM)
    set flbiomass2C     item 12 biophysical-data  ; forage litter to carbon  (kgC/kgDM)
    set llbiomass2C     item 13 biophysical-data  ; leaves litter to carbon  (kgC/kgDM)
    set livestock2C     item 14 biophysical-data  ; livestock dung to carbon (kgC/kgDM)
    set gmineralization item 15 biophysical-data  ; grass mineralization proportion (%)
    set fmineralization item 16 biophysical-data  ; forage mineralization proportion(%)
    set lmineralization item 17 biophysical-data  ; leaf mineralization proportion  (%)
    set dmineralization item 18 biophysical-data  ; dung mineralization proportion  (%)
    set C2CO2           item 19 biophysical-data  ; C to CO2 conversion factor (kgCO2/kgC)
  ][
    print "biophysical parameters are missing!"
  ]
end

to init-production-units-parameters
  ;; both production unit descriptions and economic parameters
  ifelse not empty? production-unit-data [
    set production-unitNumber  item 0 production-unit-data
    ; land structure
    set cropSurface            item 1 production-unit-data
    set agroforestrySurface    item 2 production-unit-data
    set grassSurface           item 3 production-unit-data
    set forageSurface          item 4 production-unit-data
    set sylvopastoralgSurface  item 5 production-unit-data
    set sylvopastoralfSurface  item 6 production-unit-data
    ; livestock mobility
    set walk                   item 7 production-unit-data
    ; initial cash
    set initialCash            item 8 production-unit-data
    ; fertilization strategy
    set fertilizer             item 9 production-unit-data
    set cropFertilization      item 10 production-unit-data
    set grassFertilization     item 11 production-unit-data
    set forageFertilization    item 12 production-unit-data
    ; feeding strategy
    set concentrate            item 13 production-unit-data
    set concentrateMax         item 14 production-unit-data
    set pasture                item 15 production-unit-data
    set nleaf                  item 16 production-unit-data
    set cleaf                  item 17 production-unit-data
    set residue                item 18 production-unit-data
    set forage                 item 19 production-unit-data
    ; commercialization strategy
    set rawMilk                item 20 production-unit-data
    set processedMilk          item 21 production-unit-data
    set milkeryMilk            item 22 production-unit-data
    set liveAnimal             item 23 production-unit-data
    set carcass                item 24 production-unit-data
    set shAnimal               item 25 production-unit-data
    ;; the cattle structure is setup in the init-cattle-parameters
  ][
    print "production-unit parameters are missing!"
  ]
  ifelse not empty? economic-data [
    set concentratePrice       item 0 economic-data ; $/kg
    set fertilizerPrice item 1 economic-data ; $/kg
    set milkPrice       item 2 economic-data ; $/l
    set processedPrice  item 3 economic-data ; $/l
    set diaryPrice      item 4 economic-data ; $/l
    set cowPrice        item 5 economic-data ; $/head
    set meatPrice       item 6 economic-data ; $/head
    set shPrice         item 7 economic-data ; $/head
  ][
    print "economic parameters are missing!"
  ]
end

to init-cattle-parameters
  ;; set zootechnical parameters
  ifelse not empty? zootechnical-data [
    set relative-biomass-need  item 0 zootechnical-data
    set metabolic-weight-ratio item 1 zootechnical-data
    set UFL2liter              item 2 zootechnical-data
    set literMax               item 3 zootechnical-data
    set N2liter                item 4 zootechnical-data
    set manure-ch4-emission    item 5 zootechnical-data
    set manure-n2o-emission    item 6 zootechnical-data
    set f1                     item 7 zootechnical-data
    set f2                     item 8 zootechnical-data
    set UFLm                   item 9 zootechnical-data ; kCal maintenance need
    set UFLw                   item 10 zootechnical-data ; kCal walk need
    set Nm                     item 11 zootechnical-data ; nitrogen maintenance need
    set sp                     item 12 zootechnical-data ; % metabolic energy need for shewing
    set rLimit                 item 13 zootechnical-data ; reserve limit
    set dLimit                 item 14 zootechnical-data ; starving limit
    set rMortality             item 15 zootechnical-data ; reserve mortality increase
    set dMortality             item 16 zootechnical-data ; starving mortality increase

    set feed-data table:make
    set zootechnical-data item 17 zootechnical-data
    ifelse first zootechnical-data = "inputs" [
      foreach but-first zootechnical-data [ x ->
        table:put feed-data first x but-first x
      ]
    ][
      print "feed descriptions are missing!"
    ]

    ;; cattle structure initialization from production-unit-data
    ; descriptor table
    let male-classes but-first item 26 production-unit-data
    set male-structure table:make
    set male-max -1
    foreach male-classes [ x ->
      ifelse first but-first x = male-max + 1 [
        table:put male-structure first x but-first x
        set male-max item 2 x
      ][
        error (word "male age class " first x " is not contiguous!")
      ]
    ]
    let female-classes but-first item 27 production-unit-data
    set female-structure table:make
    set female-max -1
    foreach female-classes [ x ->
      ifelse first but-first x = female-max + 1 [
        table:put female-structure first x but-first x
        set female-max item 2 x
      ][
         error (word "female age class " first x " is not contiguous!")
     ]
    ]
    print (word "male max: " male-max " female max: " female-max)
    ; null list for array initialization
    let male-lst n-values (male-max + 1) [0]
    set male-weight         array:from-list male-lst
    set male-mortality      array:from-list male-lst
    set male-slaughtering   array:from-list male-lst
    set male-size           []
    foreach table:keys male-structure [ key ->
      let descr table:get male-structure key
      let low  item 0 descr
      let high item 1 descr
      let width high - low + 1
      while [low <= high] [
        array:set male-weight       low item 2 descr
        array:set male-mortality    low item 3 descr
        array:set male-slaughtering low item 4 descr
        set male-size lput (item 5 descr / width) male-size
        set low       low + 1
      ]
    ]
    print (word "Male population:   " male-size)
    let female-lst n-values (female-max + 1) [0]
    set female-weight       array:from-list female-lst
    set female-mortality    array:from-list female-lst
    set female-slaughtering array:from-list female-lst
    set female-size         []
    set female-fecundity    array:from-list female-lst
    set milking-min-age  female-max
    set milking-max-age  0
    foreach table:keys female-structure [ key ->
      let descr table:get female-structure key
      let low  item 0 descr
      let high item 1 descr
      let width high - low + 1
      while [low <= high] [
        array:set female-weight       low item 2 descr
        array:set female-mortality    low item 3 descr
        array:set female-slaughtering low item 4 descr
        set female-size lput (item 5 descr / width) female-size
        let fecundity item 6 descr
        array:set female-fecundity low fecundity
        if fecundity > 0 [
          set milking-min-age min (list milking-min-age low)
          set milking-max-age max (list milking-max-age high)
        ]
        set low low + 1
      ]
    ]
    print (word "Female population: " female-size)
    print (word "total:             " (reduce + male-size + reduce + female-size))
  ][
    print "zootechnical parameters are missing!"
  ]
end

to init-infrastructure-parameters
  ifelse not empty? infrastructure-data [
    set clCropSurface           item 0 infrastructure-data
    set clAgroforestrySurface   item 1 infrastructure-data
    set clGrassSurface          item 2 infrastructure-data
    set clForageSurface         item 3 infrastructure-data
    set clSylvopastoralgSurface item 4 infrastructure-data
    set clSylvopastoralfSurface item 5 infrastructure-data
    set sharedMilkery?          item 6 infrastructure-data
    set sharedSlaughterhouse?   item 7 infrastructure-data
    set milkeryContribution     item 8 infrastructure-data
    set slaughterContribution   item 9 infrastructure-data
  ][
    print "infrastructure parameters are missing!"
  ]
end

to check-parameters
  if cropFertilization + grassFertilization + forageFertilization != 100 [
    error "grass, forage and crop fertilization parameters should sum to 100%"
  ]
  if concentrate + residue + pasture + nleaf + cleaf + forage != 100 [
    error "concentrate, residue, pasture, natural and cultivated leaf, forage source of concentrate should sum to 100%"
  ]
end

to system-init
  ;; initialize the system
  ;; 1) compute the necessary number of plots and resize
  let totalFarmSurface cropSurface + grassSurface + forageSurface + agroforestrySurface + sylvopastoralgSurface + sylvopastoralfSurface
  let totalCommonSurface clCropSurface + clGrassSurface + clForageSurface + clAgroforestrySurface + clSylvopastoralgSurface + clSylvopastoralfSurface
  ;; each production-unit is drawn by the circle of its plots whose radius is
  let farmRadius max list 10 (ceiling sqrt (totalFarmSurface / pi))
  ;; the production-unit are regularly spread on the environment in a number of lines and columns that are
  let nbFarmPerLineCol ceiling sqrt production-unitNumber
  ;; hence the number of patches on lines and columns are
  let nbLineCol max list 50 (nbFarmPerLineCol * farmRadius * 2)
  ;; of which total surface is
  let totalSurface nbLineCol * nbLineCol
  ;; of which free surface (not production-unit surface) is
  let remainingSurface totalSurface - totalFarmSurface * production-unitNumber
  ;; if not enough for common land, extend the number of lines
  let additionalLines 0
  if remainingSurface < totalCommonSurface [
    set additionalLines ceiling ((totalCommonSurface - remainingSurface) / nbLineCol)
  ]
  show additionalLines
  resize-world 0 nbLineCol 0 (nbLineCol + additionalLines)
  ;; 2) initializes the season
  climate-choose-season
  ;; 3) set everything to "nothing" cover
  ask patches [
    patch-init "nothing"
  ]
  ;; 4) place the waterOutput
;  ask patch (world-width / 2) (world-height - 1) [
;   patch-init "waterOutput"
;  ]
  ;; 5) create and place the production-units
  set-default-shape production-units "house"
  let farmCol  0     ; counts up the production-unit columns (left to right)
  let farmLine 1     ; counts up the production-unit line (up to bottom)
  repeat production-unitNumber [ ; repeats for the number of production-unit
    set farmCol farmCol + 1          ; increment colmun
    if farmCol > nbFarmPerLineCol [  ; wrap to the next line
      set farmCol 1
      set farmLine FarmLine + 1
    ]
    let posx (farmCol * farmRadius * 2 - farmRadius)
    let posy (farmLine * farmRadius * 2 - farmRadius)
    ask patch posx posy [
      patch-init "production-unit"
    ]
    create-production-units 1 [
      setxy posx posy
      production-unit-init totalFarmSurface farmRadius
    ]
  ]
  ;; 6) populate the common land
  common-land-init
  ;; 7) records the plots with a cultivated land-cover
  set used-plots patches with [land-cover != "nothing" and land-cover != "farm"]
  ;; 8) reset-synchronous-variables
  reset-synchronous-state-variables
end

to patch-init [cover]
  ;; initialize a patch with a given cover
  set land-cover cover
  ;; each cover is defined by its quantity of consumable and not consumable biomass
;  let parameters table:get-or-default land-covers cover []
;  if not empty? parameters [
;    set rain2gbiomass  item 0 parameters ; kgDM/l
;    set nb-trees       item 1 parameters * plot-surface ; nb trees
;    set gconsumable    item 2 parameters ; %
;    set lconsumable    item 3 parameters ; %
;    set soil-c         item 4 parameters * plot-surface ; tC
;    set Nstock         item 5 parameters ; kgN/ha
;    set soil-N         Nstock
;    set kp             item 6 parameters
;    set Nmax           item 7 parameters ; kgN/ha
;  ]
  set soil-c cover-soilC * plot-surface
  set soil-N cover-soilN
  ;; other initial values
  if-else cover = "empty" [
    set water    0
  ][
    set water      initialWater    * plot-surface ; l
  ]
  set gaz-emission 0
  ;; induced values
  patch-compute-biomass
end

to common-land-init
  ;; initialize the shared land with the requested covers
  let cropCount  clCropSurface            ; count of crop plots to create
  let grassCount clGrassSurface           ; count of grass plots to create
  let forageCount clForageSurface         ; count of grass plots to create
  let agroCount  clAgroforestrySurface    ; count of agroforestry plots to create
  let sylvogCount clSylvopastoralgSurface ; count of sylvopatoral plots to create
  let sylvofCount clSylvopastoralfSurface ; count of sylvopatoral plots to create
  set common-plots []                   ; the shared plots
  ;; browse plots from top-right corner of the environment
  foreach sort-on [distance patch max-pxcor max-pycor] patches [
    aPlot ->
    if [land-cover] of aPlot = "nothing" [
      ifelse cropCount > 0 [           ; create the crop plots
        set cropCount cropCount - 1
        ask aPlot [patch-init "crop"]
        set common-plots fput aPlot common-plots
      ][
        ifelse grassCount > 0 [        ; create the grass plots
          set grassCount grassCount - 1
          ask aPlot [patch-init "grass"]
          set common-plots fput aPlot common-plots
        ][
          ifelse forageCount > 0 [        ; create the forage plots
            set forageCount forageCount - 1
            ask aPlot [patch-init "grass"]
            set common-plots fput aPlot common-plots
          ][
            ifelse agroCount > 0 [      ; create the agroforestry plots
              set agroCount agroCount - 1
              ask aPlot [patch-init "agroforestry"]
              set common-plots fput aPlot common-plots
            ][
              ifelse sylvogCount > 0 [   ; create the grass sylvopastoral plots
                set sylvogCount sylvogCount - 1
                ask aPlot [patch-init "sylvopastoralg"]
                set common-plots fput aPlot common-plots
              ][
                ifelse sylvofCount > 0 [   ; create the forage sylvopastoral plots
                  set sylvofCount sylvofCount - 1
                  ask aPlot [patch-init "sylvopastoralf"]
                  set common-plots fput aPlot common-plots
                ][
                  ;; all done
                ]
              ]
            ]
          ]
        ]
      ]
    ]
  ]
  set common-plots patch-set common-plots ; converts to agentset for convenience
end

to production-unit-init [totalSurface radius]
  ;; shape first
  set size 1
  set color white
  set label-color black
  ;; get the neighbourhood plots
  let possiblePlots patches in-radius radius
  ;; initialize the counters like above
  let cropCount  cropSurface
  let grassCount grassSurface
  let forageCount forageSurface
  let agroCount  agroforestrySurface
  let sylvogCount sylvopastoralgSurface
  let sylvofCount sylvopastoralfSurface
  set plots lput patch-here []    ; initialize the plot list
  ;; browse plots around the production-unit
  foreach sort-on [distance myself] possiblePlots [
    aPlot ->
    if [land-cover] of aPlot = "nothing" [
      ifelse cropCount > 0 [           ; create the crop plots
        set cropCount cropCount - 1
        ask aPlot [patch-init "crop"]
        set plots fput aPlot plots
      ][
        ifelse grassCount > 0 [        ; create the grass plots
          set grassCount grassCount - 1
          ask aPlot [patch-init "grass"]
          set plots fput aPlot plots
        ][
          ifelse forageCount > 0 [        ; create the forage plots
            set forageCount forageCount - 1
            ask aPlot [patch-init "grass"]
            set plots fput aPlot plots
          ][
            ifelse agroCount > 0 [      ; create the agroforestry plots
              set agroCount agroCount - 1
              ask aPlot [patch-init "agroforestry"]
              set plots fput aPlot plots
            ][
              ifelse sylvogCount > 0 [   ; create the grass sylvopastoral plots
                set sylvogCount sylvogCount - 1
                ask aPlot [patch-init "sylvopastoralg"]
                set plots fput aPlot plots
              ][
                ifelse sylvofCount > 0 [   ; create the forage sylvopastoral plots
                  set sylvofCount sylvofCount - 1
                  ask aPlot [patch-init "sylvopastoralf"]
                  set plots fput aPlot plots
                ][
                  ;; all done
                ]
              ]
            ]
          ]
        ]
      ]
    ]
  ]
  set plots patch-set plots ; converts to agentset for convenience
  ;; cattle demographic structure initialization
  set males   array:from-list male-size    ;; male population per age
  set females array:from-list female-size  ;; female population per age
  ;; needs
  set biomass-need         0
  set pasture-need         0
  set forage-need          0
  set nleaf-need           0
  set cleaf-need           0
  set residue-need         0
  set concentrate-need     0
  ;; consumption on private land
  set pasture-consumed     0
  set forage-consumed      0
  set nleaf-consumed       0
  set cleaf-consumed       0
  set residue-consumed     0
  ;; consumption on common land
  set cpasture-consumed    0
  set cforage-consumed     0
  set cnleaf-consumed      0
  set ccleaf-consumed      0
  set cresidue-consumed    0
  ;; concentrate consumption
  set concentrate-consumed 0
  ;; demographic variations
  ;; - out
  set starved-prop         0
  set starved              table:make
  set death                table:make
  set old-male-killed      0
  set old-female-killed    0
  set killed               table:make
  ;; - in
  set births               0
  set bought               table:make
  ;; milk production
  set production-UFL       0
  set milk-production      0
  ;; income
  set rmilk-income         0
  set rmeat-income         0
  set tmilk-income         0
  set tmeat-income         0
  set dmilk-income         0
  set shmeat-income        0
  ;; expenses
  set residue-expense      0
  set concentrate-expense  0
  set fertiliser-expense   0
  set membership-expense   0
  set cow-expense          0
  ;; gaz emission
  set DOMI2CH4             0
  set co2-emission         0
end

;; Dynamics
;; ========

;; 1) general scheduling
to step
  print (word ticks ": new year")
  reset-synchronous-state-variables
  environment-update-nitrogen
  print "1) fertilization"
  ask production-units [
    production-unit-decide-fertilization
  ]
  print "2) compute biomass"
  environment-compute-biomass
  print "3) consumption"
  ask production-units [
    production-unit-cattle-feed      ; computes the ingested quantities
  ]
  print "4) compute gaz/milk/meat production"
  ask production-units [
    production-unit-update-gaz-emission  ; resulting gaz-emission
    production-unit-transformation       ; computes the outcome of ingested quantities: death if not enough or milk if enough
    production-unit-sell-milk            ; milk selling strategy
    production-unit-grow-cattle          ; meat production strategy
    production-unit-sell-meat            ; meat selling strategy
  ]
  print "5) update available water, C contribution and GHG emission"
  environment-update-water
  environment-update-carbon
  environment-update-gaz-emission
  update-indicators
  update-view
  print "6) decide season for next year"
  climate-choose-season
  tick
end

to reset-synchronous-state-variables
  ;; reset patch indicators
  ask patches [
    set livestock       0  ; no livestock pressure this year yet
    set dung            0  ; no dung yet
    set gaz-emission    0  ; reset gaz emission
  ]
  ;; reset production-unit indicators
  ask production-units [
    ;; needs
    set biomass-need         0
    set pasture-need         0
    set forage-need          0
    set nleaf-need           0
    set cleaf-need           0
    set residue-need         0
    set concentrate-need     0
    ;; consumption on private land
    set pasture-consumed     0
    set forage-consumed      0
    set nleaf-consumed       0
    set cleaf-consumed       0
    set residue-consumed     0
    ;; consumption on common land
    set cpasture-consumed    0
    set cforage-consumed     0
    set cnleaf-consumed      0
    set ccleaf-consumed      0
    set cresidue-consumed    0
    ;; concentrate consumption
    set concentrate-consumed 0
    ;; demographic variations
    set starved-prop         0
    table:put starved "young"    0
    table:put starved "subadult" 0
    table:put starved "adult"    0
    table:put death   "young"    0
    table:put death   "subadult" 0
    table:put death   "adult"    0
    table:put killed  "young"    0
    table:put killed  "subadult" 0
    table:put killed  "adult"    0
    set old-male-killed      0
    set old-female-killed    0
    set births               0
    table:put bought  "young"    0
    table:put bought  "subadult" 0
    table:put bought  "adult"    0
    ;; milk production
    set production-UFL       0
    set milk-production      0
    ;; income
    set rmilk-income         0
    set rmeat-income         0
    set tmilk-income         0
    set tmeat-income         0
    set dmilk-income         0
    set shmeat-income        0
    ;; expenses
    set residue-expense      0
    set concentrate-expense  0
    set fertiliser-expense   0
    set membership-expense   0
    set cow-expense          0
    ;; gaz emission
    set DOMI2CH4             0
    set co2-emission         0
  ]
end

;; 2) season dynamics
to climate-choose-season
  ifelse empty? season-sequence [
    ;; choose randomly a season
    let season one-of season-data
    set season-name first season
    set pluviometry item 1 season
  ][
    set season-name item season-index season-sequence
    let season find season-name season-data
    set pluviometry item 1 season
    set season-index (season-index + 1) mod length season-sequence
  ]
end

to-report find [name lst]
  let cnt 0
  while [cnt < length lst] [
    if first item cnt lst = name [ report item cnt lst ]
    set cnt cnt + 1
  ]
  report nobody
end

;; 3) environment dynamics
to environment-compute-biomass
  ask used-plots [patch-compute-biomass]
end

to environment-update-nitrogen
  ask used-plots [patch-update-nitrogen]
end

to environment-update-water
  ask used-plots [patch-update-water]
end

to environment-update-carbon
  ask used-plots [patch-update-carbon]
end

to environment-update-gaz-emission
  ask used-plots [patch-update-gaz-emission]
end

;; 4) patch dynamics

;; to be called after nutrient update and fertilization
to patch-compute-biomass
  if cover-rain2gbiomass > 0 [
    ;; available N is a biomass limiting factor
    ;; NRF = Nitrogen Reduction Factor
    let NRF soil-N * cover-kp / cover-maxN
    ;; grass/crop biomass
    set gbiomass pluviometry * cover-rain2gbiomass * plot-surface * NRF
  ]
  ;; leaf biomass
  set lbiomass cover-nb-trees * tree2lbiomass ;; !! should be dependent on the rain
  ;; ligneous biomass
  set tbiomass cover-nb-trees * tree2tbiomass ;; considered fixed
end

;; to be called at the end of the year
to patch-update-water
    ;; the water growth depends on evaporation (negatively), rain (positively) and biomass consumption
    set water-growth pluviometry * 10000 * (1 - ewc / 100) * plot-surface - (gbiomass + lbiomass + tbiomass) * bwc
    set water max list 0 (water + water-growth)
end

;; call at the begining of the year before fertilization and biomass update
to patch-update-nitrogen
  ;; leaves and dung
  set leaves-n-input (lbiomass * llbiomass2N * (1 - lmineralization / 100))
  set dung-n-input   (dung     * livestock2N * (1 - dmineralization / 100))
  ;; herbaceous biomass
  ifelse land-cover = "forage" or land-cover = "sylvopastoralf" [
    set grass-n-input (gbiomass * flbiomass2N * (1 - fmineralization / 100))
  ][ ;; either grass or crop
    set grass-n-input (gbiomass * glbiomass2N * (1 - gmineralization / 100))
  ]
  ;; update available N
  set soil-N cover-soilN * plot-surface + leaves-n-input + dung-n-input + grass-n-input
end

;; to be called at the end of the year
to patch-update-carbon
  ;; leaves and dung
  let soilCinput (lbiomass * llbiomass2C * (1 - lmineralization / 100)) +
                 (dung     * livestock2C * (1 - dmineralization / 100))
  ;; herbaceous biomass
  ifelse land-cover = "forage" or land-cover = "sylvopastoralf" [
    set soilCinput soilCinput + (gbiomass * flbiomass2C * (1 - fmineralization / 100))
  ][ ;; either grass or crop
    set soilCinput soilCinput + (gbiomass * glbiomass2C * (1 - gmineralization / 100))
  ]
  ;; the carbon in the patch (both soil and plants) increase each year
  set soil-c soil-c - (c-emission / 100) * soil-c + soilCinput
end

;; to be called at the end of the year
to patch-update-gaz-emission
  ;; compute direct gaz emission from manure
  set gaz-emission (dung * manure-ch4-emission * ch4toco2) + (dung * manure-n2o-emission * n2otoco2)
  ;; add C mineralization contribution from slow mineralization, leaves and dung ...
  set gaz-emission gaz-emission +
       (lbiomass  * llbiomass2C * lmineralization / 100 * c2co2) +
       (dung      * livestock2C * dmineralization / 100 * c2co2) +
       c-emission * soil-c * c2co2
  ;; ... and from herbaceous biomass
  ifelse land-cover = "forage" or land-cover = "sylvopastoralf" [
    set gaz-emission gaz-emission + (gbiomass * flbiomass2C * fmineralization / 100 * c2co2)
  ][ ;; either grass or crop
    set gaz-emission gaz-emission + (gbiomass * glbiomass2C * gmineralization / 100 * c2co2)
  ]
end

;; 5) production-unit dynamics
;; status: verified
to production-unit-decide-fertilization
  ;; buy fertilizer
  let cost min list cash (fertilizer * fertilizerPrice) ; the total price (not more than available cash)
  ;; update budget
  set cash    cash - cost
  set fertiliser-expense fertiliser-expense + cost
  ;; bought quantity      (kgN)
  set boughtFertiliser cost / fertilizerPrice
  ;; fertilizer for crop  (kgN)
  let cropWeight  boughtFertiliser * cropFertilization / 100
  ;; fertilizer for grass (kgN)
  let grassWeight boughtFertiliser * grassFertilization / 100
  ;; fertilizer for forage (kgN)
  let forageWeight boughtFertiliser * forageFertilization / 100
  ;; the owned plots with crops
  let crops plots with [land-cover = "crop"  or land-cover = "agroforestry"]
  ;; the owned plots with grass
  let grass plots with [land-cover = "grass" or land-cover = "sylvopastoralg"]
  ;; the owned plots with grass
  let forages plots with [land-cover = "forage" or land-cover = "sylvopastoralf"]
  ;; spread fertilizer on crops
  if any? crops and cropWeight > 0 [
    ask crops [
      set soil-n soil-n + cropWeight / count crops
    ]
  ]
  ;; spread fertiliser on grass
  if any? grass and grassWeight > 0 [
    ask grass [
      set soil-n soil-n + grassWeight / count grass
    ]
  ]
  ;; spread fertiliser on forage
  if any? forages and forageWeight > 0 [
    ask grass [
      set soil-n soil-n + forageWeight / count grass
    ]
  ]
end

to production-unit-cattle-feed
  let cattle-size      compute-cattle-size  ; the cattle size
  set biomass-need     compute-biomass-need ; the total biomass need
  if trace? [
    print (word "About to feed " cattle-size " heads: ")
    print (word "  total biomass need: " biomass-need)
  ]
  if biomass-need > 0 [  ;; there is a cattle to nourish!!
    set pasture-need     biomass-need * pasture / 100     ; by grazing on grassland
    let pasture-per-head pasture-need / cattle-size       ; the need of pasture per animal
    set forage-need      biomass-need * forage  / 100     ; by eating forage
    let forage-per-head  forage-need  / cattle-size       ; the need of forage per animal
    set nleaf-need       biomass-need * nleaf   / 100     ; by eating leaves on crops or pasture
    let nleaf-per-head   nleaf-need   / cattle-size       ; the need of natural leaves per animal
    set cleaf-need       biomass-need * cleaf   / 100     ; by eating leaves on crops or pasture
    let cleaf-per-head   cleaf-need   / cattle-size       ; the need of cultivated leaves per animal
    set residue-need     biomass-need * residue / 100     ; by grazing on crops
    let residue-per-head residue-need / cattle-size       ; the need of residue per animal
    set concentrate-need biomass-need * concentrate    / 100 ; will be bought
    let concentrate-max  biomass-need * concentrateMax / 100 ; max compensation

    ;; consume on common grass plots  => cpasture-consumed,cnleaf-consumed
    production-unit-consume-pasture common-plots with [land-cover = "grass" or land-cover = "sylvopastoralg"] pasture-per-head nleaf-per-head production-unitNumber
    ;; consume on private grass plots => pasture-consumed,nleaf-consumed
    production-unit-consume-pasture plots        with [land-cover = "grass" or land-cover = "sylvopastoralg"] pasture-per-head nleaf-per-head 1
    ;; adjust the residue need depending on found pasture
    set forage-need     forage-need + (pasture-need - pasture-consumed - cpasture-consumed)
    set forage-per-head forage-need / cattle-size

    ;; consume on common forage plots  => cforage-consumed,ccleaf-consumed
    production-unit-consume-forage common-plots with [land-cover = "forage" or land-cover = "sylvopastoralf"] forage-per-head cleaf-per-head production-unitNumber
    ;; consume on private forage plots => forage-consumed,cleaf-consumed
    production-unit-consume-forage plots        with [land-cover = "forage" or land-cover = "sylvopastoralf"] forage-per-head cleaf-per-head 1
    ;; adjust the residue need depending on found pasture
    set residue-need     residue-need + (forage-need - forage-consumed - cforage-consumed)
    set residue-per-head residue-need / cattle-size

    ;; consume on common crop plots  => cresidue-consumed,ccleaf-consumed
    production-unit-consume-residue common-plots with [land-cover = "crop" or land-cover = "agroforestry"] residue-per-head cleaf-per-head production-unitNumber
    ;; consume of private crop plots => residue-consumed,cleaf-consumed
    production-unit-consume-residue plots with [land-cover = "crop" or land-cover = "agroforestry"] residue-per-head cleaf-per-head 1

    ;; adjust the concentrate need depending on found pasture, leaves and residue
    set concentrate-need min list concentrate-max (concentrate-need +
      (pasture-need - pasture-consumed - cpasture-consumed) +
      (forage-need  - forage-consumed  - cforage-consumed) +
      (residue-need - residue-consumed - cresidue-consumed) +
      (nleaf-need   - nleaf-consumed   - cnleaf-consumed) +
      (cleaf-need   - cleaf-consumed   - ccleaf-consumed))

    production-unit-buy-concentrate
  ]
  if trace? [
    print (word "  Needed biomass:             " biomass-need)
    print (word "  Consumed pasture:           " (pasture-consumed + cpasture-consumed))
    print (word "  Consumed forage:            " (forage-consumed  + cforage-consumed))
    print (word "  Consumed natural leaves:    " (nleaf-consumed   + cnleaf-consumed))
    print (word "  Consumed cultivated leaves: " (cleaf-consumed   + ccleaf-consumed))
    print (word "  Consumed residue:           " (residue-consumed + cresidue-consumed))
    print (word "  Consumed concentrate:       " concentrate-consumed)
    print (word "  Total consumed:             " (pasture-consumed + cpasture-consumed + forage-consumed  + cforage-consumed +
                                                  nleaf-consumed   + cnleaf-consumed + cleaf-consumed   + ccleaf-consumed +
                                                  residue-consumed + cresidue-consumed + concentrate-consumed))
  ]
end

to-report compute-biomass-need
  let cnt 0
  let total 0
  repeat max (list male-max female-max) [
    if cnt <= male-max   [set total total + (array:item males   cnt * array:item male-weight   cnt / 1000 * relative-biomass-need * 365)]
    if cnt <= female-max [set total total + (array:item females cnt * array:item female-weight cnt / 1000 * relative-biomass-need * 365)]
    set cnt cnt + 1
  ]
  report total
end

to production-unit-consume-pasture [grazing-plots pasture-per-head leaf-per-head share-factor]
  if trace? [
    print (word "Grazing on " count grazing-plots " pasture plots")
    ask one-of grazing-plots [
      print (word "  pasture gbiomass: " gbiomass " consumable: " cover-gconsumable "%")
      print (word "  pasture lbiomass: " lbiomass " consumable: " cover-lconsumable "%")
    ]
  ]
  if any? grazing-plots and (pasture-need > 0 or nleaf-need > 0) [  ; grazing strategy on grassland
    ;; the available biomass is the livestock consumable biomass shared by all the production-units (or only one if private)
    let available-gbiomass (reduce + [gbiomass * cover-gconsumable / 100] of grazing-plots) / share-factor
    let available-lbiomass (reduce + [lbiomass * cover-lconsumable / 100] of grazing-plots) / share-factor
    if trace? [
      print (word "  Consuming pasture " ifelse-value share-factor = 1 ["on private:"] ["on common:"])
      print (word "    Available biomass: " available-gbiomass " pasture need: " (pasture-need - (pasture-consumed + cpasture-consumed)))
      print       "  Consuming natural leaves:"
      print (word "    Available biomass: " available-lbiomass " leaf need: "    (nleaf-need   - (nleaf-consumed + cnleaf-consumed)))
    ]
    while [(available-gbiomass > 0 and (pasture-consumed + cpasture-consumed) < pasture-need)] [
      let aPlot one-of grazing-plots with [livestock = 0]        ; an unused plot
      ifelse aplot != nobody [
;        if (pasture-consumed + cpasture-consumed) < pasture-need [
          ;; grass first
          let consumable min list [gbiomass * cover-gconsumable / 100] of aPlot            ; the grass biomass to consume on this plot
                                  (pasture-need - (pasture-consumed + cpasture-consumed))  ; the needed quantity
          ask aPlot [
            set livestock consumable / pasture-per-head                              ; the livestock pressure on this plot
            set gbiomass  gbiomass - consumable                                      ; the consumption of this plot
            set dung      dung + consumable * (1 - feed-digestibility "grass" / 100) ; dung production from grass
          ]
          set available-gbiomass available-gbiomass - consumable   ; decrease available grass biomass
          ;; record pasture consumption
          ifelse share-factor = 1 [ ; private
            set pasture-consumed   pasture-consumed  + consumable
          ][                        ; common
            set cpasture-consumed  cpasture-consumed + consumable
          ]
;        ]
         if (available-lbiomass > 0 and (nleaf-consumed + cnleaf-consumed) < nleaf-need) [
           ;; leaves second
           set consumable min list [lbiomass * cover-lconsumable / 100] of aPlot     ; the leaves biomass to consume on this plot
                                   (nleaf-need - (nleaf-consumed + cnleaf-consumed)) ; the needed quantity
           ask aPlot [
             set livestock max list livestock (consumable / leaf-per-head)            ; the livestock pressure on this plot
             set lbiomass  lbiomass - consumable                                      ; the consumption of this plot
             set dung      dung + consumable * (1 - feed-digestibility "nleaf" / 100) ; dung production from leaves
           ]
           set available-lbiomass available-lbiomass - consumable   ; decrease available leaf biomass
           ;; record pasture consumption
           ifelse share-factor = 1 [ ; private
             set nleaf-consumed   nleaf-consumed + consumable
           ][                        ; common
             set cnleaf-consumed  cnleaf-consumed + consumable
           ]
         ]
      ][  ; no plots available
        stop
      ]
    ]
    if trace? [
       set available-gbiomass (reduce + [gbiomass * cover-gconsumable / 100] of grazing-plots) / share-factor
       set available-lbiomass (reduce + [lbiomass * cover-lconsumable / 100] of grazing-plots) / share-factor
       ifelse share-factor = 1 [ ; private
         print       "  Consumed pasture on private:"
         print (word "    consumed biomass: " pasture-consumed " remaining: " available-gbiomass)
         print       "  Consumed natural leaves:"
         print (word "    consumed biomass: " nleaf-consumed   " remaining: " available-lbiomass)
       ][                        ; common
         print       "  Consumed pasture on common:"
         print (word "    consumed biomass: " cpasture-consumed " remaining: " available-gbiomass)
         print       "  Consumed natural leaves:"
         print (word "    consumed biomass: " cnleaf-consumed   " remaining: " available-lbiomass)
       ]
    ]
  ]
end

to production-unit-consume-forage [grazing-plots forage-per-head leaf-per-head share-factor]
  if trace? [
    print (word "Grazing on " count grazing-plots " forage plots")
    ask one-of grazing-plots [
      print (word "  forage gbiomass: " gbiomass " consumable: " cover-gconsumable "%")
      print (word "  forage lbiomass: " lbiomass " consumable: " cover-lconsumable "%")
    ]
  ]
  if any? grazing-plots and (forage-need > 0 or cleaf-need > 0) [  ; grazing strategy on grassland
    ;; the available biomass is the livestock consumable biomass shared by all the production-units (or only one if private)
    let available-gbiomass (reduce + [gbiomass * cover-gconsumable / 100] of grazing-plots) / share-factor
    let available-lbiomass (reduce + [lbiomass * cover-lconsumable / 100] of grazing-plots) / share-factor
    if trace? [
      print (word "  Consuming forage " ifelse-value share-factor = 1 ["on private:"] ["on common:"])
      print (word "    Available biomass: " available-gbiomass " forage need: " (forage-need - (forage-consumed + cforage-consumed)))
      print       "  Consuming cultivated leaves:"
      print (word "    Available biomass: " available-lbiomass " leaf need: "   (cleaf-need - (cleaf-consumed + ccleaf-consumed)))
    ]
    while [(available-gbiomass > 0 and (forage-consumed + cforage-consumed) < forage-need)] [
      let aPlot one-of grazing-plots with [livestock = 0]        ; an unused plot
      ifelse aplot != nobody [
        if (forage-consumed + cforage-consumed) < forage-need [
          ;; grass first
          let consumable min list [gbiomass * cover-gconsumable / 100] of aPlot               ; the forage biomass to consume on this plot
                                  (forage-need - (forage-consumed + cforage-consumed))  ; the needed quantity
          ask aPlot [
            set livestock consumable / forage-per-head                         ; the livestock pressure on this plot
            set gbiomass  gbiomass - consumable                                ; the consumption of this plot
            set dung      dung + consumable * (1 - feed-digestibility "forage" / 100) ; dung production from grass
          ]
          set available-gbiomass available-gbiomass - consumable   ; decrease available grass biomass
          ;; record pasture consumption
          ifelse share-factor = 1 [ ; private
            set forage-consumed   forage-consumed + consumable
          ][                        ; common
            set cforage-consumed  cforage-consumed + consumable
          ]
        ]
        if (available-lbiomass > 0 and (cleaf-consumed + ccleaf-consumed) < cleaf-need) [
          ;; leaves second
          let consumable min list [lbiomass * cover-lconsumable / 100] of aPlot     ; the leaves biomass to consume on this plot
                                  (cleaf-need - (cleaf-consumed + ccleaf-consumed)) ; the needed quantity
          ask aPlot [
            set livestock max list livestock (consumable / leaf-per-head)    ; the livestock pressure on this plot
            set lbiomass  lbiomass - consumable                              ; the consumption of this plot
            set dung      dung + consumable * (1 - feed-digestibility "cleaf" / 100) ; dung production from leaves
          ]
          set available-lbiomass available-lbiomass - consumable   ; decrease available leaf biomass
          ;; record pasture consumption
          ifelse share-factor = 1 [ ; private
            set cleaf-consumed   cleaf-consumed + consumable
          ][                        ; common
            set ccleaf-consumed  ccleaf-consumed + consumable
          ]
        ]
      ][
        stop
      ]
    ]
    if trace? [
       set available-gbiomass (reduce + [gbiomass * cover-gconsumable / 100] of grazing-plots) / share-factor
       set available-lbiomass (reduce + [lbiomass * cover-lconsumable / 100] of grazing-plots) / share-factor
       ifelse share-factor = 1 [ ; private
         print       "  Consumed forage on private:"
         print (word "    consumed biomass: " forage-consumed " remaining: " available-gbiomass)
         print       "  Consumed cultivated leaves:"
         print (word "    consumed biomass: " cleaf-consumed  " remaining: " available-lbiomass)
       ][                        ; common
         print       "  Consumed forage on common:"
         print (word "    consumed biomass: " cforage-consumed " remaining: " available-gbiomass)
         print       "  Consumed cultivated leaves:"
         print (word "    consumed biomass: " ccleaf-consumed  " remaining: " available-lbiomass)
       ]
    ]
  ]
end

to production-unit-consume-residue [grazing-plots pasture-per-head leaf-per-head share-factor]
  if trace? [
    print (word "Grazing on " count grazing-plots " residue plots")
    ask one-of grazing-plots [
      print (word "  residue gbiomass: " gbiomass " consumable: " cover-gconsumable "%")
      print (word "  residue lbiomass: " lbiomass " consumable: " cover-lconsumable "%")
    ]
  ]
  if any? grazing-plots and pasture-need > 0 and cleaf-need > 0 [  ; grazing strategy on grassland
    ;; the available biomass is the consumable biomass shared by all the production-units (or only one if private)
    let available-gbiomass (reduce + [gbiomass * cover-gconsumable / 100] of grazing-plots) / share-factor
    let available-lbiomass (reduce + [lbiomass * cover-lconsumable / 100] of grazing-plots) / share-factor
    if trace? [
      print (word "  Consuming residue " ifelse-value share-factor = 1 ["on private:"] ["on common:"])
      print (word "    Available biomass: " available-gbiomass " residue need: " (residue-need - (residue-consumed + cresidue-consumed)))
      print       "  Consuming cultivated leaves:"
      print (word "    Available biomass: " available-lbiomass " leaf need: "    (cleaf-need - (cleaf-consumed + ccleaf-consumed)))
    ]
    while [(available-gbiomass > 0 and (residue-consumed + cresidue-consumed) < residue-need)] [
      let aPlot one-of grazing-plots with [livestock = 0]        ; an unused plot
      ifelse aplot != nobody [
        if (residue-consumed + cresidue-consumed) < residue-need [
          ;; crop residue first
          let consumable min list [gbiomass * cover-gconsumable / 100] of aPlot            ; the grass biomass to consume on this plot
                                  (residue-need - (residue-consumed + cresidue-consumed))  ; the needed quantity
          ask aPlot [
            set livestock consumable / pasture-per-head                         ; the livestock pressure on this plot
            set gbiomass  gbiomass - consumable                                 ; the consumption of this plot
            set dung      dung + consumable * (1 - feed-digestibility "residue" / 100) ; dung production from crop residue
          ]
          set available-gbiomass available-gbiomass - consumable   ; update available biomass
                                                                   ; record residue consumption
          ifelse share-factor = 1 [ ; private
            set residue-consumed   residue-consumed + consumable
          ][                        ; common
            set cresidue-consumed  cresidue-consumed + consumable
          ]
        ]
        if (available-lbiomass > 0 and (cleaf-consumed + ccleaf-consumed) < cleaf-need) [
          ;; leaves secoond
          let consumable min list [lbiomass * cover-lconsumable / 100] of aPlot     ; the leaves biomass to consume on this plot
                                  (cleaf-need - (cleaf-consumed + ccleaf-consumed)) ; the needed quantity
          ask aPlot [
            set livestock max list livestock (consumable / leaf-per-head)    ; the livestock pressure on this plot
            set lbiomass  lbiomass - consumable                              ; the consumption of this plot
            set dung      dung + consumable * (1 - feed-digestibility "cleaf" / 100) ; dung production from leaves
          ]
          set available-lbiomass available-lbiomass - consumable   ; decrease available biomass
          ;; record pasture consumption
          ifelse share-factor = 1 [ ; private
            set cleaf-consumed   cleaf-consumed + consumable
          ][                        ; common
            set ccleaf-consumed  ccleaf-consumed + consumable
          ]
        ]
      ][
        stop
      ]
    ]
    if trace? [
       set available-gbiomass (reduce + [gbiomass * cover-gconsumable / 100] of grazing-plots) / share-factor
       set available-lbiomass (reduce + [lbiomass * cover-lconsumable / 100] of grazing-plots) / share-factor
       ifelse share-factor = 1 [ ; private
         print       "  Consumed residue on private:"
         print (word "    consumed biomass: " residue-consumed " remaining: " available-gbiomass)
         print       "  Consumed cultivated leaves:"
         print (word "    consumed biomass: " cleaf-consumed   " remaining: " available-lbiomass)
       ][                        ; common
         print       "  Consumed residue on common:"
         print (word "    consumed biomass: " cresidue-consumed " remaining: " available-gbiomass)
         print       "  Consumed cultivated leaves:"
         print (word "    consumed biomass: " ccleaf-consumed   " remaining: " available-lbiomass)
       ]
    ]
  ]
end

to production-unit-buy-concentrate
  if concentrate-need > 0 [
    ;; the amount to put on concentrate up to available cash
    let buy min list cash (concentrate-need * concentratePrice)
    ;; update budget
    set cash                 cash - buy                ; buy it
    set concentrate-expense  concentrate-expense + buy ; update expenses
    ;; bought quantity      (kgDM)
    set concentrate-consumed buy / concentratePrice  ; estimated consumed concentrate
    if trace? [
      print       "Consumed concentrate:"
      print (word "  consumed-concentrate: " concentrate-consumed " on need: " concentrate-need)
    ]
  ]
end

to production-unit-transformation
  ;; compute global available energy
  let gEnergy (pasture-consumed + cpasture-consumed) * feed-kgDM2kgCal "grass"   +
              (forage-consumed  + cforage-consumed)  * feed-kgDM2kgCal "forage"  +
              (nleaf-consumed   + cnleaf-consumed)   * feed-kgDM2kgCal "nleaf"   +
              (cleaf-consumed   + ccleaf-consumed)   * feed-kgDM2kgCal "cleaf"   +
              (residue-consumed + cresidue-consumed) * feed-kgDM2kgCal "residue" +
              concentrate-consumed                   * feed-kgDM2kgCal "feed"
  if gEnergy > 0 [
    ;; compute metabolizable energy
    let mEnergy (pasture-consumed + cpasture-consumed) * feed-ME "grass"   +
                (forage-consumed  + cforage-consumed)  * feed-ME "forage"  +
                (nleaf-consumed   + cnleaf-consumed)   * feed-ME "nleaf"   +
                (cleaf-consumed   + ccleaf-consumed)   * feed-ME "cleaf"   +
                (residue-consumed + cresidue-consumed) * feed-ME "residue" +
                concentrate-consumed                   * feed-ME "feed"
    ;; delete the energy for maintenance, walking and shewing
    let maintenanceEnergy  compute-maintenance-UFL + compute-walking-UFL
    let cattle-weight      compute-cattle-weight
    let availableEnergy    mEnergy - maintenanceEnergy
    if trace? [
      print "Metabolism:"
      print (word "  total energy:               " gEnergy)
      print (word "  total metabolizable energy: " mEnergy)
      print (word "  maintenance energy:         " maintenanceEnergy)
      print (word "  remaining energy:           " availableEnergy)
    ]
    ifelse availableEnergy > 0 [    ; enough energy for milk production
      set production-UFL availableEnergy / compute-cattle-size ; to record
      let milking-weight compute-milking-weight
      let maxl literMax * compute-milking-size * 365
      ifelse milking-weight > 0 [  ; there are milking cows
        let milkingEnergy  availableEnergy * (milking-weight / cattle-weight) * ; available energy of milking cows
                           (0.65 + 0.247 * (mEnergy / gEnergy - 0.63))          ; some weighting factor
        set milk-production min list maxl (milkingEnergy * UFL2liter)
        if trace? [
          print (word "  energy for milking:         " milkingEnergy " producing " milk-production " liters")
          print (word "  (" (milk-production / compute-milking-size / 365) " liters per milking cow per day")
        ]
      ][
        if trace? [
          print (word "  no milking cows.")
        ]
      ]
    ][               ;; not enough energy => compute mortality increase
      let missing-energy      abs availableEnergy
      let month-needed-energy maintenanceEnergy / 12
      (ifelse missing-energy < rlimit * month-needed-energy [ ;; survival on reserve
        set starved-prop 0
      ] missing-energy > dLimit * month-needed-energy [       ;; not enough for surviving
        set starved-prop dMortality
      ][                                                      ;; in between
        set starved-prop rMortality +
        (missing-energy - rlimit * month-needed-energy) / month-needed-energy *
        (dMortality - rMortality) / (dLimit - rLimit)
      ])
      if trace? [
        print (word "  starving proportion: " starved-prop)
      ]
    ]
  ]
  ;; here starved-prop    is the proportion of starving died animals
  ;; here production-UFL  is the UFL per animal
  ;; here milk-production is the total milk production
end

to-report compute-maintenance-UFL
  let cnt 0
  let total 0
  ;; metabolism need
  repeat max (list male-max female-max) [
    if cnt <= male-max   [set total total + (array:item males   cnt * (array:item male-weight   cnt ^ 0.75) * UFLm * 365)]
    if cnt <= female-max [set total total + (array:item females cnt * (array:item female-weight cnt ^ 0.75) * UFLm * 365)]
    set cnt cnt + 1
  ]
  ;; includes chewing need as a percentage of energy need
  report total * (1 + sp / 100)
end

to-report compute-walking-UFL
  let cnt 0
  let total 0
  repeat max (list male-max female-max) [
    if cnt <= male-max   [set total total + (array:item males   cnt * (array:item male-weight   cnt) *
                                                                (walk * 365) * UFLw )]
    if cnt <= female-max [set total total + (array:item females cnt * (array:item female-weight cnt) *
                                                                (walk * 365) * UFLw )]
    set cnt cnt + 1
  ]
  report total
end

to production-unit-sell-milk
  ;; milk selling
  if sharedMilkery? and milkeryMilk > 0 [ ; sold to milk factory
     set cash               cash + milk-production * (milkeryMilk / 100) * diaryPrice - milkeryContribution
     set membership-expense membership-expense + milkeryContribution
     set dmilk-income       dmilk-income  + milk-production * (milkeryMilk / 100) * diaryPrice
  ]
  if rawMilk > 0 [       ; part of sold raw milk
    set cash          cash + milk-production * (rawMilk / 100) * milkPrice
    set rmilk-income  rmilk-income + milk-production * (rawMilk / 100) * milkPrice
  ]
  if processedMilk > 0 [ ; part of self-processed milk
    set cash          cash + milk-production * (processedMilk / 100) * processedPrice
    set tmilk-income  tmilk-income + milk-production * (processedMilk / 100) * processedPrice
  ]
end

to production-unit-grow-cattle
  ;; new structure
  if trace? [
    print (word "Cattle population before evolution:" compute-cattle-size)
  ]
  ;; old cows
  set old-male-killed   array:item males   male-max
  set old-female-killed array:item females female-max
  ;; male evolution
  let age male-max
  while [age > 0] [
    let previous   (array:item males          (age - 1))
    let nmortality (array:item male-mortality (age - 1)) / 100 * previous ; age natural mortality
    let smortality starved-prop                          / 100 * previous ; age starvation mortality
    let age-class  (male-age-class age)
    if nmortality + smortality > previous [
      set smortality previous - nmortality
    ]
    table:put death     age-class (table:get death   age-class + nmortality) ; natural mortality
    table:put starved   age-class (table:get starved age-class + smortality) ; starving mortality
    array:set males age (previous - smortality - nmortality)
    set age age - 1
  ]
  ;; female evolution
  set age female-max
  while [age > 0] [
    let previous   (array:item females          (age - 1))
    let nmortality (array:item female-mortality (age - 1)) / 100 * previous ; age natural mortality
    let smortality starved-prop                            / 100 * previous ; age starvation mortality
    let age-class  (female-age-class age)
    if nmortality + smortality > previous [
      set smortality previous - nmortality
    ]
    table:put death   age-class (table:get death   age-class + nmortality) ; natural mortality
    table:put starved age-class (table:get starved age-class + smortality) ; starving mortality
    set births  births  + previous * (array:item female-fecundity (age - 1)) ; reproduction
    array:set females age (previous - smortality - nmortality)
    set age age - 1
  ]
  ;; new cows
  array:set males   0 (births / 2)
  array:set females 0 (births / 2)
  if trace? [
    print       "Cattle evolution:"
    print (word "  natural death: " death ", starvation: " starved ", age: " (old-male-killed + old-female-killed))
    print (word "  birth: " births)
    print (word "Cattle population after evolution:" compute-cattle-size)
  ]
  ;; here births is the number of new borns
  ;; here death   is the number of naturaly died animals
  ;; here starved is the number of starving died animals
  ;; here old-male-killed/old-female-killed are old slaughtered animals
end

to production-unit-sell-meat
  let age                  max list male-max female-max ; counter
  let remaining-old-male   old-male-killed              ; account for old male   killed
  let remaining-old-female old-female-killed            ; account for old female killed
  while [age >= 0] [

   if age <= male-max [
      let off-take (array:item males age) * (array:item male-slaughtering age) / 100    ; theoretical number
      let age-class  (male-age-class age)
      ifelse off-take > 0 [
        if remaining-old-male > 0 [
          set remaining-old-male    remaining-old-male - off-take                       ; account for male already killed
          set off-take ifelse-value remaining-old-male >= 0 [0][0 - remaining-old-male] ; real number
        ]
        table:put killed age-class table:get killed age-class + off-take
      ][
        table:put bought age-class table:get bought age-class - off-take
      ]
      array:set males age max (list 0 ((array:item males age) - off-take))     ; number precision problem
    ]
    if age <= female-max [
      let off-take (array:item females age) * (array:item female-slaughtering age) / 100  ; theoretical number
      let age-class  (female-age-class age)
      ifelse off-take > 0 [
        if remaining-old-female > 0 [
          set remaining-old-female  remaining-old-female - off-take                         ; account for female already killed
          set off-take ifelse-value remaining-old-female >= 0 [0][0 - remaining-old-female] ; real number
        ]
        table:put killed age-class table:get killed age-class + off-take
      ][
        table:put bought age-class table:get bought age-class - off-take
      ]
      array:set females age max (list 0 ((array:item females age) - off-take)) ; number precision problem
    ]
    set age age - 1
  ]
  ;; add already killed
  let total-killed table:get killed "young" + table:get killed "subadult" + table:get killed "adult"
  if trace? [
    print "Cattle slaughtering:"
    print (word "  total killed: " total-killed)
  ]
  ;; selling slaughtered cattle
  if total-killed > 0 [  ; a percentage of adults is slaughtered
    if sharedSlaughterhouse? and shAnimal > 0 [  ; common slaughterhouse
      set cash               cash               + total-killed * (shAnimal / 100) * meatPrice - slaughterContribution
      set membership-expense membership-expense + slaughterContribution   ; update expenses
      set shmeat-income      shmeat-income      + total-killed * (shAnimal / 100) * shPrice
    ]
    if liveAnimal > 0 [  ; the live cows
       set cash         cash         + total-killed * (liveAnimal / 100) * cowPrice
       set rmeat-income rmeat-income + total-killed * (liveAnimal / 100) * cowPrice
    ]
    if carcass > 0 [     ; the carcasses
       set cash         cash         + total-killed * (carcass / 100) * meatPrice
       set tmeat-income tmeat-income + total-killed * (carcass / 100) * meatPrice
    ]
  ]
  let total-bought table:get bought "young" + table:get bought "subadult" + table:get bought "adult"
  if total-bought > 0 [
       set cash         cash        - total-bought * cowPrice
       set cow-expense  cow-expense + total-bought * cowPrice
  ]
  if trace? [
    print (word "  live cow income: " rmeat-income)
    print (word "  carcass income:  " tmeat-income)
    print (word "  bought cows:     " total-bought " with expense: " (total-bought * cowPrice))
    print (word "  females:    " females)
    print (word "  males:      " males)
    print (word "  population: " compute-cattle-size)
  ]
end

to production-unit-update-gaz-emission
  ;; total ingested dry matter
  let DMI (pasture-consumed + cpasture-consumed) +
          (forage-consumed  + forage-consumed) +
          (nleaf-consumed   + cnleaf-consumed) +
          (cleaf-consumed   + ccleaf-consumed) +
          (residue-consumed + cresidue-consumed) +
          concentrate-consumed
  if DMI > 0 [ ;; something eaten
    ;; we have the pasture, grass, leaves and concentrate consumed, we get organic matter ingested quantities
    let OMI (pasture-consumed + cpasture-consumed) * feed-om "grass"   / 100 * feed-digestibility "grass"   / 100 +
            (forage-consumed  + forage-consumed)   * feed-om "forage"  / 100 * feed-digestibility "forage"  / 100 +
            (nleaf-consumed   + cnleaf-consumed)   * feed-om "nleaf"   / 100 * feed-digestibility "nleaf"   / 100 +
            (cleaf-consumed   + ccleaf-consumed)   * feed-om "cleaf"   / 100 * feed-digestibility "cleaf"   / 100 +
            (residue-consumed + cresidue-consumed) * feed-om "residue" / 100 * feed-digestibility "residue" / 100 +
            concentrate-consumed                   * feed-om "feed"    / 100 * feed-digestibility "feed"    / 100
    ;; the proportion of organic matter on ingested dry matter
    let OM-DM     OMI / DMI
    ;; the proportion of organic matter on cattle weight
    let OM-weight OMI / compute-cattle-weight
    ;; compute CH4 emission
    set DOMI2CH4 0
    ifelse concentrate-consumed = 0 [ ;; only pasture and forage
                                      ; the proportion of fiber
      let NDF ((pasture-consumed + cpasture-consumed) * feed-NDF "grass"   / 100 +
        (forage-consumed  + cforage-consumed)  * feed-NDF "forage"  / 100 +
        (nleaf-consumed   + cnleaf-consumed)   * feed-NDF "nleaf"   / 100 +
        (cleaf-consumed   + ccleaf-consumed)   * feed-NDF "cleaf"   / 100 +
        (residue-consumed + cresidue-consumed) * feed-NDF "residue" / 100) / DMI
      set DOMI2CH4 34.95 - 4.05 * OM-weight + 0.027 * NDF - 0.010 * OM-DM
    ][
      let PCO concentrate-consumed / DMI
      set DOMI2CH4 45.42 - 6.66 * OM-weight + 0.75 * OM-weight ^ 2 + 19.65 * PCO - 35 * PCO ^ 2
    ]
    let CH4 OMI * 0.001 * OM-DM * DOMI2CH4
    if trace? [
      print (word "  CH4 proportion: " DOMI2CH4 " resulting to: " CH4 " emission.")
    ]
    set co2-emission co2-emission + CH4 * ch4toco2
  ]
end

;; Access to cattle structure
;; ==========================

to-report compute-cattle-weight
  let cnt   0
  let total 0
  while [cnt <= max (list male-max female-max)] [
    if cnt <= male-max   [set total total + (array:item males   cnt * array:item male-weight   cnt)]
    if cnt <= female-max [set total total + (array:item females cnt * array:item female-weight cnt)]
    set cnt cnt + 1
  ]
  report total
end

to-report compute-milking-weight
  let cnt milking-min-age
  let total 0
  while [cnt <= milking-max-age] [
    set total total + (array:item females cnt * array:item female-weight cnt)
    set cnt cnt + 1
  ]
  report total
end

to-report compute-cattle-size
  let cnt   0
  let total 0
  while [cnt <= max (list male-max female-max)] [
    if cnt <= male-max   [set total total + array:item males   cnt ]
    if cnt <= female-max [set total total + array:item females cnt ]
    set cnt cnt + 1
  ]
  report total
end

to-report compute-male-size [class]
  let descr table:get male-structure class
  let cnt   (first descr)
  let total 0
  while [cnt <= item 1 descr] [
    set total total + array:item males cnt
    set cnt cnt + 1
  ]
  report total
end

to-report compute-female-size [class]
  let descr table:get female-structure class
  let cnt   (first descr)
  let total 0
  while [cnt <= item 1 descr] [
    set total total + array:item females cnt
    set cnt cnt + 1
  ]
  report total
end

to-report male-age-class [age]
  let keys table:keys male-structure
  let res filter [key -> (run-result [descr -> (age >= first descr) and (age <= item 1 descr)] table:get male-structure key)] keys
  report (first res)
end

to-report female-age-class [age]
  let keys table:keys female-structure
  let res filter [key -> (run-result [descr -> (age >= first descr) and (age <= item 1 descr)] table:get female-structure key)] keys
  report (first res)
end

to-report compute-milking-size
  let cnt milking-min-age
  let total 0
  while [cnt <= milking-max-age] [
    set total total + array:item females cnt
    set cnt cnt + 1
  ]
  report total
end


;; Indicators
;; ==========

to update-indicators
  ;; environmental indicators
  ;; - plot gaz emission
  set total-plot-emission (reduce + [gaz-emission] of patches) / 1000
  ;; compute carbon impact
  ifelse any? production-units [
    ;; production-unit gaz emission
    set total-production-unit-emission (reduce + [co2-emission] of production-units)
  ][
    set total-production-unit-emission 0
  ]
  ; - grass biomass indicators
  let lst [gBiomass] of used-plots
  set average-gbiomass ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [gBiomass] of used-plots with [land-cover = "grass"]
  set average-gbiomass-grass ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [gBiomass] of used-plots with [land-cover = "crop"]
  set average-gbiomass-crop ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [gBiomass] of used-plots with [land-cover = "forage"]
  set average-gbiomass-forage ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [gBiomass] of used-plots with [land-cover = "agroforestry"]
  set average-gbiomass-agroforestry ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [gBiomass] of used-plots with [land-cover = "sylvogpastoral"]
  set average-gbiomass-sylvogpastoral ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [gBiomass] of used-plots with [land-cover = "sylvofpastroal"]
  set average-gbiomass-sylvofpastoral ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  ; leaf biomass indicators
  set lst [lBiomass] of used-plots
  set average-lbiomass ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [lBiomass] of used-plots with [land-cover = "grass"]
  set average-lBiomass-grass ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [lBiomass] of used-plots with [land-cover = "crop"]
  set average-lBiomass-crop ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [lBiomass] of used-plots with [land-cover = "forage"]
  set average-lBiomass-forage ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [lBiomass] of used-plots with [land-cover = "agroforestry"]
  set average-lBiomass-agroforestry ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [lBiomass] of used-plots with [land-cover = "sylvogpastoral"]
  set average-lBiomass-sylvogpastoral ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  set lst [lBiomass] of used-plots with [land-cover = "sylvofpastroal"]
  set average-lBiomass-sylvofpastoral ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  ; ligneous biomass indicators
  set lst [tBiomass] of used-plots
  set average-tbiomass ifelse-value not empty? lst [(reduce + lst) / length lst] [0]
  ; water and nutrients on landscape
  set lst [water] of used-plots
  set average-water ifelse-value not empty? lst [(reduce + lst) / length lst][0]
  ; livestock use of landscape
  set lst used-plots with [livestock > 0]
  set grass-livestock          count lst with [land-cover = "grass"]           * plot-surface
  set crop-livestock           count lst with [land-cover = "crop"]            * plot-surface
  set forage-livestock         count lst with [land-cover = "forage"]          * plot-surface
  set agroforestry-livestock   count lst with [land-cover = "agroforestry"]    * plot-surface
  set sylvogpastoral-livestock count lst with [land-cover = "sylvogpastoral"]  * plot-surface
  set sylvofpastoral-livestock count lst with [land-cover = "sylvofpastoral"]  * plot-surface

  ; c-sequestration
  set lst [soil-c] of patches with [land-cover != "nothing"]
  set total-c-sequestration (ifelse-value not empty? lst [(reduce + lst) / 1000][0])
  ; average nutrient
  set lst [soil-n] of used-plots
  set average-nutrient ifelse-value not empty? lst [(reduce + lst) / length lst][0]
  ; fertilizer contribution (fertilizer of production-units spread on the patches)
  let lst2 [boughtFertiliser] of production-units ; (length lst = number of used-plots)
  set average-fertilizer (ifelse-value not empty? lst and not empty? lst2 [(reduce + lst2) / length lst][0])
  ; livestock contribution
  set lst [dung-n-input] of used-plots
  set average-manure (ifelse-value not empty? lst [(reduce + lst) / length lst][0])
  ; grass liter contribution
  set lst [grass-n-input] of used-plots
  set average-gliter (ifelse-value not empty? lst [(reduce + lst) / length lst][0])
  ; grass liter contribution
  set lst [leaves-n-input] of used-plots
  set average-lliter (ifelse-value not empty? lst [(reduce + lst) / length lst][0])


  set lst [DOMI2CH4] of production-units
  set average-domi2ch4 reduce + lst / length lst

  ; production
  set lst [array:item males 0] of production-units
  set average-male-born (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [array:item females 0] of production-units
  set average-female-born (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set average-born average-male-born + average-female-born
  set lst [compute-male-size "young"] of production-units
  set average-male-young (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [compute-female-size "young"] of production-units
  set average-female-young (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [compute-male-size "subadult"] of production-units
  set average-male-subadult (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [compute-female-size "subadult"] of production-units
  set average-female-subadult (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [compute-male-size "adult"] of production-units
  set average-male-adult (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [compute-female-size "adult"] of production-units
  set average-female-adult (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set average-cattle average-male-young    + average-female-young    +
                     average-male-subadult + average-female-subadult +
                     average-male-adult    + average-female-adult
  set lst [table:get death "young"] of production-units
  set average-young-death   (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [table:get death "subadult"] of production-units
  set average-subadult-death   (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [table:get death "adult"] of production-units
  set average-adult-death   (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set average-death (average-young-death + average-subadult-death + average-adult-death) / 3
  set lst [table:get starved "young"] of production-units
  set average-young-starved (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [table:get starved "subadult"] of production-units
  set average-subadult-starved (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [table:get starved "adult"] of production-units
  set average-adult-starved (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set average-starved (average-young-starved + average-subadult-starved + average-adult-starved) / 3
  set lst [table:get killed "young"] of production-units
  set average-young-killed (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [table:get killed "subadult"] of production-units
  set average-subadult-killed (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [table:get killed "adult"] of production-units
  set average-adult-killed (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set average-killed (average-young-killed + average-subadult-killed + average-adult-killed) / 3
  set lst [table:get bought "young"] of production-units
  set average-young-bought (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [table:get bought "subadult"] of production-units
  set average-subadult-bought (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [table:get bought "adult"] of production-units
  set average-adult-bought (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set average-bought (average-young-bought + average-subadult-bought + average-adult-bought) / 3
  set lst [old-male-killed] of production-units
  set average-old-male-killed (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [old-female-killed] of production-units
  set average-old-female-killed (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set average-old-killed average-old-male-killed + average-old-female-killed

  set average-live-sold    average-killed * (liveAnimal / 100)
  set average-carcass-sold average-killed * (carcass    / 100)
  set average-sh-sold      average-killed * (shAnimal   / 100)

  set lst [biomass-need] of production-units
  set average-biomass-need     (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [pasture-need] of production-units
  set average-pasture-need     (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [residue-need] of production-units
  set average-residue-need     (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [nleaf-need] of production-units
  set average-nleaf-need       (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [cleaf-need] of production-units
  set average-cleaf-need       (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [concentrate-need] of production-units
  set average-concentrate-need (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [forage-need] of production-units
  set average-forage-need      (ifelse-value not empty? lst [reduce + lst / length lst][0])

  set lst [pasture-consumed] of production-units
  set average-pasture-consumed     (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [residue-consumed] of production-units
  set average-residue-consumed     (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [nleaf-consumed] of production-units
  set average-nleaf-consumed       (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [cleaf-consumed] of production-units
  set average-cleaf-consumed       (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [forage-consumed] of production-units
  set average-forage-consumed      (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [cpasture-consumed] of production-units
  set average-cpasture-consumed    (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [cresidue-consumed] of production-units
  set average-cresidue-consumed    (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [cnleaf-consumed] of production-units
  set average-cnleaf-consumed      (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [ccleaf-consumed] of production-units
  set average-ccleaf-consumed      (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [cforage-consumed] of production-units
  set average-cforage-consumed     (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [concentrate-consumed] of production-units
  set average-concentrate-consumed (ifelse-value not empty? lst [reduce + lst / length lst][0])

  set lst [production-ufl] of production-units
  set average-production-ufl  (ifelse-value not empty? lst [reduce + lst / length lst][0])

  set lst [milk-production] of production-units
  set average-milk-production (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set average-rmilk-sold  average-milk-production * (rawMilk / 100)
  set average-pmilk-sold  average-milk-production * (processedMilk / 100)
  set average-mmilk-sold  average-milk-production * (milkeryMilk / 100)

  ; social
  set average-amilk  average-milk-production - average-rmilk-sold - average-pmilk-sold - average-mmilk-sold
  set nb-cooperative milkeryMilk / 15 ; one cooperative per 15% sold to milkery

  set lst [cash] of production-units
  set average-cash (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [rmilk-income] of production-units
  set average-rmilk-income (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [tmilk-income] of production-units
  set average-tmilk-income (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [rmeat-income] of production-units
  set average-rmeat-income (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [tmeat-income] of production-units
  set average-tmeat-income (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [residue-expense] of production-units
  set average-residue-expense (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [concentrate-expense] of production-units
  set average-concentrate-expense (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [fertiliser-expense] of production-units
  set average-fertiliser-expense (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [membership-expense] of production-units
  set average-membership-expense (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set lst [cow-expense] of production-units
  set average-cow-expense (ifelse-value not empty? lst [reduce + lst / length lst][0])
  set average-income  average-rmilk-income + average-tmilk-income + average-rmeat-income + average-tmeat-income
  set average-expense average-residue-expense + average-concentrate-expense + average-fertiliser-expense + average-membership-expense + average-cow-expense
  set average-balance average-income - average-expense

  ; local development
  set nb-ss-employee  (rawMilk + processedMilk + milkeryMilk) / 10   ; one employee per 10% sold
  set nb-in-employee  (milkeryMilk + shAnimal) / 15 * 3              ; three employees per 15 % sold to industry
  set nb-cow-employee (average-cattle * count production-units) / 30 ; one employee per 30 cows
  set nb-employee     (nb-ss-employee + nb-in-employee + nb-cow-employee) ; total
end

;; Visualization
;; =============

to update-view
  set maxWater    0
  set maxNutrient 0
  set maxC        0
  set maxGBiomass 0
  set maxLBiomass 0
  set maxTBiomass 0
  set maxDung     0
  ask patches [
    set maxWater    max list maxWater water
    set maxNutrient max list maxNutrient soil-n
    set maxC        max list maxC soil-c
;    set maxGBiomass max list maxGBiomass gBiomass
    set maxGBiomass 300
    set maxLBiomass max list maxLBiomass lBiomass
    set maxTBiomass max list maxTBiomass tBiomass
    set maxDung     max list maxDung dung
  ]
  if maxDung = 0 [set maxDung 1]
  ask patches [
    patch-update-view
  ]
  ask production-units [
    production-unit-update-view
  ]
end

to patch-update-view
  ;; update the color of the patch according to the choice
  if colorInfo = "cover" [
    set pcolor table:get-or-default land-cover-colors land-cover black
  ]
  if colorInfo = "water" [
    set pcolor scale-color blue water maxWater 0
  ]
  if colorInfo = "nutrient" [
    set pcolor scale-color brown soil-n maxNutrient 0
  ]
  if colorInfo = "gBiomass" [
    set pcolor scale-color green gBiomass maxGBiomass 0
  ]
  if colorInfo = "lBiomass" [
    set pcolor scale-color green lBiomass maxLBiomass 0
  ]
  if colorInfo = "tBiomass" [
    set pcolor scale-color brown tBiomass maxTBiomass 0
  ]
  if colorInfo = "livestock" [
    set pcolor scale-color violet livestock 3 0
  ]
  if colorInfo = "dung" [
    set pcolor scale-color brown dung maxDung 0
  ]
  if colorInfo = "cSequestration" [
    set pcolor scale-color black soil-c 50 0
  ]
  if colorInfo = "gazEmission" [
    set pcolor scale-color black gaz-emission 400 0
  ]
end

to production-unit-update-view
    ;; update the label of the patch according to the choice
  if numericInfo = "nothing" [
    set label ""
  ]
  if numericInfo = "cash" [
    set label precision cash 0
  ]
  if numericInfo = "gazEmission" [
    set label precision co2-emission 0
  ]
end

;; some utility functions

; returns the list but the first n elements
to-report but-n [n lst]
  let rest lst
  repeat n [set rest but-first rest]
  report rest
end
@#$#@#$#@
GRAPHICS-WINDOW
15
195
389
684
-1
-1
6.0
1
10
1
1
1
0
0
0
1
0
60
0
79
0
0
1
ticks
30.0

TEXTBOX
15
14
165
32
Visualization
13
0.0
1

CHOOSER
15
58
156
103
colorInfo
colorInfo
"water" "nutrient" "gBiomass" "lBiomass" "tBiomass" "livestock" "dung" "cover" "cSequestration" "gazEmission"
7

CHOOSER
16
126
154
171
numericInfo
numericInfo
"cash" "nothing" "gazEmission"
1

TEXTBOX
15
37
165
55
1) environment
11
0.0
1

TEXTBOX
14
110
164
128
2) farms
11
0.0
1

BUTTON
202
57
310
90
NIL
update-view
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

MONITOR
202
119
295
164
Season
season-name
0
1
11

MONITOR
294
119
413
164
Annual pluviometry
pluviometry
0
1
11

@#$#@#$#@
## WHAT IS IT?

(a general understanding of what the model is trying to show or explain)

## HOW IT WORKS

(what rules the agents use to create the overall behavior of the model)

## HOW TO USE IT

(how to use the model, including a description of each of the items in the Interface tab)

## THINGS TO NOTICE

(suggested things for the user to notice while running the model)

## THINGS TO TRY

(suggested things for the user to try to do (move sliders, switches, etc.) with the model)

## EXTENDING THE MODEL

(suggested things to add or change in the Code tab to make the model more complicated, detailed, accurate, etc.)

## NETLOGO FEATURES

(interesting or unusual features of NetLogo that the model uses, particularly in the Code tab; or where workarounds were needed for missing features)

## RELATED MODELS

(models in the NetLogo Models Library and elsewhere which are of related interest)

## CREDITS AND REFERENCES

(a reference to the model's URL on the web if it has one, as well as any other necessary credits, citations, and links)
@#$#@#$#@
default
true
0
Polygon -7500403 true true 150 5 40 250 150 205 260 250

airplane
true
0
Polygon -7500403 true true 150 0 135 15 120 60 120 105 15 165 15 195 120 180 135 240 105 270 120 285 150 270 180 285 210 270 165 240 180 180 285 195 285 165 180 105 180 60 165 15

arrow
true
0
Polygon -7500403 true true 150 0 0 150 105 150 105 293 195 293 195 150 300 150

box
false
0
Polygon -7500403 true true 150 285 285 225 285 75 150 135
Polygon -7500403 true true 150 135 15 75 150 15 285 75
Polygon -7500403 true true 15 75 15 225 150 285 150 135
Line -16777216 false 150 285 150 135
Line -16777216 false 150 135 15 75
Line -16777216 false 150 135 285 75

bug
true
0
Circle -7500403 true true 96 182 108
Circle -7500403 true true 110 127 80
Circle -7500403 true true 110 75 80
Line -7500403 true 150 100 80 30
Line -7500403 true 150 100 220 30

butterfly
true
0
Polygon -7500403 true true 150 165 209 199 225 225 225 255 195 270 165 255 150 240
Polygon -7500403 true true 150 165 89 198 75 225 75 255 105 270 135 255 150 240
Polygon -7500403 true true 139 148 100 105 55 90 25 90 10 105 10 135 25 180 40 195 85 194 139 163
Polygon -7500403 true true 162 150 200 105 245 90 275 90 290 105 290 135 275 180 260 195 215 195 162 165
Polygon -16777216 true false 150 255 135 225 120 150 135 120 150 105 165 120 180 150 165 225
Circle -16777216 true false 135 90 30
Line -16777216 false 150 105 195 60
Line -16777216 false 150 105 105 60

car
false
0
Polygon -7500403 true true 300 180 279 164 261 144 240 135 226 132 213 106 203 84 185 63 159 50 135 50 75 60 0 150 0 165 0 225 300 225 300 180
Circle -16777216 true false 180 180 90
Circle -16777216 true false 30 180 90
Polygon -16777216 true false 162 80 132 78 134 135 209 135 194 105 189 96 180 89
Circle -7500403 true true 47 195 58
Circle -7500403 true true 195 195 58

circle
false
0
Circle -7500403 true true 0 0 300

circle 2
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240

cow
false
0
Polygon -7500403 true true 200 193 197 249 179 249 177 196 166 187 140 189 93 191 78 179 72 211 49 209 48 181 37 149 25 120 25 89 45 72 103 84 179 75 198 76 252 64 272 81 293 103 285 121 255 121 242 118 224 167
Polygon -7500403 true true 73 210 86 251 62 249 48 208
Polygon -7500403 true true 25 114 16 195 9 204 23 213 25 200 39 123

cylinder
false
0
Circle -7500403 true true 0 0 300

dot
false
0
Circle -7500403 true true 90 90 120

face happy
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 255 90 239 62 213 47 191 67 179 90 203 109 218 150 225 192 218 210 203 227 181 251 194 236 217 212 240

face neutral
false
0
Circle -7500403 true true 8 7 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Rectangle -16777216 true false 60 195 240 225

face sad
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 168 90 184 62 210 47 232 67 244 90 220 109 205 150 198 192 205 210 220 227 242 251 229 236 206 212 183

fish
false
0
Polygon -1 true false 44 131 21 87 15 86 0 120 15 150 0 180 13 214 20 212 45 166
Polygon -1 true false 135 195 119 235 95 218 76 210 46 204 60 165
Polygon -1 true false 75 45 83 77 71 103 86 114 166 78 135 60
Polygon -7500403 true true 30 136 151 77 226 81 280 119 292 146 292 160 287 170 270 195 195 210 151 212 30 166
Circle -16777216 true false 215 106 30

flag
false
0
Rectangle -7500403 true true 60 15 75 300
Polygon -7500403 true true 90 150 270 90 90 30
Line -7500403 true 75 135 90 135
Line -7500403 true 75 45 90 45

flower
false
0
Polygon -10899396 true false 135 120 165 165 180 210 180 240 150 300 165 300 195 240 195 195 165 135
Circle -7500403 true true 85 132 38
Circle -7500403 true true 130 147 38
Circle -7500403 true true 192 85 38
Circle -7500403 true true 85 40 38
Circle -7500403 true true 177 40 38
Circle -7500403 true true 177 132 38
Circle -7500403 true true 70 85 38
Circle -7500403 true true 130 25 38
Circle -7500403 true true 96 51 108
Circle -16777216 true false 113 68 74
Polygon -10899396 true false 189 233 219 188 249 173 279 188 234 218
Polygon -10899396 true false 180 255 150 210 105 210 75 240 135 240

house
false
0
Rectangle -7500403 true true 45 120 255 285
Rectangle -16777216 true false 120 210 180 285
Polygon -7500403 true true 15 120 150 15 285 120
Line -16777216 false 30 120 270 120

leaf
false
0
Polygon -7500403 true true 150 210 135 195 120 210 60 210 30 195 60 180 60 165 15 135 30 120 15 105 40 104 45 90 60 90 90 105 105 120 120 120 105 60 120 60 135 30 150 15 165 30 180 60 195 60 180 120 195 120 210 105 240 90 255 90 263 104 285 105 270 120 285 135 240 165 240 180 270 195 240 210 180 210 165 195
Polygon -7500403 true true 135 195 135 240 120 255 105 255 105 285 135 285 165 240 165 195

line
true
0
Line -7500403 true 150 0 150 300

line half
true
0
Line -7500403 true 150 0 150 150

pentagon
false
0
Polygon -7500403 true true 150 15 15 120 60 285 240 285 285 120

person
false
0
Circle -7500403 true true 110 5 80
Polygon -7500403 true true 105 90 120 195 90 285 105 300 135 300 150 225 165 300 195 300 210 285 180 195 195 90
Rectangle -7500403 true true 127 79 172 94
Polygon -7500403 true true 195 90 240 150 225 180 165 105
Polygon -7500403 true true 105 90 60 150 75 180 135 105

plant
false
0
Rectangle -7500403 true true 135 90 165 300
Polygon -7500403 true true 135 255 90 210 45 195 75 255 135 285
Polygon -7500403 true true 165 255 210 210 255 195 225 255 165 285
Polygon -7500403 true true 135 180 90 135 45 120 75 180 135 210
Polygon -7500403 true true 165 180 165 210 225 180 255 120 210 135
Polygon -7500403 true true 135 105 90 60 45 45 75 105 135 135
Polygon -7500403 true true 165 105 165 135 225 105 255 45 210 60
Polygon -7500403 true true 135 90 120 45 150 15 180 45 165 90

sheep
false
15
Circle -1 true true 203 65 88
Circle -1 true true 70 65 162
Circle -1 true true 150 105 120
Polygon -7500403 true false 218 120 240 165 255 165 278 120
Circle -7500403 true false 214 72 67
Rectangle -1 true true 164 223 179 298
Polygon -1 true true 45 285 30 285 30 240 15 195 45 210
Circle -1 true true 3 83 150
Rectangle -1 true true 65 221 80 296
Polygon -1 true true 195 285 210 285 210 240 240 210 195 210
Polygon -7500403 true false 276 85 285 105 302 99 294 83
Polygon -7500403 true false 219 85 210 105 193 99 201 83

square
false
0
Rectangle -7500403 true true 30 30 270 270

square 2
false
0
Rectangle -7500403 true true 30 30 270 270
Rectangle -16777216 true false 60 60 240 240

star
false
0
Polygon -7500403 true true 151 1 185 108 298 108 207 175 242 282 151 216 59 282 94 175 3 108 116 108

target
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240
Circle -7500403 true true 60 60 180
Circle -16777216 true false 90 90 120
Circle -7500403 true true 120 120 60

tree
false
0
Circle -7500403 true true 118 3 94
Rectangle -6459832 true false 120 195 180 300
Circle -7500403 true true 65 21 108
Circle -7500403 true true 116 41 127
Circle -7500403 true true 45 90 120
Circle -7500403 true true 104 74 152

triangle
false
0
Polygon -7500403 true true 150 30 15 255 285 255

triangle 2
false
0
Polygon -7500403 true true 150 30 15 255 285 255
Polygon -16777216 true false 151 99 225 223 75 224

truck
false
0
Rectangle -7500403 true true 4 45 195 187
Polygon -7500403 true true 296 193 296 150 259 134 244 104 208 104 207 194
Rectangle -1 true false 195 60 195 105
Polygon -16777216 true false 238 112 252 141 219 141 218 112
Circle -16777216 true false 234 174 42
Rectangle -7500403 true true 181 185 214 194
Circle -16777216 true false 144 174 42
Circle -16777216 true false 24 174 42
Circle -7500403 false true 24 174 42
Circle -7500403 false true 144 174 42
Circle -7500403 false true 234 174 42

turtle
true
0
Polygon -10899396 true false 215 204 240 233 246 254 228 266 215 252 193 210
Polygon -10899396 true false 195 90 225 75 245 75 260 89 269 108 261 124 240 105 225 105 210 105
Polygon -10899396 true false 105 90 75 75 55 75 40 89 31 108 39 124 60 105 75 105 90 105
Polygon -10899396 true false 132 85 134 64 107 51 108 17 150 2 192 18 192 52 169 65 172 87
Polygon -10899396 true false 85 204 60 233 54 254 72 266 85 252 107 210
Polygon -7500403 true true 119 75 179 75 209 101 224 135 220 225 175 261 128 261 81 224 74 135 88 99

wheel
false
0
Circle -7500403 true true 3 3 294
Circle -16777216 true false 30 30 240
Line -7500403 true 150 285 150 15
Line -7500403 true 15 150 285 150
Circle -7500403 true true 120 120 60
Line -7500403 true 216 40 79 269
Line -7500403 true 40 84 269 221
Line -7500403 true 40 216 269 79
Line -7500403 true 84 40 221 269

wolf
false
0
Polygon -16777216 true false 253 133 245 131 245 133
Polygon -7500403 true true 2 194 13 197 30 191 38 193 38 205 20 226 20 257 27 265 38 266 40 260 31 253 31 230 60 206 68 198 75 209 66 228 65 243 82 261 84 268 100 267 103 261 77 239 79 231 100 207 98 196 119 201 143 202 160 195 166 210 172 213 173 238 167 251 160 248 154 265 169 264 178 247 186 240 198 260 200 271 217 271 219 262 207 258 195 230 192 198 210 184 227 164 242 144 259 145 284 151 277 141 293 140 299 134 297 127 273 119 270 105
Polygon -7500403 true true -1 195 14 180 36 166 40 153 53 140 82 131 134 133 159 126 188 115 227 108 236 102 238 98 268 86 269 92 281 87 269 103 269 113

x
false
0
Polygon -7500403 true true 270 75 225 30 30 225 75 270
Polygon -7500403 true true 30 75 75 30 270 225 225 270
@#$#@#$#@
NetLogo 6.4.0
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
default
0.0
-0.2 0 0.0 1.0
0.0 1 1.0 0.0
0.2 0 0.0 1.0
link direction
true
0
Line -7500403 true 150 150 90 180
Line -7500403 true 150 150 210 180
@#$#@#$#@
0
@#$#@#$#@
