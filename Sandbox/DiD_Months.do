

clear all

set more off

est clear

/* *args coming from the python script*/
/* *args: input_path       = `1' */
/* *args: output_path      = `2' */
/* *args: month_or_quarter = `3' */
/* *args: year_completed   = `4' */
/* *args: month_completed  = `5' */
/* *args: year_announced   = `6' */
/* *args: month_announced  = `7' */


cd `1'
log using `2'/did_Months, text replace

import delimited "stata_did_int_`3'.csv", encoding(ISO-8859-1)

/*Install Packages*/
ssc install outreg2
ssc install ftools
ssc install reghdfe
ssc install estout

/* Fixed Effects */
egen entity_effects = group(upc dma_code)
egen time_effects = group(year `3')
egen time_calendar = group(`3')

/* WEIGHTING SCHEMES */
gen pre_vol = volume * (1 - post_merger)
gen weights_0 = 1 /*to add weights that won't change things*/
egen weights_1 = total(pre_vol), by(upc)
egen weights_2 = total(pre_vol), by(dma_code)
egen weights_3 = total(pre_vol), by(upc dma_code)
replace weights_1 = round(weights_1)
replace weights_2 = round(weights_2)
replace weights_3 = round(weights_3)

/*Post Merger Non Merging*/
gen Merging = .
replace Merging = 1 if merging == "True"
replace Merging = 0 if merging == "False"
gen Non_Merging = (1 - Merging)
gen Post_Non_Merging = post_merger * (1 - Merging)

/*Controls*/
replace demand_instruments0 = demand_instruments0/distance

/*Quantity*/
gen lquant = log(volume)

rename post_merger_merging Post_Merging

/*One Year Post*/
gen month_date = ym(year, month)
tabstat month_date if (month==`5' & year==`4'), save
matrix cutoff_c=r(StatTotal)
local cutoff_c=cutoff_c[1,1]

/*Minor post*/
gen Major = .
replace Major = 1 if major_competitor == "True"
replace Major = 0 if major_competitor == "False"
gen Post_Minor = (1 - Major) * Non_Merging * post_merger
gen Post_Major = Major * Non_Merging * post_merger


/*Months After and Pre Dummies*/
gen Months = .
forv i=-24/24{
	local j = `i' + 25
	replace Months = `j' if month_date == `cutoff_c' + `i'
}
*
gen Months_post = .
forv i=0/24{
	replace Months_post = `i' if month_date == `cutoff_c' + `i'
}
*


summarize Months
local max_month = `r(max)'
local min_month = `r(min)'

matrix P = J(`r(max)', 32, .)

/*Main Routine*/
forval x = 0/3 {

quietly{


/*Granular Timing for Post Only*/
reghdfe lprice i.Merging##ib0.Months_post  [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)

forv i=25/`max_month'{

	local j = `i' - 25
	lincom 1.Merging + `j'.Months + 1.Merging#`j'.Months
	matrix P[`i',(8*`x'+ 1)] = `r(estimate)'
	matrix P[`i',(8*`x'+ 2)] = `r(se)'

	lincom 0.Merging + `j'.Months + 0.Merging#`j'.Months
	matrix P[`i',(8*`x'+ 3)] = `r(estimate)'
	matrix P[`i',(8*`x'+ 4)] = `r(se)'
}
*

/*Granular Timing Pre and Post*/
reghdfe lprice i.Merging##ib25.Months trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code) basel

forv i=`min_month'/`max_month'{

	lincom 1.Merging + `i'.Months + 1.Merging#`i'.Months
	matrix P[`i',(8*`x'+ 5)] = `r(estimate)'
	matrix P[`i',(8*`x'+ 6)] = `r(se)'

	lincom 0.Merging + `i'.Months + 0.Merging#`i'.Months
	matrix P[`i',(8*`x'+ 7)] = `r(estimate)'
	matrix P[`i',(8*`x'+ 8)] = `r(se)'
}
*


}
}
*

putexcel set "`2'/Months", replace
putexcel A1=matrix(P)
mata : st_matrix("Months", mean(st_matrix("P")))





exit, STATA clear





*





