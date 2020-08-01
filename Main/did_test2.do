
clear all

set more off

est clear

/* *args: input_path       = `1' */
/* *args: output_path      = `2' */
/* *args: month_or_quarter = `3' */

cd `1'
log using `2'/did_stata_`3', text replace

import delimited "stata_did_`3'.csv", encoding(ISO-8859-1)

/*Install Packages*/

ssc install outreg2
ssc install ftools
ssc install reghdfe

/* Fixed Effects */
egen entity_effects = group(upc dma_code)
egen time_effects = group(year `3') /* same goes for month*/
egen time_calendar = group(`3') /* same goes for month*/


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



forval x = 0/3 {

* No Fixed-Effects
reg lprice post_merger_merging post_merger trend [aw = weights_`x'], vce(cluster dma_code)
est sto NO_FE_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("No FE") replace

* Product/Market Fixed-Effects
reghdfe lprice post_merger_merging post_merger trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product FE") append


* Product/Market and Time Fixed-Effects
reghdfe lprice post_merger_merging [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto PMT_FE_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Time FE") append


* Calendar Fixed-Effects
reghdfe lprice post_merger_merging post_merger trend [aw = weights_`x'], abs(time_calendar entity_effects) vce(cluster dma_code)
est sto PMT_C_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Calendar FE") append

* Dma-Specific Time Trends
reghdfe lprice post_merger_merging post_merger [aw = weights_`x'], abs(dma_code##c.trend) vce(cluster dma_code)
est sto PMT_t_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product Trends") append


*MAJOR*

* No Fixed-Effects, but with Major
reg lprice post_merger_merging post_merger post_merger_major trend [aw = weights_`x'], vce(cluster dma_code)
est sto NO_FE_M_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("No FE, Major") append


* Product/market Fixed-Effects (Time Trend)
reghdfe lprice post_merger_merging post_merger post_merger_major trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_M_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product FE, Major") append


* Product/market and Time Fixed-Effects
reghdfe lprice post_merger_merging post_merger_major [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto PMT_FE_M_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Time FE, Major") append



reghdfe lprice post_merger_merging post_merger post_merger_major trend [aw = weights_`x'], abs(time_calendar entity_effects) vce(cluster dma_code)
est sto PMT_C_M_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Calendar FE, Major") append

reghdfe lprice post_merger_merging post_merger post_merger_major [aw = weights_`x'], abs(dma_code##c.trend) vce(cluster dma_code)
est sto PMT_t_M_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Major") append

/******************************/
/******************************/
/******************************/

*DHHI

* No Fixed-Effects, DHHI
reg lprice post_merger_dhhi post_merger trend [aw = weights_`x'], vce(cluster dma_code)
est sto NO_FE_DHHI_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("No FE, DHHI") append

* Product/market Fixed-Effects, DHHI
reghdfe lprice post_merger_dhhi post_merger trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_DHHI_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product FE, DHHI") append

*Product/market and Time Fixed-Effects, DHHI.
reghdfe lprice post_merger_dhhi [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto PMT_FE_DHHHI_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Time FE, Major") append


reghdfe lprice post_merger_dhhi post_merger trend [aw = weights_`x'], abs(time_calendar entity_effects) vce(cluster dma_code)
est sto PMT_C_DHHI_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Calendar FE, DHHI") append

reghdfe lprice post_merger_dhhi post_merger [aw = weights_`x'], abs(dma_code##c.trend) vce(cluster dma_code)
est sto PMT_t_DHHI_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product Trends, DHHI") append

/******************************/
/******************************/
/******************************/


*NAIVE SPECIFICATIONS


*No FE

*No Fixed-Effects naive DHHI and post-HHI
reg lprice post_merger post_hhi dhhi np_dhhi np_HHI trend [aw = weights_`x'], vce(cluster dma_code)
est sto np_D_H_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("No FE, Naive DHHI & post HHI") append

*No Fixed-Effects naive post-HHI
reg lprice post_merger post_hhi  np_HHI trend [aw = weights_`x'], vce(cluster dma_code)
est sto np_H_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("No FE, Naive post HHI") append

*No Fixed-Effects naive DHHI
reg lprice post_merger dhhi np_dhhi trend [aw = weights_`x'], vce(cluster dma_code)
est sto np_D_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("No FE, Naive DHHI") append

*Product/market FE

*Product/market Fixed-Effects, naive DHHI and post-HHI
reghdfe lprice post_merger np_dhhi np_HHI trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_D_H_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI & post HHI") append

*Product/market Fixed-Effects, naive post-HHI
reghdfe lprice post_merger np_HHI trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_H_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive post HHI") append

*Product/market Fixed-Effects, naive DHHI
reghdfe lprice post_merger np_dhhi trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_D_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI") append

*Product/Market and Time FE

*Product/market Fixed-Effects, naive DHHI and post-HHI
reghdfe lprice np_dhhi np_HHI [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto PMT_FE_np_D_H_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI & post HHI") append

*Product/market Fixed-Effects, naive post-HHI
reghdfe lprice np_HHI [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto PMT_FE_np_H_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive post HHI") append

*Product/market Fixed-Effects, naive DHHI
reghdfe lprice np_dhhi [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto PMT_FE_np_D_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI") append


/******************************/

*Calendar Fixed-Effects, naive DHHI and post-HHI
reghdfe lprice post_merger post_hhi dhhi np_dhhi np_HHI trend [aw = weights_`x'], abs(time_calendar entity_effects) vce(cluster dma_code)
est sto PMT_FE_t_np_D_H_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Calendar FE, Naive DHHI & post HHI") append

*DMA-trends, naive DHHI and post-HHI
reghdfe lprice post_merger np_dhhi np_HHI [aw = weights_`x'], abs(dma_code##c.trend) vce(cluster dma_code)
est sto PMT_FE_t_np_D_H_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive DHHI & post HHI") append

*Calendar Fixed-Effects, naive post-HHI
reghdfe lprice post_hhi post_merger np_HHI trend [aw = weights_`x'], abs(time_calendar entity_effects) vce(cluster dma_code)
est sto PMT_FE_t_np_H_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Calendar FE, Naive post HHI") append

*DMA-trends, naive post-HHI
reghdfe lprice post_merger np_HHI [aw = weights_`x'], abs(dma_code##c.trend) vce(cluster dma_code)
est sto PMT_FE_t_np_H_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive post HHI") append

*Calendar Fixed-Effects, naive DHHI
reghdfe lprice post_merger dhhi np_dhhi trend [aw = weights_`x'], abs(time_calendar entity_effects) vce(cluster dma_code)
est sto PMT_FE_t_np_D_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Calendar FE, Naive DHHI") append

*DMA-trends, naive DHHI
reghdfe lprice post_merger np_dhhi [aw = weights_`x'], abs(dma_code##c.trend) vce(cluster dma_code)
est sto PMT_FE_t_np_D_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive DHHI") append



/******************************/
/******************************/
/******************************/






* No Fixed-Effects, Demographics
reg lprice post_merger_merging post_merger log_hhinc_per_person_adj trend [aw = weights_`x'], vce(cluster dma_code)
est sto NO_FE_d_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("No FE, Demographics") append

* Product/market Fixed-Effects, Demographics
reghdfe lprice post_merger_merging post_merger log_hhinc_per_person_adj trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
*note: this one  seemed to have both Time F-E and Time-Trends*
est sto PM_FE_d_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Products FE, Demographics") append

* Product/market and Time Fixed-Effects, Demographics
reghdfe lprice post_merger_merging log_hhinc_per_person_adj [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto PMT_FE_d_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Time FE, Demographics") append



reghdfe lprice post_merger_merging post_merger log_hhinc_per_person_adj trend [aw = weights_`x'], abs(time_calendar entity_effects) vce(cluster dma_code)
est sto PMT_C_d_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Calendar FE, Demographics") append

reghdfe lprice post_merger_merging post_merger log_hhinc_per_person_adj [aw = weights_`x'], abs(dma_code##c.trend) vce(cluster dma_code)
est sto PMT_t_d_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Demographics") append



* No Fixed-Effects, Demographics, but with Major
reg lprice post_merger_merging post_merger post_merger_major trend log_hhinc_per_person_adj [aw = weights_`x'], vce(cluster dma_code)
est sto NO_FE_d_M_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("No FE, Major, Demographics") append

*Products/market Fixed-Effects, Major, Demographics
reghdfe lprice post_merger_merging post_merger post_merger_major trend log_hhinc_per_person_adj [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_d_M_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product FE, Major, Demographics") append

*Products/market and Time Fixed-Effects, Major, Demographics
reghdfe lprice post_merger_merging post_merger_major log_hhinc_per_person_adj [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto PMT_FE_d_M_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Time FE, Major, Demographics") append


reghdfe lprice post_merger_merging post_merger post_merger_major log_hhinc_per_person_adj trend [aw = weights_`x'], abs(time_calendar entity_effects) vce(cluster dma_code)
est sto PMT_C_d_M_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Calendar FE, Major, Demographics") append

reghdfe lprice post_merger_merging post_merger post_merger_major log_hhinc_per_person_adj [aw = weights_`x'], abs(dma_code##c.trend) vce(cluster dma_code)
est sto PMT_t_d_M_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Major, Demographics") append

/******************************/
/******************************/
/******************************/

*No Fixed-Effects, DHHI, Demographics
reg lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj [aw = weights_`x'], vce(cluster dma_code)
est sto NO_FE_DHHI_d_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("No FE, DHHI, Demographics") append

*Product/market Fixed-Effects, DHHI, Demographics
reghdfe lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_DHHI_d_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product FE, DHHI, Demographics") append

*Product/market and Time Fixed-Effects, DHHI, Demographics
reghdfe lprice post_merger_dhhi log_hhinc_per_person_adj [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto PMT_FE_DHHI_d_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Time FE, DHHI, Demographics") append


reghdfe lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj [aw = weights_`x'], abs(time_calendar entity_effects) vce(cluster dma_code)
est sto PMT_C_d_D_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("Calendar FE, DHHI, Demographics") append

reghdfe lprice post_merger_dhhi post_merger log_hhinc_per_person_adj [aw = weights_`x'], abs(dma_code##c.trend) vce(cluster dma_code)
est sto PMT_t_d_D_`x'
outreg2 using `2'/did_stata_`3'_`x'.txt, stats(coef se pval) ctitle("DMA/Product Trends, DHHI, Demographics") append

/******************************/
/******************************/
/******************************/




est clear


}


exit, STATA clear






.
