import excel using "raw\sdc_food_temp.xls", clear firstrow
drop if TargetName == AcquirorName
drop if AcquirorIndustrySector == "Investment & Commodity Firms,Dealers,Exchanges"
keep if TargetNation == "United States" | AcquirorNation == "United States"
keep if OwnedAfterTransaction == 100
count if ValueofTransactionmil > 200

g yr = year(DateEffective )
keep if yr >= 2007 & yr <= 2016

count if ValueofTransactionmil > 200

g neg = -ValueofTransactionmil 
sort neg
drop neg
br TargetName AcquirorName
