
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
bys dma_code year month: egen tot_dist = total(distance)
rename log_within_nest_shares lwns
egen period = group(year month)


if "`4'" == "Nested_Logit" {

	if "`5'" == "Linear_FE" {

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 (prices lwns = demand_instruments0 tot_dist N_upc), abs(dma_code upc period) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		esttab est1 st1* using `2'/demand_results_`3'.tex, stats(N r2 F APF1 APF2, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest")) replace
		outreg2 est1 st1* using `2'/demand_results_`3'.txt, replace
		*REGHDFE OLS
		reghdfe logsj_logs0 prices lwns, abs(dma_code upc period) cluster(dma_code)
		outreg2 using `2'/demand_results_`3'.txt, stats(coef se) append


	}

	else if "`5'" == "Chars" {

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 chars* (prices lwns = demand_instruments0 tot_dist N_upc), abs(dma_code period) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		esttab est1 st1* using `2'/demand_results_`3'.tex, stats(N r2 F APF1 APF2, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest")) replace
		outreg2 est1 st1* using `2'/demand_results_`3'.txt, replace
		*REGHDFE OLS
		reghdfe logsj_logs0 prices lwns chars*, abs(dma_code period) cluster(dma_code)
		outreg2 using `2'/demand_results_`3'.txt, stats(coef se) append

	}
}


else if "`4'" == "Logit" {

	if "`5'" == "Linear_FE" {

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 (prices = demand_instruments0 tot_dist N_upc), abs(dma_code upc period) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		esttab est1 st1* using `2'/demand_results_`3'.tex, stats(N r2 F APF1 APF2, labels("Observations" "R-squared" "F-statistic" "F-prices")) replace
		outreg2 est1 st1* using `2'/demand_results_`3'.txt, replace
		*REGHDFE OLS
		reghdfe logsj_logs0 prices, abs(dma_code upc period) cluster(dma_code)
		outreg2 using `2'/demand_results_`3'.txt, stats(coef se) append

	}

	else if "`5'" == "Chars" {

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 chars* (prices = demand_instruments0 tot_dist N_upc), abs(dma_code period) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		esttab est1 st1* using `2'/demand_results_`3'.tex, stats(N r2 F APF1 APF2, labels("Observations" "R-squared" "F-statistic" "F-prices")) replace
		outreg2 est1 st1* using `2'/demand_results_`3'.txt, replace
		*REGHDFE OLS
		reghdfe logsj_logs0 prices chars*, abs(dma_code period) cluster(dma_code)
		outreg2 using `2'/demand_results_`3'.txt, stats(coef se) append


	}
}




exit, STATA clear






