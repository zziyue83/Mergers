
clear all

set more off

est clear

/* *args: input_path       = `1' */
/* *args: output_path      = `2' */
/* *args: month_or_quarter = `3' */
/* *args: routine          = `4' */
/* *args: spec             = `5' */
/* *args: chars            = `6' */


cd `1'
log using `2'/compute_demand_`3', text replace

import delimited "demand_`3'.csv", encoding(ISO-8859-1)

/*Install Packages*/

ssc install outreg2
ssc install ftools
ssc install reghdfe
ssc install estout
ssc install ivreghdfe


if `4' == "Nested_Logit" {

	if `5' == "Linear_Fe"{

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 (prices log_within_nest_shares = demand*), abs(dma_code upc) cluster(dma_code) first savefirst savefprefix(st1)
		esttab est1 st1* using `2'/demand_results_`3'.tex, replace

	}

	else {

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 `6' (prices log_within_nest_shares = demand*), abs(dma_code) cluster(dma_code) first savefirst savefprefix(st1)
		esttab est1 st1* using `2'/demand_results_`3'.tex, replace

	}
}


else `4' == "Logit" {

	if `5' == "Linear_Fe"{

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 (prices = demand*), abs(dma_code upc) cluster(dma_code) first savefirst savefprefix(st1)
		esttab est1 st1* using `2'/demand_results_`3'.tex, replace

	}

	else {

		eststo clear
		*IVHDFE WITH FIRST STAGE
		eststo: ivreghdfe logsj_logs0 `6' (prices = demand*), abs(dma_code) cluster(dma_code) first savefirst savefprefix(st1)
		esttab est1 st1* using `2'/demand_results_`3'.tex, replace

	}
}


