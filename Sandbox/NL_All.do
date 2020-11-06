
clear all

set more off

est clear

/* *args: input_path       = `1' */
/* *args: output_path      = `2' */
/* *args: month_or_quarter = `3' */
/* *args: routine          = `4' */
/* *args: spec             = `5' */

di "`3'"
cd `1'
log using `2'/compute_demand_`3', text replace

import delimited "demand_`3'.csv", encoding(ISO-8859-1)

/*Install Packages*/

ssc install outreg2, replace
ssc install ranktest, replace
ssc install ivreg2, replace
ssc install ftools, replace
ssc install reghdfe, replace
ssc install estout, replace
ssc install ivreghdfe, replace
ssc install unique, replace
ssc install lassopack, replace
ssc install pdslasso, replace

di "`4'"
di "`5'"

qui unique upc, by(dma_code year month nesting_ids) gen(N_upc)
bysort dma_code year month nesting_ids: egen N_UPC = mean(N_upc)
bys dma_code year month: egen tot_dist = total(distance)
rename log_within_nest_shares lwns
egen period = group(year month)
egen calendar = group(month)

sort dma_code upc year month
foreach inst of varlist demand* {
	forval x=1/12{
		gen lag_`x'_`inst' = `inst'[_n-`x'] if (upc[_n] == upc[_n-`x'] & dma_code[_n] == dma_code[_n-`x'])
	}
}
*
egen UPC = group(upc)

xtset dma_code

/*NO TIME RELATED FE*/
eststo clear
*REGHDFE OLS
reghdfe logsj_logs0 prices lwns, abs(dma_code upc) cluster(dma_code)
outreg2 using `2'/NL_All_`3'.txt, stats(coef se) ctitle("OLS") replace
*IVHDFE distance_diesel tot_dist N_UPC
eststo: ivreghdfe logsj_logs0 (prices lwns = dem* tot_dist N_UPC), abs(dma_code upc) cluster(dma_code)
outreg2 using `2'/NL_All_`3'.txt, ctitle("IV") append
*IVLASSO distance_diesel tot_dist N_UPC
eststo: ivlasso logsj_logs0 (i.UPC) (prices lwns = dem* lag* N_UPC tot_dist), fe cluster(dma_code) partial(i.UPC)
outreg2 using `2'/NL_All_`3'.txt, keep(prices lwns) stat(coef se) ctitle("IV-Lasso") append

/*CALENDAR FE*/
*REGHDFE OLS
reghdfe logsj_logs0 prices lwns, abs(dma_code upc calendar) cluster(dma_code)
outreg2 using `2'/NL_All_`3'.txt, stats(coef se) ctitle("OLS Calendar") append
*IVHDFE distance_diesel tot_dist N_UPC
eststo: ivreghdfe logsj_logs0 (prices lwns = demand_instruments0 tot_dist N_UPC), abs(dma_code upc calendar) cluster(dma_code)
outreg2 using `2'/NL_All_`3'.txt, ctitle("IV Calendar") append
*IVLASSO distance_diesel tot_dist N_UPC
eststo: ivlasso logsj_logs0 (i.UPC i.calendar) (prices lwns = dem* lag* N_UPC tot_dist), fe cluster(dma_code) partial(i.UPC i.calendar)
outreg2 using `2'/NL_All_`3'.txt, keep(prices lwns) stat(coef se) ctitle("IV-Lasso Calendar") append

/*CALENDAR FE*/
*REGHDFE OLS
reghdfe logsj_logs0 prices lwns, abs(dma_code upc period) cluster(dma_code)
outreg2 using `2'/NL_All_`3'.txt, stats(coef se) ctitle("OLS Period") append
*IVHDFE distance_diesel tot_dist N_UPC
eststo: ivreghdfe logsj_logs0 (prices lwns = demand_instruments0 tot_dist N_UPC), abs(dma_code upc period) cluster(dma_code)
outreg2 using `2'/NL_All_`3'.txt, ctitle("IV Period") append
*IVLASSO distance_diesel tot_dist N_UPC
eststo: ivlasso logsj_logs0 (i.UPC i.period) (prices lwns = dem* lag* N_UPC tot_dist), fe cluster(dma_code) partial(i.UPC i.period)
outreg2 using `2'/NL_All_`3'.txt, keep(prices lwns) stat(coef se) ctitle("IV-Lasso Period") append


eststo clear


.
exit, STATA clear






