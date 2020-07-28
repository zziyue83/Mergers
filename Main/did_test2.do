
clear all

set more off

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
egen weights1 = total(pre_vol), by(upc)
egen weights2 = total(pre_vol), by(dma_code)
replace weights1 = round(weights1)
replace weights2 = round(weights2)


* No Fixed-Effects
reg lprice post_merger_merging post_merger trend, vce(cluster dma_code)
est sto NO_FE
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE") replace

* Product/Market Fixed-Effects
areg lprice post_merger_merging post_merger trend, abs(entity_effects) vce(cluster dma_code)
est sto PM_FE
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE") append


* Product/Market and Time Fixed-Effects
reghdfe lprice post_merger_merging, abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE") append


/********************************/
/*      NEW SPECIFICATIONS     */
/******************************/

* Calendar Fixed-Effects
areg lprice post_merger_merging post_merger trend, abs(time_calendar) vce(cluster dma_code)
est sto PMT_C
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE") append

* Dma-Specific Time Trends
reghdfe lprice post_merger_merging post_merger, abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends") append




* No Fixed-Effects, but with Major
reg lprice post_merger_merging post_merger post_merger_major trend, vce(cluster dma_code)
est sto NO_FE_M
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Major") append


* Product/market Fixed-Effects (Time Trend)
areg lprice post_merger_merging post_merger post_merger_major trend, abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_M
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, Major") append


* Product/market and Time Fixed-Effects
reghdfe lprice post_merger_merging post_merger_major, abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_M
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Major") append


/*******************************/
/*     NEW SPECIFICATIONS     */
/*****************************/

areg lprice post_merger_merging post_merger post_merger_major trend, abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_M
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Major") append

reghdfe lprice post_merger_merging post_merger post_merger_major, abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_M
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Major") append

/******************************/
/******************************/
/******************************/



* No Fixed-Effects, DHHI
reg lprice post_merger_dhhi post_merger trend, vce(cluster dma_code)
est sto NO_FE_DHHI
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, DHHI") append

* Product/market Fixed-Effects, DHHI
areg lprice post_merger_dhhi post_merger trend, abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_DHHI
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, DHHI") append

*Product/market and Time Fixed-Effects, DHHI.
reghdfe lprice post_merger_dhhi, abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_DHHHI
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Major") append


/******************************/
/*      NEW SPECIFICATIONS    */
/******************************/

areg lprice post_merger_dhhi post_merger trend, abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_DHHI
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, DHHI") append

reghdfe lprice post_merger_dhhi post_merger, abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_DHHI
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, DHHI") append

/******************************/
/******************************/
/******************************/




/********************************/
/*     NAIVE SPECIFICATIONS    */
/******************************/


gen np_dhhi = post_merger*dhhi
gen np_HHI = post_merger*post_hhi

*No FE

*No Fixed-Effects naive DHHI and post-HHI
reg lprice post_hhi dhhi post_merger np_dhhi np_HHI trend, vce(cluster dma_code)
est sto np_D_H
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Naive DHHI & post HHI") append

*No Fixed-Effects naive post-HHI
reg lprice post_hhi post_merger np_HHI trend, vce(cluster dma_code)
est sto np_H
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Naive post HHI") append

*No Fixed-Effects naive DHHI
reg lprice dhhi post_merger np_dhhi trend, vce(cluster dma_code)
est sto np_D
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Naive DHHI") append

*Product/market FE

*Product/market Fixed-Effects, naive DHHI and post-HHI
areg lprice post_hhi dhhi post_merger np_dhhi np_HHI trend, abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_D_H
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI & post HHI") append

*Product/market Fixed-Effects, naive post-HHI
areg lprice post_hhi post_merger np_HHI trend, abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_H
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive post HHI") append

*Product/market Fixed-Effects, naive DHHI
areg lprice dhhi post_merger np_dhhi trend, abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_D
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI") append

*Product/Market and Time FE

*Product/market Fixed-Effects, naive DHHI and post-HHI
reghdfe lprice np_dhhi np_HHI, abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_np_D_H
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI & post HHI") append

*Product/market Fixed-Effects, naive post-HHI
reghdfe lprice np_HHI, abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_np_H
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive post HHI") append

*Product/market Fixed-Effects, naive DHHI
reghdfe lprice np_dhhi, abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_np_D
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI") append




/******************************/
/*      NEW SPECIFICATIONS    */
/******************************/

*Calendar Fixed-Effects, naive DHHI and post-HHI
areg lprice post_hhi dhhi post_merger np_dhhi np_HHI trend, abs(time_calendar) vce(cluster dma_code)
est sto PMT_FE_t_np_D_H
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Naive DHHI & post HHI") append

*Calendar Fixed-Effects, naive DHHI and post-HHI
reghdfe lprice post_hhi dhhi post_merger np_dhhi np_HHI trend, abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_FE_t_np_D_H
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive DHHI & post HHI") append

*Calendar Fixed-Effects, naive post-HHI
areg lprice post_hhi post_merger np_HHI trend, abs(time_calendar) vce(cluster dma_code)
est sto PMT_FE_t_np_H
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Naive post HHI") append

*Calendar Fixed-Effects, naive post-HHI
reghdfe lprice post_hhi post_merger np_HHI trend, abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_FE_t_np_H
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive post HHI") append

*Calendar Fixed-Effects, naive DHHI
areg lprice dhhi post_merger np_dhhi trend, abs(time_calendar) vce(cluster dma_code)
est sto PMT_FE_t_np_D
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Naive DHHI") append

*Calendar Fixed-Effects, naive DHHI
reghdfe lprice dhhi post_merger np_dhhi trend, abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_FE_t_np_D
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive DHHI") append



/******************************/
/******************************/
/******************************/






* No Fixed-Effects, Demographics
reg lprice post_merger_merging post_merger trend log_hhinc_per_person_adj, vce(cluster dma_code)
est sto NO_FE_d
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Demographics") append

* Product/market Fixed-Effects, Demographics
areg lprice post_merger_merging post_merger trend log_hhinc_per_person_adj, abs(entity_effects) vce(cluster dma_code)
*note: this one  seemed to have both Time F-E and Time-Trends*
est sto PM_FE_d
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Demographics") append

* Product/market and Time Fixed-Effects, Demographics
reghdfe lprice post_merger_merging log_hhinc_per_person_adj, abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_d
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Demographics") append


/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_merging post_merger log_hhinc_per_person_adj trend, abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_d
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Demographics") append

reghdfe lprice post_merger_merging post_merger log_hhinc_per_person_adj, abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_d
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Demographics") append

/******************************/
/******************************/
/******************************/


* No Fixed-Effects, Demographics, but with Major
reg lprice post_merger_merging post_merger post_merger_major trend log_hhinc_per_person_adj, vce(cluster dma_code)
est sto NO_FE_d_M
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Major, Demographics") append

*Products/market Fixed-Effects, Major, Demographics
areg lprice post_merger_merging post_merger post_merger_major trend log_hhinc_per_person_adj, abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_d_M
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, Major, Demographics") append

*Products/market and Time Fixed-Effects, Major, Demographics
reghdfe lprice post_merger_merging post_merger_major log_hhinc_per_person_adj, abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_d_M
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Major, Demographics") append

/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_merging post_merger post_merger_major log_hhinc_per_person_adj trend, abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_d_M
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Major, Demographics") append

reghdfe lprice post_merger_merging post_merger post_merger_major log_hhinc_per_person_adj, abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_d_M
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Major, Demographics") append

/******************************/
/******************************/
/******************************/

*No Fixed-Effects, DHHI, Demographics
reg lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj, vce(cluster dma_code)
est sto NO_FE_DHHI_d
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, DHHI, Demographics") append

*Product/market Fixed-Effects, DHHI, Demographics
areg lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj, abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_DHHI_d
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, DHHI, Demographics") append

*Product/market and Time Fixed-Effects, DHHI, Demographics
reghdfe lprice post_merger_dhhi log_hhinc_per_person_adj, abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_DHHI_d
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, DHHI, Demographics") append

/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj, abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_d_D
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, DHHI, Demographics") append

reghdfe lprice post_merger_dhhi post_merger log_hhinc_per_person_adj, abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_d_D
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, DHHI, Demographics") append

/******************************/
/******************************/
/******************************/



/******************************/
/******************************/
/******************************/
/******************************/
/*********WEIGHTS1*************/
/******************************/
/******************************/
/******************************/
/******************************/



/*CHECKED!*/
* No Fixed-Effects
reg lprice post_merger_merging post_merger trend [aw = weights1], vce(cluster dma_code)
est sto NO_FE_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE") replace

/*CHECKED!*/
* Product/Market Fixed-Effects
areg lprice post_merger_merging post_merger trend [aw = weights1], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE") append

/*CHECK HOW THEY TREAT SINGLETONS!*/
/*NON-CHECKED YET*/
* Product/Market and Time Fixed-Effects
reghdfe lprice post_merger_merging [aw = weights1], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE") append


/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_merging post_merger trend [aw = weights1], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE") append

reghdfe lprice post_merger_merging post_merger [aw = weights1], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends") append

/******************************/
/******************************/
/******************************/



/********************************/
/*     NAIVE SPECIFICATIONS    */
/******************************/


reg lprice post_hhi dhhi post_merger np_dhhi np_HHI trend [aw = weights1], vce(cluster dma_code)
est sto np_D_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Naive DHHI & post HHI") append

reg lprice post_hhi post_merger np_HHI trend [aw = weights1], vce(cluster dma_code)
est sto np_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Naive post HHI") append

reg lprice dhhi post_merger np_dhhi trend [aw = weights1], vce(cluster dma_code)
est sto np_D_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Naive DHHI") append

/******************************/
/******************************/
/******************************/



/*CHECKED!*/
* No Fixed-Effects, but with Major
reg lprice post_merger_merging post_merger post_merger_major trend [aw = weights1], vce(cluster dma_code)
est sto NO_FE_M_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Major") append

/*CHECKED!*/
* Product/market Fixed-Effects (Time Trend)
areg lprice post_merger_merging post_merger post_merger_major trend [aw = weights1], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_M_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, Major") append

/*CHECK HOW THEY TREAT SINGLETONS!*/
/*NON-CHECKED YET*/
* Product/market and Time Fixed-Effects
reghdfe lprice post_merger_merging post_merger_major [aw = weights1], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_M_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Major") append


/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_merging post_merger post_merger_major trend [aw = weights1], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_M_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Major") append

reghdfe lprice post_merger_merging post_merger post_merger_major [aw = weights1], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_M_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Major") append

/******************************/
/******************************/
/******************************/



* No Fixed-Effects, DHHI
reg lprice post_merger_dhhi post_merger trend [aw = weights1], vce(cluster dma_code)
est sto NO_FE_DHHI_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, DHHI") append

* Product/market Fixed-Effects, DHHI
areg lprice post_merger_dhhi post_merger trend [aw = weights1], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_DHHI_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, DHHI") append

*Product/market and Time Fixed-Effects, DHHI.
reghdfe lprice post_merger_dhhi [aw = weights1], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_DHHHI_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Major") append


/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_dhhi post_merger trend [aw = weights1], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_DHHI_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, DHHI") append

reghdfe lprice post_merger_dhhi post_merger [aw = weights1], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_DHHI_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, DHHI") append

/******************************/
/******************************/
/******************************/




/********************************/
/*     NAIVE SPECIFICATIONS    */
/******************************/


*No FE

*No Fixed-Effects naive DHHI and post-HHI
reg lprice post_hhi dhhi post_merger np_dhhi np_HHI trend [aw = weights1], vce(cluster dma_code)
est sto np_D_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Naive DHHI & post HHI") append

*No Fixed-Effects naive post-HHI
reg lprice post_hhi post_merger np_HHI trend [aw = weights1], vce(cluster dma_code)
est sto np_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Naive post HHI") append

*No Fixed-Effects naive DHHI
reg lprice dhhi post_merger np_dhhi trend [aw = weights1], vce(cluster dma_code)
est sto np_D_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Naive DHHI") append

*Product/market FE

*Product/market Fixed-Effects, naive DHHI and post-HHI
areg lprice post_hhi dhhi post_merger np_dhhi np_HHI trend [aw = weights1], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_D_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI & post HHI") append

*Product/market Fixed-Effects, naive post-HHI
areg lprice post_hhi post_merger np_HHI trend [aw = weights1], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive post HHI") append

*Product/market Fixed-Effects, naive DHHI
areg lprice dhhi post_merger np_dhhi trend [aw = weights1], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_D_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI") append

*Product/Market and Time FE

*Product/market Fixed-Effects, naive DHHI and post-HHI
reghdfe lprice np_dhhi np_HHI [aw = weights1], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_np_D_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI & post HHI") append

*Product/market Fixed-Effects, naive post-HHI
reghdfe lprice np_HHI [aw = weights1], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_np_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive post HHI") append

*Product/market Fixed-Effects, naive DHHI
reghdfe lprice np_dhhi [aw = weights1], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_np_D_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI") append


/******************************/
/*      NEW SPECIFICATIONS    */
/******************************/

*Calendar Fixed-Effects, naive DHHI and post-HHI
areg lprice post_hhi dhhi post_merger np_dhhi np_HHI trend [aw = weights1], abs(time_calendar) vce(cluster dma_code)
est sto PMT_FE_t_np_D_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Naive DHHI & post HHI") append

*Calendar Fixed-Effects, naive DHHI and post-HHI
reghdfe lprice post_hhi dhhi post_merger np_dhhi np_HHI trend [aw = weights1], abs(time_calendar) vce(cluster dma_code) keepsingletons
est sto PMT_FE_t_np_D_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive DHHI & post HHI") append

*Calendar Fixed-Effects, naive post-HHI
areg lprice post_hhi post_merger np_HHI trend [aw = weights1], abs(time_calendar) vce(cluster dma_code)
est sto PMT_FE_t_np_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Naive post HHI") append

*Calendar Fixed-Effects, naive post-HHI
reghdfe lprice post_hhi post_merger np_HHI trend [aw = weights1], abs(time_calendar) vce(cluster dma_code) keepsingletons
est sto PMT_FE_t_np_H_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive post HHI") append

*Calendar Fixed-Effects, naive DHHI
areg lprice dhhi post_merger np_dhhi trend [aw = weights1], abs(time_calendar) vce(cluster dma_code)
est sto PMT_FE_t_np_D_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Naive DHHI") append

*Calendar Fixed-Effects, naive DHHI
reghdfe lprice dhhi post_merger np_dhhi trend [aw = weights1], abs(time_calendar) vce(cluster dma_code) keepsingletons
est sto PMT_FE_t_np_D_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive DHHI") append



/******************************/
/******************************/
/******************************/



* No Fixed-Effects, Demographics
reg lprice post_merger_merging post_merger trend log_hhinc_per_person_adj [aw = weights1], vce(cluster dma_code)
est sto NO_FE_d_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Demographics") append

* Product/market Fixed-Effects, Demographics
areg lprice post_merger_merging post_merger trend log_hhinc_per_person_adj [aw = weights1], abs(entity_effects) vce(cluster dma_code)
*note: this one  seemed to have both Time F-E and Time-Trends*
est sto PM_FE_d_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Demographics") append

* Product/market and Time Fixed-Effects, Demographics
reghdfe lprice post_merger_merging log_hhinc_per_person_adj [aw = weights1], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_d_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Demographics") append


/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_merging post_merger log_hhinc_per_person_adj trend [aw = weights1], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_d_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Demographics") append

reghdfe lprice post_merger_merging post_merger log_hhinc_per_person_adj [aw = weights1], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_d_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Demographics") append

/******************************/
/******************************/
/******************************/


* No Fixed-Effects, Demographics, but with Major
reg lprice post_merger_merging post_merger post_merger_major trend log_hhinc_per_person_adj [aw = weights1], vce(cluster dma_code)
est sto NO_FE_d_M_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Major, Demographics") append

*Products/market Fixed-Effects, Major, Demographics
areg lprice post_merger_merging post_merger post_merger_major trend log_hhinc_per_person_adj [aw = weights1], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_d_M_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, Major, Demographics") append

*Products/market and Time Fixed-Effects, Major, Demographics
reghdfe lprice post_merger_merging post_merger_major log_hhinc_per_person_adj [aw = weights1], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_d_M_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Major, Demographics") append

/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_merging post_merger post_merger_major log_hhinc_per_person_adj trend [aw = weights1], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_d_M_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Major, Demographics") append

reghdfe lprice post_merger_merging post_merger post_merger_major log_hhinc_per_person_adj [aw = weights1], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_d_M_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Major, Demographics") append

/******************************/
/******************************/
/******************************/

*No Fixed-Effects, DHHI, Demographics
reg lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj [aw = weights1], vce(cluster dma_code)
est sto NO_FE_DHHI_d_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, DHHI, Demographics") append

*Product/market Fixed-Effects, DHHI, Demographics
areg lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj [aw = weights1], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_DHHI_d_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, DHHI, Demographics") append

*Product/market and Time Fixed-Effects, DHHI, Demographics
reghdfe lprice post_merger_dhhi log_hhinc_per_person_adj [aw = weights1], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_DHHI_d_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, DHHI, Demographics") append

/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj [aw = weights1], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_d_D_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, DHHI, Demographics") append

reghdfe lprice post_merger_dhhi post_merger log_hhinc_per_person_adj [aw = weights1], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_d_D_w1
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, DHHI, Demographics") append

/******************************/
/******************************/
/******************************/




/******************************/
/******************************/
/******************************/
/******************************/
/*********WEIGHTS2*************/
/******************************/
/******************************/
/******************************/
/******************************/


/*CHECKED!*/
* No Fixed-Effects
reg lprice post_merger_merging post_merger trend [aw = weights2], vce(cluster dma_code)
est sto NO_FE_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE") replace

/*CHECKED!*/
* Product/Market Fixed-Effects
areg lprice post_merger_merging post_merger trend [aw = weights2], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE") append

/*CHECK HOW THEY TREAT SINGLETONS!*/
/*NON-CHECKED YET*/
* Product/Market and Time Fixed-Effects
reghdfe lprice post_merger_merging [aw = weights2], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE") append


/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_merging post_merger trend [aw = weights2], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE") append

reghdfe lprice post_merger_merging post_merger [aw = weights2], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends") append

/******************************/
/******************************/
/******************************/



/*CHECKED!*/
* No Fixed-Effects, but with Major
reg lprice post_merger_merging post_merger post_merger_major trend [aw = weights2], vce(cluster dma_code)
est sto NO_FE_M_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Major") append

/*CHECKED!*/
* Product/market Fixed-Effects (Time Trend)
areg lprice post_merger_merging post_merger post_merger_major trend [aw = weights2], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_M_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, Major") append

/*CHECK HOW THEY TREAT SINGLETONS!*/
/*NON-CHECKED YET*/
* Product/market and Time Fixed-Effects
reghdfe lprice post_merger_merging post_merger_major [aw = weights2], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_M_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Major") append


/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_merging post_merger post_merger_major trend [aw = weights2], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_M_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Major") append

reghdfe lprice post_merger_merging post_merger post_merger_major [aw = weights2], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_M_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Major") append

/******************************/
/******************************/
/******************************/



* No Fixed-Effects, DHHI
reg lprice post_merger_dhhi post_merger trend [aw = weights2], vce(cluster dma_code)
est sto NO_FE_DHHI_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, DHHI") append

* Product/market Fixed-Effects, DHHI
areg lprice post_merger_dhhi post_merger trend [aw = weights2], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_DHHI_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, DHHI") append

*Product/market and Time Fixed-Effects, DHHI.
reghdfe lprice post_merger_dhhi [aw = weights2], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_DHHHI_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Major") append


/******************************/
/*CHECK THIS NEW SPECIFICATIONS*/
/******************************/

areg lprice post_merger_dhhi post_merger trend [aw = weights2], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_DHHI_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, DHHI") append

reghdfe lprice post_merger_dhhi post_merger [aw = weights2], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_DHHI_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, DHHI") append

/******************************/
/******************************/
/******************************/


* No Fixed-Effects, Demographics
reg lprice post_merger_merging post_merger trend log_hhinc_per_person_adj [aw = weights2], vce(cluster dma_code)
est sto NO_FE_d_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Demographics") append

* Product/market Fixed-Effects, Demographics
areg lprice post_merger_merging post_merger trend log_hhinc_per_person_adj [aw = weights2], abs(entity_effects) vce(cluster dma_code)
*note: this one  seemed to have both Time F-E and Time-Trends*
est sto PM_FE_d_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Demographics") append

* Product/market and Time Fixed-Effects, Demographics
reghdfe lprice post_merger_merging log_hhinc_per_person_adj [aw = weights2], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_d_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Demographics") append


/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_merging post_merger log_hhinc_per_person_adj trend [aw = weights2], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_d_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Demographics") append

reghdfe lprice post_merger_merging post_merger log_hhinc_per_person_adj [aw = weights2], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_d_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Demographics") append

/******************************/
/******************************/
/******************************/




/********************************/
/*     NAIVE SPECIFICATIONS    */
/******************************/


*No FE

*No Fixed-Effects naive DHHI and post-HHI
reg lprice post_hhi dhhi post_merger np_dhhi np_HHI trend [aw = weights2], vce(cluster dma_code)
est sto np_D_H_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Naive DHHI & post HHI") append

*No Fixed-Effects naive post-HHI
reg lprice post_hhi post_merger np_HHI trend [aw = weights2], vce(cluster dma_code)
est sto np_H_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Naive post HHI") append

*No Fixed-Effects naive DHHI
reg lprice dhhi post_merger np_dhhi trend [aw = weights2], vce(cluster dma_code)
est sto np_D_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Naive DHHI") append

*Product/market FE

*Product/market Fixed-Effects, naive DHHI and post-HHI
areg lprice post_hhi dhhi post_merger np_dhhi np_HHI trend [aw = weights2], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_D_H_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI & post HHI") append

*Product/market Fixed-Effects, naive post-HHI
areg lprice post_hhi post_merger np_HHI trend [aw = weights2], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_H_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive post HHI") append

*Product/market Fixed-Effects, naive DHHI
areg lprice dhhi post_merger np_dhhi trend [aw = weights2], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_np_D_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI") append

*Product/Market and Time FE

*Product/market Fixed-Effects, naive DHHI and post-HHI
reghdfe lprice np_dhhi np_HHI [aw = weights2], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_np_D_H_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI & post HHI") append

*Product/market Fixed-Effects, naive post-HHI
reghdfe lprice np_HHI [aw = weights2], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_np_H_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive post HHI") append

*Product/market Fixed-Effects, naive DHHI
reghdfe lprice np_dhhi [aw = weights2], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_np_D_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Products FE, Naive DHHI") append



/******************************/
/*      NEW SPECIFICATIONS    */
/******************************/

*Calendar Fixed-Effects, naive DHHI and post-HHI
areg lprice post_hhi dhhi post_merger np_dhhi np_HHI trend [aw = weights2], abs(time_calendar) vce(cluster dma_code)
est sto PMT_FE_t_np_D_H_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Naive DHHI & post HHI") append

*Calendar Fixed-Effects, naive DHHI and post-HHI
reghdfe lprice post_hhi dhhi post_merger np_dhhi np_HHI trend [aw = weights2], abs(time_calendar) vce(cluster dma_code) keepsingletons
est sto PMT_FE_t_np_D_H_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive DHHI & post HHI") append

*Calendar Fixed-Effects, naive post-HHI
areg lprice post_hhi post_merger np_HHI trend [aw = weights2], abs(time_calendar) vce(cluster dma_code)
est sto PMT_FE_t_np_H_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Naive post HHI") append

*Calendar Fixed-Effects, naive post-HHI
reghdfe lprice post_hhi post_merger np_HHI trend [aw = weights2], abs(time_calendar) vce(cluster dma_code) keepsingletons
est sto PMT_FE_t_np_H_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive post HHI") append

*Calendar Fixed-Effects, naive DHHI
areg lprice dhhi post_merger np_dhhi trend [aw = weights2], abs(time_calendar) vce(cluster dma_code)
est sto PMT_FE_t_np_D_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Naive DHHI") append

*Calendar Fixed-Effects, naive DHHI
reghdfe lprice dhhi post_merger np_dhhi trend [aw = weights2], abs(time_calendar) vce(cluster dma_code) keepsingletons
est sto PMT_FE_t_np_D_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Naive DHHI") append



/******************************/
/******************************/
/******************************/



* No Fixed-Effects, Demographics, but with Major
reg lprice post_merger_merging post_merger post_merger_major trend log_hhinc_per_person_adj [aw = weights2], vce(cluster dma_code)
est sto NO_FE_d_M_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, Major, Demographics") append

*Products/market Fixed-Effects, Major, Demographics
areg lprice post_merger_merging post_merger post_merger_major trend log_hhinc_per_person_adj [aw = weights2], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_d_M_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, Major, Demographics") append

*Products/market and Time Fixed-Effects, Major, Demographics
reghdfe lprice post_merger_merging post_merger_major log_hhinc_per_person_adj [aw = weights2], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_d_M_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, Major, Demographics") append

/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_merging post_merger post_merger_major log_hhinc_per_person_adj trend [aw = weights2], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_d_M_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, Major, Demographics") append

reghdfe lprice post_merger_merging post_merger post_merger_major log_hhinc_per_person_adj [aw = weights2], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_d_M_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, Major, Demographics") append

/******************************/
/******************************/
/******************************/

*No Fixed-Effects, DHHI, Demographics
reg lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj [aw = weights2], vce(cluster dma_code)
est sto NO_FE_DHHI_d_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("No FE, DHHI, Demographics") append

*Product/market Fixed-Effects, DHHI, Demographics
areg lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj [aw = weights2], abs(entity_effects) vce(cluster dma_code)
est sto PM_FE_DHHI_d_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product FE, DHHI, Demographics") append

*Product/market and Time Fixed-Effects, DHHI, Demographics
reghdfe lprice post_merger_dhhi log_hhinc_per_person_adj [aw = weights2], abs(entity_effects time_effects) vce(cluster dma_code) keepsingletons
est sto PMT_FE_DHHI_d_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Time FE, DHHI, Demographics") append

/******************************/
/*     NEW SPECIFICATIONS     */
/******************************/

areg lprice post_merger_dhhi post_merger trend log_hhinc_per_person_adj [aw = weights2], abs(time_calendar) vce(cluster dma_code)
est sto PMT_C_d_D_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("Calendar FE, DHHI, Demographics") append

reghdfe lprice post_merger_dhhi post_merger log_hhinc_per_person_adj [aw = weights2], abs(dma_code##c.trend) vce(cluster dma_code) keepsingletons
est sto PMT_t_d_D_w2
outreg2 using `2'/did_stata_`3'.txt, stats(coef se pval) ctitle("DMA/Product Trends, DHHI, Demographics") append

/******************************/
/******************************/
/******************************/












est clear


exit, STATA clear






.
