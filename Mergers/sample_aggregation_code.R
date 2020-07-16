library(dplyr)
library(bit64)
library(lubridate)
library(data.table)

master_region_file <- SOMETHING
master_region_list <- read_csv(master_region_file) %>%
  select(c("store_code_uc", "region")) # should have (store_code_uc, region), and that's it

##########################
# Do all this in a loop over mvmt files
#

mvmt_file <- "5000_2006.tsv"
mvmt <- fread(mvmt_file, data.table = FALSE)
mvmt <- mvmt %>%
  mutate(clean_date = lubridate::ymd(week_end)) %>%
  mutate(year = lubridate::year(clean_date),
         month = lubridate::month(clean_date))
agg <- mvmt %>%
  left_join(master_region_list) %>%
  group_by(region, upc, year, month) %>%
  summarize(quantity = sum(units, na.rm = TRUE),
            price = weighted.mean(price, units, na.rm = TRUE))

# Keep the UPCs you want
agg <- agg %>%
  semi_join(relevant_upc_list)

#
###################

compress_movement <- function(mvmt_file) {
  mvmt <- fread(mvmt_file, data.table = FALSE)  %>%
    mutate(clean_date = lubridate::ymd(week_end)) %>%
    mutate(year = lubridate::year(clean_date),
           month = lubridate::month(clean_date))
  agg <- mvmt %>%
    left_join(master_region_list) %>%
    group_by(region, upc, year, month) %>%
    summarize(quantity = sum(units, na.rm = TRUE),
              price = weighted.mean(price, units, na.rm = TRUE))
  
  # Keep the UPCs you want
  agg <- agg %>%
    semi_join(relevant_upc_list)
  return(agg)
}

list_of_mvmt_files <- something
list_mvmt_df <- lapply(list_of_mvmt_files, compress_movement)
all_mvmt <- do.call(rbind, list_mvmt_df)
list_mvmt_df <- NULL