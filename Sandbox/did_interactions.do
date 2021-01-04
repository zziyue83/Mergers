
clear all

set more off

est clear

/* *args coming from the python script*/
/* *args: input_path       = `1' */
/* *args: output_path      = `2' */
/* *args: month_or_quarter = `3' */
/* *args: year_completed   = `4' */
/* *args: month_completed  = `5' */


cd `1'
log using `2'/did_stata_`3', text replace

import delimited "stata_did_`3'.csv", encoding(ISO-8859-1)

/*Install Packages*/
ssc install outreg2
ssc install ftools
ssc install reghdfe
ssc install estout

/* Fixed Effects */
egen entity_effects = group(upc dma_code)

/* WEIGHTING SCHEMES */
gen pre_vol = volume * (1 - post_merger)
gen weights_0 = 1 /*to add weights that won't change things*/
egen weights_1 = total(pre_vol), by(upc)
egen weights_2 = total(pre_vol), by(dma_code)
egen weights_3 = total(pre_vol), by(upc dma_code)
replace weights_1 = round(weights_1)
replace weights_2 = round(weights_2)
replace weights_3 = round(weights_3)

/*Naive Variables*/
gen np_dhhi = post_merger*dhhi
gen np_HHI = post_merger*post_hhi

/*One Year Post*/
gen month_date = ym(year, month)
tabstat month_date if (month==`5' & year==`4'), save
matrix cutoff=r(StatTotal)
local cutoff=cutoff[1,1]
gen after = 0
replace after = 1 if month_date >= `cutoff' + 12
gen post_merger_1y = post_merger * after
gen post_merger_merging_1y = post_merger_merging * after

/*Coarse HHI Bins*/
gen HHI_bins = 0
replace HHI_bins = 1 if (post_hhi*10000>1500 & post_hhi*10000<2500)
replace HHI_bins = 2 if (post_hhi*10000>2500 & !missing(post_hhi))

/*Coarse DHHI Bins*/
gen DHHI_bins = 0
replace DHHI_bins = 1 if (dhhi*10000>100 & dhhi*10000<200)
replace DHHI_bins = 2 if (dhhi*10000>200 & !missing(dhhi))

/*Finer HHI Bins*/
gen HHI_binsf = 0
replace HHI_binsf = 1 if (post_hhi*10000>=375 & post_hhi*10000<750)
replace HHI_binsf = 2 if (post_hhi*10000>=750 & post_hhi*10000<1125)
replace HHI_binsf = 3 if (post_hhi*10000>=1125 & post_hhi*10000<1500)
replace HHI_binsf = 4 if (post_hhi*10000>=1500 & post_hhi*10000<1750)
replace HHI_binsf = 5 if (post_hhi*10000>=1750 & post_hhi*10000<2000)
replace HHI_binsf = 6 if (post_hhi*10000>=2000 & post_hhi*10000<2250)
replace HHI_binsf = 7 if (post_hhi*10000>=2250 & post_hhi*10000<2500)
replace HHI_binsf = 8 if (post_hhi*10000>=2500 & !missing(post_hhi))

/*Finer DHHI Bins*/
gen DHHI_binsf = 0
replace DHHI_binsf = 1 if (dhhi*10000>=25 & dhhi*10000<50)
replace DHHI_binsf = 2 if (dhhi*10000>=50 & dhhi*10000<75)
replace DHHI_binsf = 3 if (dhhi*10000>=75 & dhhi*10000<100)
replace DHHI_binsf = 4 if (dhhi*10000>=100 & dhhi*10000<125)
replace DHHI_binsf = 5 if (dhhi*10000>=125 & dhhi*10000<150)
replace DHHI_binsf = 6 if (dhhi*10000>=150 & dhhi*10000<175)
replace DHHI_binsf = 7 if (dhhi*10000>175 & dhhi*10000<200)
replace DHHI_binsf = 8 if (dhhi*10000>=200 & !missing(dhhi))

/*HHI and DHHI Bins*/
gen DHHI_HHI = 0
replace DHHI_HHI = 1 if (dhhi*10000>=25 & dhhi*10000<50 & post_hhi*10000>=375 & post_hhi*10000<750)
replace DHHI_HHI = 2 if (dhhi*10000>=50 & dhhi*10000<75 & post_hhi*10000>=750 & post_hhi*10000<1125)
replace DHHI_HHI = 3 if (dhhi*10000>=75 & dhhi*10000<100 & post_hhi*10000>=1125 & post_hhi*10000<1500)
replace DHHI_HHI = 4 if (dhhi*10000>=100 & dhhi*10000<125 & post_hhi*10000>=1500 & post_hhi*10000<1750)
replace DHHI_HHI = 5 if (dhhi*10000>=125 & dhhi*10000<150 & post_hhi*10000>=1750 & post_hhi*10000<2000)
replace DHHI_HHI = 6 if (dhhi*10000>=150 & dhhi*10000<175 & post_hhi*10000>=2000 & post_hhi*10000<2250)
replace DHHI_HHI = 7 if (dhhi*10000>=175 & dhhi*10000<200 & post_hhi*10000>=2250 & post_hhi*10000<2500)
replace DHHI_HHI = 8 if (dhhi*10000>=200 & !missing(dhhi) & post_hhi*10000>=2500 & !missing(post_hhi))

/*Nocke & Whinston Bins*/
gen DHHI_HHI_NW = 0
replace DHHI_HHI_NW = 1 if (dhhi*10000>=100 & dhhi*10000<200 & post_hhi*10000>=1500 & post_hhi*10000<2500)
replace DHHI_HHI_NW = 2 if (dhhi*10000>=200 & !missing(dhhi) & post_hhi*10000>2500 & !missing(post_hhi))

/*Main Routine*/
forval x = 0/3 {

* 1y After
reghdfe lprice post_merger_merging post_merger post_merger_1y post_merger_merging_1y trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)est sto PM_FE_`x'
outreg2 using `2'/did_stata_int_`3'_`x'.txt, stats(coef se pval) ctitle("1y After") replace

* HHI Coarse
reghdfe lprice post_merger_merging#i.HHI_bins post_merger#i.HHI_bins i.HHI_bins trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)est sto PM_FE_`x'
outreg2 using `2'/did_stata_int_`3'_`x'.txt, stats(coef se pval) ctitle("HHI bins") append
est clear

* DHHI Coarse
reghdfe lprice post_merger_merging#i.DHHI_bins post_merger#i.DHHI_bins i.DHHI_bins trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
outreg2 using `2'/did_stata_int_`3'_`x'.txt, stats(coef se pval) ctitle("DHHI bins") append

* HHI Fine
reghdfe lprice post_merger_merging#i.HHI_binsf post_merger#i.HHI_binsf i.HHI_binsf trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)est sto PM_FE_`x'
outreg2 using `2'/did_stata_int_`3'_`x'.txt, stats(coef se pval) ctitle("HHI bins") append
est clear

* DHHI Fine
reghdfe lprice post_merger_merging#i.DHHI_binsf post_merger#i.DHHI_binsf i.DHHI_binsf trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
outreg2 using `2'/did_stata_int_`3'_`x'.txt, stats(coef se pval) ctitle("DHHI bins") append

* DHHI & HHI Bins
reghdfe lprice post_merger_merging#i.DHHI_HHI post_merger#i.DHHI_HHI i.DHHI_HHI trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
outreg2 using `2'/did_stata_int_`3'_`x'.txt, stats(coef se pval) ctitle("DHHI & HHI bins") append

* Nocke & Whinston Regions
reghdfe lprice post_merger_merging#i.DHHI_HHI_NW post_merger#i.DHHI_HHI_NW i.DHHI_HHI_NW trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
outreg2 using `2'/did_stata_int_`3'_`x'.txt, stats(coef se pval) ctitle("NW bins") append


}


est clear




exit, STATA clear






.
