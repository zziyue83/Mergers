
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
log using `2'/did_stata_int_`3', text replace

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
gen after = 0
replace after = 1 if month_date >= `cutoff_c' + 12
gen Post_Merger_1y = post_merger * after
gen Post_Merging_1y = Post_Merging * after
gen Post_Non_Merging_1y = Post_Non_Merging * after

/*Announced vs Completed*/
tabstat month_date if (month==`7' & year==`6'), save
matrix cutoff_a=r(StatTotal)
local cutoff_a=cutoff_a[1,1]
gen between = 0
replace between = 1 if (month_date >= `cutoff_a' & month_date <= `cutoff_c')
gen Merging_btw = Merging * between
gen Non_Merging_btw = Non_Merging * between

/*Untreated*/
bys dma_code: gen mp_shares = sum(shares) if Merging==1
bys dma_code: egen mp_share = max(mp_share)
drop mp_shares
foreach x in 2 5 10 {
gen Untreated_`x' = 1
replace Untreated_`x' = 0 if mp_share >= `x'/100
gen Post_Merging_Treat_`x' = (1 - Untreated_`x') * Merging * post_merger
gen Post_Non_Merging_Treat_`x' = (1 - Untreated_`x') * Non_Merging * post_merger

gen Merging_Treated_`x' = Merging * (1 - Untreated_`x')
gen Non_Merging_Treated_`x' = (1 - Merging) * (1 - Untreated_`x')
gen Merging_Treated_Post_`x' = Merging * (1 - Untreated_`x') * post_merger
gen Non_Merging_Treated_Post_`x' = (1 - Merging) * (1 - Untreated_`x') * post_merger
gen Treated_`x' = (1 - Untreated_`x')
gen Treated_Post_`x' = (1 - Untreated_`x') * post_merger

}
*

/*Minor post*/
gen Major = .
replace Major = 1 if major_competitor == "True"
replace Major = 0 if major_competitor == "False"
gen Post_Minor = (1 - Major) * Non_Merging * post_merger
gen Post_Major = Major * Non_Merging * post_merger

/*Coarse HHI Bins*/
gen HHI_bins = 0
replace HHI_bins = 1 if (post_hhi*10000>1500 & post_hhi*10000<2500)
replace HHI_bins = 2 if (post_hhi*10000>2500 & !missing(post_hhi))

/*Coarse DHHI Bins*/
gen DHHI_bins = 0
replace DHHI_bins = 1 if (dhhi*10000>100 & dhhi*10000<200)
replace DHHI_bins = 2 if (dhhi*10000>200 & !missing(dhhi))

/*Finer HHI Bins*/
gen HHI_binsf = 0
replace HHI_binsf = 1 if (post_hhi*10000>=375 & post_hhi*10000<750)
replace HHI_binsf = 2 if (post_hhi*10000>=750 & post_hhi*10000<1125)
replace HHI_binsf = 3 if (post_hhi*10000>=1125 & post_hhi*10000<1500)
replace HHI_binsf = 4 if (post_hhi*10000>=1500 & post_hhi*10000<1750)
replace HHI_binsf = 5 if (post_hhi*10000>=1750 & post_hhi*10000<2000)
replace HHI_binsf = 6 if (post_hhi*10000>=2000 & post_hhi*10000<2250)
replace HHI_binsf = 7 if (post_hhi*10000>=2250 & post_hhi*10000<2500)
replace HHI_binsf = 8 if (post_hhi*10000>=2500 & !missing(post_hhi))

/*Finer DHHI Bins*/
gen DHHI_binsf = 0
replace DHHI_binsf = 1 if (dhhi*10000>=25 & dhhi*10000<50)
replace DHHI_binsf = 2 if (dhhi*10000>=50 & dhhi*10000<75)
replace DHHI_binsf = 3 if (dhhi*10000>=75 & dhhi*10000<100)
replace DHHI_binsf = 4 if (dhhi*10000>=100 & dhhi*10000<125)
replace DHHI_binsf = 5 if (dhhi*10000>=125 & dhhi*10000<150)
replace DHHI_binsf = 6 if (dhhi*10000>=150 & dhhi*10000<175)
replace DHHI_binsf = 7 if (dhhi*10000>175 & dhhi*10000<200)
replace DHHI_binsf = 8 if (dhhi*10000>=200 & !missing(dhhi))

/*HHI and DHHI Bins*/
gen DHHI_HHI = 0
replace DHHI_HHI = 1 if (dhhi*10000>=25 & post_hhi*10000>=375)
replace DHHI_HHI = 2 if (dhhi*10000>=50 & post_hhi*10000>=750)
replace DHHI_HHI = 3 if (dhhi*10000>=75 & post_hhi*10000>=1125)
replace DHHI_HHI = 4 if (dhhi*10000>=100 & post_hhi*10000>=1500)
replace DHHI_HHI = 5 if (dhhi*10000>=125 & post_hhi*10000>=1750)
replace DHHI_HHI = 6 if (dhhi*10000>=150 & post_hhi*10000>=2000)
replace DHHI_HHI = 7 if (dhhi*10000>=175 & post_hhi*10000>=2250)
replace DHHI_HHI = 8 if (dhhi*10000>=200 & !missing(dhhi) & post_hhi*10000>=2500 & !missing(post_hhi))

/*Nocke & Whinston Bins*/
gen DHHI_HHI_NW = 0
replace DHHI_HHI_NW = 1 if (dhhi*10000>=100 & post_hhi*10000>=1500)
replace DHHI_HHI_NW = 2 if (dhhi*10000>=200 & !missing(dhhi) & post_hhi*10000>2500 & !missing(post_hhi))

/*Months After and Pre Dummies*/
gen Months_post = 0
forv i=1/24{
	replace Months_post = `i' if month_date >= `cutoff_c' + `i'
}
*
gen Months_pre = 0
forv i=1/24{
	replace Months_pre = `i' if month_date <= `cutoff_c' - `i'
}
*
/*Months Pre-Post Dummies*/
gen Months = .
forv i=-24/24{
	local j = `i' + 25
	replace Months = `j' if month_date == `cutoff_c' + `i'
}
*


/*Main Routine*/
foreach var of varlist lprice lquant {
forval x = 0/3 {
quietly{
/*Overall Price Effects*/

/*Overall Effects*/
reghdfe `var' Merging Post_Merging Post_Non_Merging trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto OA_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Overall") replace

reghdfe `var' Merging Post_Merging Post_Non_Merging trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto OA_FE_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Overall FE") append

reghdfe `var' Merging Post_Merging Post_Non_Merging trend [aw = weights_`x'], abs(dma_code##c.trend entity_effects time_calendar) vce(cluster dma_code)
est sto OA_FE_t_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Overall t") append

/*Overall Effects Controls*/
reghdfe `var' Merging Post_Merging Post_Non_Merging log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto OA_C_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Overall C") append

reghdfe `var' Merging Post_Merging Post_Non_Merging log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto OA_FE_C_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Overall FE C") append

reghdfe `var' Merging Post_Merging Post_Non_Merging log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(dma_code##c.trend entity_effects time_calendar) vce(cluster dma_code)
est sto OA_FE_C_t_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Overall t C") append

foreach z in 2 5 10 {
/*Overall Effects Untreated*/
reghdfe `var' Merging_Treated_`z' Non_Merging_Treated_`z' Merging_Treated_Post_`z' Non_Merging_Treated_Post_`z' trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto UT_`x'_`var'_`z'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Untreated `z'") append

reghdfe `var' Merging_Treated_`z' Non_Merging_Treated_`z' Merging_Treated_Post_`z' Non_Merging_Treated_Post_`z' trend [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto UT_`x'_`var'_`z'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Untreated `z'") append

reghdfe `var' Merging_Treated_`z' Non_Merging_Treated_`z' Merging_Treated_Post_`z' Non_Merging_Treated_Post_`z' trend [aw = weights_`x'], abs(dma_code##c.trend entity_effects time_calendar) vce(cluster dma_code)
est sto UT_`x'_`var'_`z'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Untreated T `z'") append


/*Overall Effects Untreated Controls*/
reghdfe `var' Merging_Treated_`z' Non_Merging_Treated_`z' Merging_Treated_Post_`z' Non_Merging_Treated_Post_`z' log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto UT_C_`x'_`var'_`z'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Untreated C `z'") append

reghdfe `var' Merging_Treated_`z' Non_Merging_Treated_`z' Merging_Treated_Post_`z' Non_Merging_Treated_Post_`z' log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto UT_FE_C_`x'_`var'_`z'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Untreated FE C `z'") append

reghdfe `var' Merging_Treated_`z' Non_Merging_Treated_`z' Merging_Treated_Post_`z' Non_Merging_Treated_Post_`z' log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(dma_code##c.trend entity_effects time_calendar) vce(cluster dma_code)
est sto UT_T_C_`x'_`var'_`z'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Untreated T C `z'") append

/*Untreated as Controls*/
reghdfe `var' Merging_Treated_`z' Non_Merging_Treated_`z' Merging#ib25.Months Merging#ib25.Months Non_Merging#ib25.Months trend [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto UT_M_`x'_`var'_`z'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Untreated Months `z'") append

/*Untreated as Controls with Controls*/
reghdfe `var' Merging_Treated_`z' Non_Merging_Treated_`z' Merging#ib25.Months Merging#ib25.Months Non_Merging#ib25.Months log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto UT_M_C_`x'_`var'_`z'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Untreated Months C `z'") append

}
*

/*Overall Effects Major*/
reghdfe `var' Major Merging Post_Major Post_Merging Post_Minor trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto Maj_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': MAjor") append

reghdfe `var' Major Merging Post_Major Post_Merging Post_Minor trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto Maj_FE_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Major FE") append

reghdfe `var' Major Merging Post_Major Post_Merging Post_Minor trend [aw = weights_`x'], abs(dma_code##c.trend entity_effects time_calendar) vce(cluster dma_code)
est sto Maj_FE_t_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Major t") append

/*Overall Effects Major Controls*/
reghdfe `var' Major Merging Post_Major Post_Merging Post_Minor log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto Maj_C_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': MAjor C") append

reghdfe `var' Major Merging Post_Major Post_Merging Post_Minor log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto Maj_FE_C_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Major FE C") append

reghdfe `var' Major Merging Post_Major Post_Merging Post_Minor log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(dma_code##c.trend entity_effects time_calendar) vce(cluster dma_code)
est sto Maj_FE_t_C_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Major t C") append

/*Timing of the Effects on Prices*/
/*One Year After*/
reghdfe `var' Merging Post_Merging Post_Non_Merging Post_Non_Merging_1y Post_Merging_1y trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto After_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': 1y") append

reghdfe `var' Merging Post_Merging Post_Non_Merging Post_Non_Merging_1y Post_Merging_1y trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto After_FE_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': 1y FE") append

/*Granular Timing for Post Only*/
reghdfe `var' Merging Post_Merging#i.Months_post Post_Non_Merging#i.Months_post i.Months_post trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto Tim_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Timing") append

reghdfe `var' Merging Post_Merging#i.Months_post Post_Non_Merging#i.Months_post i.Months_post trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto Tim_FE_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Timing FE") append

/*Granular Timing Pre and Post*/
reghdfe `var' Merging Merging#i.Months_pre Non_Merging#i.Months_pre Post_Merging#i.Months_post Post_Non_Merging#i.Months_post i.Months_pre i.Months_post trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto Timing_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Timing Pre Post") append

reghdfe `var' Merging Merging#i.Months_pre Non_Merging#i.Months_pre Post_Merging#i.Months_post Post_Non_Merging#i.Months_post i.Months_pre i.Months_post trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto Timing_FE_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Timing Pre Post FE") append

/*Between Period*/
reghdfe `var' Merging Merging_btw Non_Merging_btw Post_Merging Post_Non_Merging trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto Btw_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Between") append

reghdfe `var' Merging Merging_btw Non_Merging_btw Post_Merging Post_Non_Merging trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto Btw_FE_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': Between FE") append

/*Interactions of Concentration Measures on Prices*/

/* HHI Coarse */
reghdfe `var' Post_Merging#i.HHI_bins Post_Non_Merging#i.HHI_bins i.HHI_bins trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto HHI_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': HHI") append

* DHHI Coarse
reghdfe `var' Post_Merging#i.DHHI_bins Post_Non_Merging#i.DHHI_bins i.DHHI_bins trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto DHHI_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': DHHI") append

* HHI Fine
reghdfe `var' Post_Merging#i.HHI_binsf Post_Non_Merging#i.HHI_binsf i.HHI_binsf trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto HHIf_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': HHIf") append

* DHHI Fine
reghdfe `var' Post_Merging#i.DHHI_binsf Post_Non_Merging#i.DHHI_binsf i.DHHI_binsf trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto DHHIf_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': DHHIf") append

* DHHI & HHI Bins
reghdfe `var' Post_Merging#i.DHHI_HHI Post_Non_Merging#i.DHHI_HHI i.DHHI_HHI trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto DHHI_HHI_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': DHHI_HHI") append

* Nocke & Whinston Regions
reghdfe `var' Post_Merging#i.DHHI_HHI_NW Post_Non_Merging#i.DHHI_HHI_NW i.DHHI_HHI_NW trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto DHHI_HHI_NW_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': NW") append

/*Classic Diff in Diffs*/
/*Price Effects*/
reghdfe `var' Post_Merging post_merger trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto Did_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': did") append

reghdfe `var' Post_Merging post_merger trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto Did_calendar_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': did calendar") append

reghdfe `var' Post_Merging post_merger trend [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto Did_period_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': did period") append

reghdfe `var' Post_Merging post_merger trend [aw = weights_`x'], abs(dma_code##c.trend entity_effects time_calendar) vce(cluster dma_code)
est sto Did_t_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': did trends") append


/*Summary Specs*/
reghdfe `var' post_merger trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto sum_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': sum") append

reghdfe `var' post_merger trend [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto sum_t_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': sum period") append

foreach z in 2 5 10 {
reghdfe `var' Treated_`x' Treated_Post_`x' trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto sum_t_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': sum treated") 

reghdfe `var' Treated_`x' Treated_Post_`x' trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto sum_t_c_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': sum treated calendar") append

reghdfe `var' Treated_`x' Treated_Post_`x' trend [aw = weights_`x'], abs(entity_effects time_period) vce(cluster dma_code)
est sto sum_t_p_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': sum treated period") append
}
*

/*Summary Specs with Controls*/
reghdfe `var' post_merger trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto sum_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': did") append

reghdfe `var' post_merger trend [aw = weights_`x'], abs(entity_effects time_effects) vce(cluster dma_code)
est sto sum_t_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': did") append

foreach z in 2 5 10 {
reghdfe `var' Treated_`x' Treated_Post_`x' log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(entity_effects) vce(cluster dma_code)
est sto sum_t_c_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': sum treated C") 

reghdfe `var' Treated_`x' Treated_Post_`x' log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(entity_effects time_calendar) vce(cluster dma_code)
est sto sum_t_c_c_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': sum treated calendar C") append

reghdfe `var' Treated_`x' Treated_Post_`x' log_hhinc_per_person_adj demand* trend [aw = weights_`x'], abs(entity_effects time_period) vce(cluster dma_code)
est sto sum_t_p_c_`x'_`var'
outreg2 using `2'/did_int_`var'_`x'.txt, stats(coef se pval) ctitle("`var': sum treated period C") append
}
*

est clear
}
}
}

est clear




exit, STATA clear






.
