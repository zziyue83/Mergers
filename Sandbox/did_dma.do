
clear all
set more off
set scheme s1mono
set matsize 11000
est clear

/* *args: input_path       = `1' */
/* *args: output_path      = `2' */
/* *args: month_or_quarter = `3' */
/* *args: merger_code 	   = `4' */

cd `1'
log using `2'/did_stata_quarter, text replace
import delimited "stata_did_quarter.csv", encoding(ISO-8859-1)

/* WEIGHTING SCHEMES */
gen pre_vol = volume * (1 - post_merger)
egen weights_2 = total(pre_vol), by(dma_code)
replace weights_2 = round(weights_2)

replace dhhi = dhhi * 10000


/* MAIN ROUTINE */

gen tot_dma_2 = .
reghdfe lprice post_merger##post_merger_merging##i.dma_code trend [aw=weights_2], abs(upc) vce(cluster dma_code)

levelsof dma_code, local(levels)
foreach l of local levels{

	replace tot_dma_2 = _b[1.post_merger] + _b[1.post_merger_merging] + ///
						  _b[1.post_merger#`l'.dma_code] + ///
						  _b[1.post_merger_merging#`l'.dma_code] if dma_code == `l'
}

collapse (mean) tot_dma_2 dhhi, by(dma_code)

graph twoway (lfit tot_dma_2 dhhi) (scatter tot_dma_2 dhhi, mcolor(gs4))
graph export `2'/tot_dma_2_`4'.eps, replace

est clear



exit, STATA clear



.
