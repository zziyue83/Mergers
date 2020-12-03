
clear all

set more off

est clear

/* *args: input_path       = `1' */
/* *args: output_path      = `2' */
/* *args: year             = `3' */
/* *args: month            = `4' */



cd `1'
log using `2'/cross_valid_`3', text replace

import delimited "demand_`3'.csv", encoding(ISO-8859-1)

/*

This Routine calculates predicted share for observations "out of sample"
and gets the mean squared error of the prediction. Repeats this through "i"
and delivers an excel called MSE that has the MSE of each "i" for every model.
After that it prints tables for each model calculated on the whole sample.

*/

/*Install Packages*/

ssc install outreg2, replace
ssc install ranktest, replace
ssc install ivreg2, replace
ssc install ftools, replace
ssc install reghdfe, replace
ssc install estout, replace
ssc install ivreghdfe, replace

*Sample Selection
drop if year>`3'
drop if year==`3' & month>=`4'
drop if shares < 0.001

*Time FE schemes
egen period = group(year month)
egen calendar = group(month)

*generate nesting schemes
gen nesting_ids_1 = 1
egen nesting_ids_2 = group(brand_code)
* mean per-unit price by brand and take the brands in the 75th percentile and above
bys brand_code_uc: egen mean_price = mean(prices)
egen p75 = pctile(prices), p(75)
gen nesting_ids_3 = cond(mean_price >= p75, 1, 0)

*generate rhs variables
forval z=1/3{
	bys market_ids nesting_ids_`z': egen tns_`z' = sum(shares)
	gen wns_`z' = shares/tns_`z'
	gen lwns_`z' = log(wns_`z')
	* rename log_within_nest_share_`z' lwns_`z'
	qui unique upc, by(dma_code year month nesting_ids_`z') gen(N_upc_`z')
	bysort dma_code year month nesting_ids_`z': egen N_UPC_`z' = mean(N_upc_`z')
}
*
drop wns_* N_upc*
bys dma_code year month: egen tot_dist = total(distance)
gen dist_diesel_tot = tot_dist * demand_instruments0

*generate a matrix to store the MSE values
matrix P = J(50,54,.)

*main loop across nesting schemes and random samples
forval z=1/3{

	forval i=1/50{

		quietly{

			* this divides the sample into two groups based on their dma
			generate rand_dma = .
			bysort dma_code: replace rand_dma = cond(_n==1,rnormal(),rand_dma[1])
			egen groups_dma = cut(rand_dma), group(2)

			* this divides the sample into two groups based on their period
			generate rand_per = .
			bysort year month: replace rand_per = cond(_n==1,rnormal(),rand_per[1])
			egen groups_per = cut(rand_per), group(2)

			gen e_sample = cond(((groups_per==1 & groups_dma==1) | (groups_per==0 & groups_dma==0)), 1, 0)

			/*Estimate all models in the random sample*/
			/*INST: demand* N_UPC_`z' */
			*upc
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* N_UPC_`z') if e_sample==1, abs(fe1=upc, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			predict xb1, xb
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb1 + fe1 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_1 = mean(err_hat2)
			local MSE_1 = MSE_1
			matrix P[`i',(18*`z'-17)] = `MSE_1'
			drop MSE_1 xb1 fe1 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc dma
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* N_UPC_`z') if e_sample==1, abs(fe1=upc fe2=dma_code, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			predict xb2, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb2 + fe1 + fe2 + mean_xi- _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_2 = mean(err_hat2)
			local MSE_2 = MSE_2
			matrix P[`i',(18*`z'-16)] = `MSE_2'
			drop MSE_2 xb2 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc dma calendar
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* N_UPC_`z') if e_sample==1, abs(fe1=upc fe2=dma_code fe3=calendar, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			bys calendar (fe3): replace fe3 = fe3[1]
			predict xb3, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb3 + fe1 + fe2 + fe3 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_3 = mean(err_hat2)
			local MSE_3 = MSE_3
			matrix P[`i',(18*`z'-15)] = `MSE_3'
			drop MSE_3 xb3 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc dma period
			ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 N_UPC_`z') if e_sample==1, abs(fe1=upc fe2=dma_code fe3=period, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			bys period (fe3): replace fe3 = fe3[1]
			predict xb4, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb4 + fe1 + fe2 + fe3 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_4 = mean(err_hat2)
			local MSE_4 = MSE_4
			matrix P[`i',(18*`z'-14)] = `MSE_4'
			drop MSE_4 xb4 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc calendar
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* N_UPC_`z') if e_sample==1, abs(fe1=upc fe2=calendar, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys calendar (fe2): replace fe2 = fe2[1]
			predict xb5, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb5 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_5 = mean(err_hat2)
			local MSE_5 = MSE_5
			matrix P[`i',(18*`z'-13)] = `MSE_5'
			drop MSE_5 xb5 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc period
			ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 N_UPC_`z') if e_sample==1, abs(fe1=upc fe2=period, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys period (fe2): replace fe2 = fe2[1]
			predict xb6, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb6 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_6 = mean(err_hat2)
			local MSE_6 = MSE_6
			matrix P[`i',(18*`z'-12)] = `MSE_6'
			drop MSE_6 xb6 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			/*INST: dist_diesel_tot cost_shifters*/
			*upc
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot) if e_sample==1, abs(fe1=upc, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			predict xb7, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb7 + fe1 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_7 = mean(err_hat2)
			local MSE_7 = MSE_7
			matrix P[`i',(18*`z'-11)] = `MSE_7'
			drop MSE_7 xb7 fe1 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc dma
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot) if e_sample==1, abs(fe1=upc fe2=dma_code, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			predict xb8, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb8 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_8 = mean(err_hat2)
			local MSE_8 = MSE_8
			matrix P[`i',(18*`z'-10)] = `MSE_8'
			drop MSE_8 xb8 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest mean_xi errores

			*upc dma calendar
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot) if e_sample==1, abs(fe1=upc fe2=dma_code fe3=calendar, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			bys calendar (fe3): replace fe3 = fe3[1]
			predict xb9, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb9 + fe1 + fe2 + fe3 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_9 = mean(err_hat2)
			local MSE_9 = MSE_9
			matrix P[`i',(18*`z'-9)] = `MSE_9'
			drop MSE_9 xb9 fe1 fe2 fe3  num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc dma period
			ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 dist_diesel_tot) if e_sample==1, abs(fe1=upc fe2=dma_code fe3=period, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			bys period (fe3): replace fe3 = fe3[1]
			predict xb10, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb10 + fe1 + fe2 + fe3 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_10 = mean(err_hat2)
			local MSE_10 = MSE_10
			matrix P[`i',(18*`z'-8)] = `MSE_10'
			drop MSE_10 xb10 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc calendar
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot) if e_sample==1, abs(fe1=upc fe2=calendar, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys calendar (fe2): replace fe2 = fe2[1]
			predict xb11, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb11 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_11 = mean(err_hat2)
			local MSE_11 = MSE_11
			matrix P[`i',(18*`z'-7)] = `MSE_11'
			drop MSE_11 xb11 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc period
			ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 dist_diesel_tot) if e_sample==1, abs(fe1=upc fe2=period, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys period (fe2): replace fe2 = fe2[1]
			predict xb12, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb12 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_12 = mean(err_hat2)
			local MSE_12 = MSE_12
			matrix P[`i',(18*`z'-6)] = `MSE_12'
			drop MSE_12 xb12 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			/*INST: dist_diesel_tot cost_shifters N_UPC_`z'*/
			*upc
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot N_UPC_`z') if e_sample==1, abs(fe1=upc, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			predict xb13, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb13 + fe1 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_13 = mean(err_hat2)
			local MSE_13 = MSE_13
			matrix P[`i',(18*`z'-5)] = `MSE_13'
			drop MSE_13 xb13 fe1 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc dma
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot N_UPC_`z') if e_sample==1, abs(fe1=upc fe2=dma_code, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			predict xb14, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb14 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_14 = mean(err_hat2)
			local MSE_14 = MSE_14
			matrix P[`i',(18*`z'-4)] = `MSE_14'
			drop MSE_14 xb14 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc dma calendar
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot N_UPC_`z') if e_sample==1, abs(fe1=upc fe2=dma_code fe3=calendar, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			bys calendar (fe3): replace fe3 = fe3[1]
			predict xb15, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb15 + fe1 + fe2 + fe3 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_15 = mean(err_hat2)
			local MSE_15 = MSE_15
			matrix P[`i',(18*`z'-3)] = `MSE_15'
			drop MSE_15 xb15 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc dma period
			ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 dist_diesel_tot N_UPC_`z') if e_sample==1, abs(fe1=upc fe2=dma_code fe3=period, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			bys period (fe3): replace fe3 = fe3[1]
			predict xb16, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb16 + fe1 + fe2 + fe3 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_16 = mean(err_hat2)
			local MSE_16 = MSE_16
			matrix P[`i',(18*`z'-2)] = `MSE_16'
			drop MSE_16 xb16 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc calendar
			ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot N_UPC_`z') if e_sample==1, abs(fe1=upc fe2=calendar, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys calendar (fe2): replace fe2 = fe2[1]
			predict xb17, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb17 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_17 = mean(err_hat2)
			local MSE_17 = MSE_17
			matrix P[`i',(18*`z'-1)] = `MSE_17'
			drop MSE_17 xb17 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*upc period
			ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 dist_diesel_tot N_UPC_`z') if e_sample==1, abs(fe1=upc fe2=period, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys period (fe2): replace fe2 = fe2[1]
			predict xb18, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb18 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0
			gen err_hat2 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_18 = mean(err_hat2)
			local MSE_18 = MSE_18
			matrix P[`i',(18*`z')] = `MSE_18'
			drop MSE_18 xb18 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi

			*clean out for next iter
			drop e_sample rand_dma rand_per groups_per groups_dma
		}
	}
}
*

/*

Export the Matrix with the MSE values for each model round

*/
putexcel set "MSE", modify
putexcel A1=matrix(P)
mata: st_matrix("MSE", mean(st_matrix("P")))


/*

Whole-Sample estimation and tables for theory restrictions

*/

forval z=1/3{
		quietly{
		/*INST: demand* N_UPC_`z' */
		*upc
		est clear
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* N_UPC_`z'), abs(upc) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-17)]
		esttab est1 st1* using tables/r_1_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc dma
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* N_UPC_`z'), abs(upc dma_code) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-16)]
		esttab est1 st1* using tables/r_2_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc dma calendar
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* N_UPC_`z'), abs(upc dma_code calendar) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-15)]
		esttab est1 st1* using tables/r_3_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc dma period
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 N_UPC_`z'), abs(upc dma_code period) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-14)]
		esttab est1 st1* using tables/r_4_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc calendar
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* N_UPC_`z'), abs(upc calendar) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-13)]
		esttab est1 st1* using tables/r_5_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc period
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 N_UPC_`z'), abs(upc period) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-12)]
		esttab est1 st1* using tables/r_6_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		/*INST: dist_diesel_tot cost_shifters*/
		*upc
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot), abs(upc) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-11)]
		esttab est1 st1* using tables/r_7_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc dma
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot), abs(upc dma_code) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-10)]
		esttab est1 st1* using tables/r_8_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc dma calendar
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot), abs(upc dma_code calendar) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-9)]
		esttab est1 st1* using tables/r_9_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc dma period
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 dist_diesel_tot), abs(upc dma_code period) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-8)]
		esttab est1 st1* using tables/r_10_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc calendar
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot), abs(upc calendar) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-7)]
		esttab est1 st1* using tables/r_11_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc period
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 dist_diesel_tot), abs(upc period) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-6)]
		esttab est1 st1* using tables/r_12_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		/*INST: dist_diesel_tot cost_shifters N_UPC_`z'*/
		*upc
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot N_UPC_`z'), abs(upc) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-5)]
		esttab est1 st1* using tables/r_13_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc dma
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot N_UPC_`z'), abs(upc dma_code) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-4)]
		esttab est1 st1* using tables/r_14_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc dma calendar
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot N_UPC_`z'), abs(upc dma_code calendar) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-3)]
		esttab est1 st1* using tables/r_15_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc dma period
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 dist_diesel_tot N_UPC_`z'), abs(upc dma_code period) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-2)]
		esttab est1 st1* using tables/r_16_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc calendar
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand* dist_diesel_tot N_UPC_`z'), abs(upc calendar) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z'-1)]
		esttab est1 st1* using tables/r_17_`z'.csv, stats(N r2 F APF1 APF2 MSE1,  labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
		*upc period
		eststo: ivreghdfe logsj_logs0 (price lwns_`z' = demand_instruments0 dist_diesel_tot N_UPC_`z'), abs(upc period) cluster(dma_code) first savefirst savefprefix(st1)
		mat first=e(first)
		estadd scalar APF1=first[4,1]
		estadd scalar APF2=first[4,2]
		estadd scalar MSE1=MSE[1,(18*`z')]
		esttab est1 st1* using tables/r_18_`z'.csv, stats(N r2 F APF1 APF2 MSE1, labels("Observations" "R-squared" "F-statistic" "F-prices" "F-nest" "MSE")) replace

		est clear
	}
}
*


*

exit, STATA clear



































/* mata code */
/*
matrix P = J(`nbases',1,.)
matrix rowname P = `bases'
matrix colname P = Junior

local i = 1
foreach base of local bases {
	use `base', clear
	summ p12_2 if p12_2>48
	local hora=r(sum_w)
	summ estado if estado==1
	matrix P[`i',1] = `hora'/r(sum_w)*100
	local ++i
}
matrix list P, format(%2.1f)

*/







