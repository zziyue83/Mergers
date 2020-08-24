
clear all

set more off

est clear

/* *args: input_path       = `1' */
/* *args: output_path      = `2' */
/* *args: month_or_quarter = `3' */
/* *args: routine          = `4' */
/* *args: spec             = `5' */


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

di "`4'"
di "`5'"

if "`4'" == "Nested_Logit" {

	if "`5'" == "Linear_FE" {

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 (prices log_within_nest_shares = demand*), abs(dma_code upc) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		esttab est1 st1* using `2'/demand_results_`3'.tex, stats(N r2 F APF1 APF2, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest")) replace
		outreg2 est1 st1* using `2'/demand_results_`3'.txt, replace


	}

	else if "`5'" == "Chars" {

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 chars* (prices log_within_nest_shares = demand*), abs(dma_code) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		esttab est1 st1* using `2'/demand_results_`3'.tex, stats(N r2 F APF1 APF2, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest")) replace
		outreg2 est1 st1* using `2'/demand_results_`3'.txt, replace


	}
}


else if "`4'" == "Logit" {

	if "`5'" == "Linear_FE" {

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 (prices = demand*), abs(dma_code upc) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		esttab est1 st1* using `2'/demand_results_`3'.tex, stats(N r2 F APF1 APF2, labels("Observations" "R-squared" "F-statistic" "F-prices")) replace
		outreg2 est1 st1* using `2'/demand_results_`3'.txt, replace


	}

	else if "`5'" == "Chars" {

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 chars* (prices = demand*), abs(dma_code) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		esttab est1 st1* using `2'/demand_results_`3'.tex, stats(N r2 F APF1 APF2, labels("Observations" "R-squared" "F-statistic" "F-prices")) replace
		outreg2 est1 st1* using `2'/demand_results_`3'.txt, replace


	}
}




exit, STATA clear






