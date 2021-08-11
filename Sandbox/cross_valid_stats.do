
clear all

set more off

est clear

/* *args: input_path       = `1' */
/* *args: output_path      = `2' */
/* *args: year             = `3' */
/* *args: month            = `4' */



cd `1'
log using `2'/cross_valid, text replace

import delimited "demand_month.csv", encoding(ISO-8859-1)

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
ssc install _gwtmean, replace

*Sample Selection
di `3'
di `4'

drop if year>`3'
drop if year==`3' & month>=`4'
drop if shares < 0.001

*Time FE schemes
egen period = group(year month)
egen calendar = group(month)

*rescale prices
replace price = price * multi * size1_amount * conversion

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

gen market_size = volume/shares

*generate a matrix to store the MSE values
matrix P = J(1,72,.)
matrix K = J(1,72,.)

*main loop across nesting schemes and random samples
forval z=1/3{

	foreach i in 1{

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_1 = wtmean(err_hat2), weight(shares)
			egen MSE_1_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_1 = MSE_1
			local MSE_1_1 = MSE_1_1
			matrix P[`i',(24*`z'-23)] = `MSE_1'
			matrix K[`i',(24*`z'-23)] = `MSE_1_1'
			drop MSE_1* xb1 fe1 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_2 = wtmean(err_hat2), weight(shares)
			egen MSE_2_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_2 = MSE_2
			local MSE_2_1 = MSE_2_1
			matrix P[`i',(24*`z'-22)] = `MSE_2'
			matrix K[`i',(24*`z'-22)] = `MSE_2_1'
			drop MSE_2* xb2 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_3 = wtmean(err_hat2), weight(shares)
			egen MSE_3_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_3 = MSE_3
			local MSE_3_1 = MSE_3_1
			matrix P[`i',(24*`z'-21)] = `MSE_3'
			matrix K[`i',(24*`z'-21)] = `MSE_3_1'
			drop MSE_3* xb3 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_4 = wtmean(err_hat2), weight(shares)
			egen MSE_4_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_4 = MSE_4
			local MSE_4_1 = MSE_4_1
			matrix P[`i',(24*`z'-20)] = `MSE_4'
			matrix K[`i',(24*`z'-20)] = `MSE_4_1'
			drop MSE_4* xb4 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_5 = wtmean(err_hat2), weight(shares)
			egen MSE_5_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_5 = MSE_5
			local MSE_5_1 = MSE_5_1
			matrix P[`i',(24*`z'-19)] = `MSE_5'
			matrix K[`i',(24*`z'-19)] = `MSE_5_1'
			drop MSE_5* xb5 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_6 = wtmean(err_hat2), weight(shares)
			egen MSE_6_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_6 = MSE_6
			local MSE_6_1 = MSE_6_1
			matrix P[`i',(24*`z'-18)] = `MSE_6'
			matrix K[`i',(24*`z'-18)] = `MSE_6_1'
			drop MSE_6* xb6 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_7 = wtmean(err_hat2), weight(shares)
			egen MSE_7_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_7 = MSE_7
			local MSE_7_1 = MSE_7_1
			matrix P[`i',(24*`z'-17)] = `MSE_7'
			matrix K[`i',(24*`z'-17)] = `MSE_7_1'
			drop MSE_7* xb7 fe1 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_8 = wtmean(err_hat2), weight(shares)
			egen MSE_8_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_8 = MSE_8
			local MSE_8_1 = MSE_8_1
			matrix P[`i',(24*`z'-16)] = `MSE_8'
			matrix K[`i',(24*`z'-16)] = `MSE_8_1'
			drop MSE_8* xb8 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest mean_xi errores Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_9 = wtmean(err_hat2), weight(shares)
			egen MSE_9_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_9 = MSE_9
			local MSE_9_1 = MSE_9_1
			matrix P[`i',(24*`z'-15)] = `MSE_9'
			matrix K[`i',(24*`z'-15)] = `MSE_9_1'
			drop MSE_9* xb9 fe1 fe2 fe3  num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_10 = wtmean(err_hat2), weight(shares)
			egen MSE_10_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_10 = MSE_10
			local MSE_10_1 = MSE_10_1
			matrix P[`i',(24*`z'-14)] = `MSE_10'
			matrix K[`i',(24*`z'-14)] = `MSE_10_1'
			drop MSE_10* xb10 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_11 = wtmean(err_hat2), weight(shares)
			egen MSE_11_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_11 = MSE_11
			local MSE_11_1 = MSE_11_1
			matrix P[`i',(24*`z'-13)] = `MSE_11'
			matrix K[`i',(24*`z'-13)] = `MSE_11_1'
			drop MSE_11* xb11 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_12 = wtmean(err_hat2), weight(shares)
			egen MSE_12_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_12 = MSE_12
			local MSE_12_1 = MSE_12_1
			matrix P[`i',(24*`z'-12)] = `MSE_12'
			matrix K[`i',(24*`z'-12)] = `MSE_12_1'
			drop MSE_12* xb12 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_13 = wtmean(err_hat2), weight(shares)
			egen MSE_13_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_13 = MSE_13
			local MSE_13_1 = MSE_13_1
			matrix P[`i',(24*`z'-11)] = `MSE_13'
			matrix K[`i',(24*`z'-11)] = `MSE_13_1'
			drop MSE_13* xb13 fe1 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_14 = wtmean(err_hat2), weight(shares)
			egen MSE_14_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_14 = MSE_14
			local MSE_14_1 = MSE_14_1
			matrix P[`i',(24*`z'-10)] = `MSE_14'
			matrix K[`i',(24*`z'-10)] = `MSE_14_1'
			drop MSE_14* xb14 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_15 = wtmean(err_hat2), weight(shares)
			egen MSE_15_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_15 = MSE_15
			local MSE_15_1 = MSE_15_1
			matrix P[`i',(24*`z'-9)] = `MSE_15'
			matrix K[`i',(24*`z'-9)] = `MSE_15_1'
			drop MSE_15* xb15 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_16 = wtmean(err_hat2), weight(shares)
			egen MSE_16_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_16 = MSE_16
			local MSE_16_1 = MSE_16_1
			matrix P[`i',(24*`z'-8)] = `MSE_16'
			matrix K[`i',(24*`z'-8)] = `MSE_16_1'
			drop MSE_16* xb16 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_17 = wtmean(err_hat2), weight(shares)
			egen MSE_17_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_17 = MSE_17
			local MSE_17_1 = MSE_17_1
			matrix P[`i',(24*`z'-7)] = `MSE_17'
			matrix K[`i',(24*`z'-7)] = `MSE_17_1'
			drop MSE_17* xb17 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

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

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_18 = wtmean(err_hat2), weight(shares)
			egen MSE_18_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_18 = MSE_18
			local MSE_18_1 = MSE_18_1
			matrix P[`i',(24*`z'-6)] = `MSE_18'
			matrix K[`i',(24*`z'-6)] = `MSE_18_1'
			drop MSE_18* xb18 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

			/*OLS*/
			*upc
			reghdfe logsj_logs0 price lwns_`z' if e_sample==1, abs(fe1=upc, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			predict xb19, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb19 + fe1 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_19 = wtmean(err_hat2), weight(shares)
			egen MSE_19_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_19 = MSE_19
			local MSE_19_1 = MSE_19_1
			matrix P[`i',(24*`z'-5)] = `MSE_19'
			matrix K[`i',(24*`z'-5)] = `MSE_19_1'
			drop MSE_19* xb19 fe1 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

			*upc dma
			reghdfe logsj_logs0 price lwns_`z' if e_sample==1, abs(fe1=upc fe2=dma_code, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			predict xb20, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb20 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_20 = wtmean(err_hat2), weight(shares)
			egen MSE_20_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_20 = MSE_20
			local MSE_20_1 = MSE_20_1
			matrix P[`i',(24*`z'-4)] = `MSE_20'
			matrix K[`i',(24*`z'-4)] = `MSE_20_1'
			drop MSE_20* xb20 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

			*upc dma calendar
			reghdfe logsj_logs0 price lwns_`z' if e_sample==1, abs(fe1=upc fe2=dma_code fe3=calendar, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			bys calendar (fe3): replace fe3 = fe3[1]
			predict xb21, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb21 + fe1 + fe2 + fe3 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_21 = wtmean(err_hat2), weight(shares)
			egen MSE_21_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_21 = MSE_21
			local MSE_21_1 = MSE_21_1
			matrix P[`i',(24*`z'-3)] = `MSE_21'
			matrix K[`i',(24*`z'-3)] = `MSE_21_1'
			drop MSE_21* xb21 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

			*upc dma period
			reghdfe logsj_logs0 price lwns_`z' if e_sample==1, abs(fe1=upc fe2=dma_code fe3=period, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys dma_code (fe2): replace fe2 = fe2[1]
			bys period (fe3): replace fe3 = fe3[1]
			predict xb22, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb22 + fe1 + fe2 + fe3 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_22 = wtmean(err_hat2), weight(shares)
			egen MSE_22_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_22 = MSE_22
			local MSE_22_1 = MSE_22_1
			matrix P[`i',(24*`z'-2)] = `MSE_22'
			matrix K[`i',(24*`z'-2)] = `MSE_22_1'
			drop MSE_22* xb22 fe1 fe2 fe3 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat


			*upc calendar
			reghdfe logsj_logs0 price lwns_`z' if e_sample==1, abs(fe1=upc fe2=calendar, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys calendar (fe2): replace fe2 = fe2[1]
			predict xb23, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb23 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_23 = wtmean(err_hat2), weight(shares)
			egen MSE_23_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_23 = MSE_23
			local MSE_23_1 = MSE_23_1
			matrix P[`i',(24*`z'-1)] = `MSE_23'
			matrix K[`i',(24*`z'-1)] = `MSE_23_1'
			drop MSE_23* xb23 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat

			*upc period
			reghdfe logsj_logs0 price lwns_`z' if e_sample==1, abs(fe1=upc fe2=period, res(err_hat)) cluster(dma_code)
			bys upc (fe1): replace fe1 = fe1[1]
			bys period (fe2): replace fe2 = fe2[1]
			predict xb24, xb //works out of sample
			predict errores, res
			bys upc dma_code: egen mean_xi = mean(errores)
			gen delta_j = xb24 + fe1 + fe2 + mean_xi - _b[lwns_`z']*lwns_`z' if e_sample==0 // works out of sample
			gen num = exp(delta_j/(1-_b[lwns_`z'])) if e_sample==0
			bysort market_ids nesting_ids_`z': egen nest_inclusive_value = total(num) if e_sample==0
			bysort market_ids nesting_ids_`z': gen num_in_nest = _n if e_sample==0
			gen unique_nest = (num_in_nest==1) if e_sample==0
			bysort market_ids: egen market_inclusive_value = sum((unique_nest*nest_inclusive_value)^(1-_b[lwns_`z'])) if e_sample==0
			gen share_predicted = num / ((nest_inclusive_value^_b[lwns_`z'])*(1+market_inclusive_value)) if e_sample==0

			gen Revenues = shares * market_size * prices
			gen Reve_hat = share_predicted * market_size * prices

			gen err_hat2 = (Reve_hat - Revenues)*(Reve_hat - Revenues)
			gen err_hat2_1 = (share_predicted - shares)*(share_predicted - shares)
			egen MSE_24 = wtmean(err_hat2), weight(shares)
			egen MSE_24_1 = wtmean(err_hat2_1), weight(shares)
			local MSE_24 = MSE_24
			local MSE_24_1 = MSE_24_1
			matrix P[`i',(24*`z')] = `MSE_24'
			matrix K[`i',(24*`z')] = `MSE_24_1'
			drop MSE_24* xb24 fe1 fe2 num delta_j unique_nest market_inclusive_value nest_inclusive_value share_predicted err_ha* num_in_nest errores mean_xi Revenues Reve_hat


			*clean out for next iter
			drop e_sample rand_dma rand_per groups_per groups_dma
		}
	}
}
*

/*

Export the Matrix with the MSE values for each model round

*/
putexcel set "MSE_r", modify
putexcel A1=matrix(P)
mata: st_matrix("MSE_r", mean(st_matrix("P")))

putexcel set "MSE_s", modify
putexcel A1=matrix(P)
mata: st_matrix("MSE_s", mean(st_matrix("K")))

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







