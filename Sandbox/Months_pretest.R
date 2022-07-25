# 0. Overhead -------------------------------------------------------------
# 0.1 Load/install packages -----------------------------------------------
rm(list = ls())
installed_packages <- .packages(all.available = TRUE)
load_packages <- function(x) {
 # if (!x %in% installed_packages) install.packages(x)
  library(x, character.only = TRUE)
}
packages_to_load <- c(
  "tibble", "dplyr", "dtplyr", "data.table", "fixest", "haven",
  "readr", "broom", "tidyr", "glue", "stringr", "lubridate", "purrr",
  "janitor", "zoo", "logr"
)
invisible(lapply(packages_to_load, load_packages))

# 0.2 Helper functions ---------------------------------------------------- 
# 0.2.1 Months between two dates ------------------------------------------
months_between <- function(start, end) {
  interval(start, end) %/% months(1)
}

# 0.2.2 Bin numeric variables ---------------------------------------------
cutr <- function(x, breaks) {
  if_else(is.na(x), 0L, cut(x = x, breaks = c(-Inf, breaks, Inf), labels = FALSE, right = FALSE) - 1L)
}

# 0.2.3 Extract YMD date --------------------------------------------------
extract_ymd <- function(str) {
  str_extract(str, "[0-9]{4}\\-[0-9]{2}\\-[0-9]{2}") %>% 
    ymd()
}

# 0.3 Set up file paths, local variables, log, and read in dataset ------------

### TO INHERIT FROM PYTHON ###
args <- commandArgs(trailingOnly = TRUE)
base_path <- args[1]
month_or_quarter <- args[2]
###

input_path <- glue("{base_path}/intermediate")
output_path <- glue("{base_path}/output")
log_path <- glue("{output_path}/R_did_log.log")
log <- log_open(log_path, logdir = FALSE)


# 0.4 Get information from info.txt ---------------------------------------
info <- read_lines(glue("{base_path}/info.txt"))
completed_line <- info[str_detect(info, "DateCompleted")]
completed_date <- extract_ymd(completed_line)
announced_line <- info[str_detect(info, "DateAnnounced")]
announced_date <- extract_ymd(announced_line)
year_completed <- year(completed_date)
month_completed <- month(completed_date)
year_announced <- year(announced_date)
month_announced <- month(announced_date)
### END ###

cutoff_c <- make_date(year_completed, month_completed)
cutoff_a <- make_date(year_announced, month_announced)


df_0 <- read_csv(glue("{input_path}/stata_did_int_{month_or_quarter}.csv"), locale = locale(encoding = "ISO-8859-1"))

# 1. DATA MANIPULATION ----------------------------------------------------
if (!"parent_code" %in% names(df_0)) {
  df_0 <- mutate(df_0, parent_code = NA_character_)
}
df_1 <- df_0 %>% 
  lazy_dt() %>% 
  arrange(row_number(), upc, dma_code, month, year, owner) %>% 
  distinct(upc, dma_code, month, year, owner, .keep_all = TRUE) %>% 

  # 1.1 Fixed effects -------------------------------------------------------
  mutate(
    entity_effects = factor(paste0(upc, "_", dma_code)),
    time_effects = factor(paste0(year, "_", !!sym(month_or_quarter))),
    time_calendar = factor(!!sym(month_or_quarter))
  ) %>% 

  # 1.2 Weighting schemes ---------------------------------------------------
  mutate(
    pre_vol = volume * (1 - post_merger),
    weights_0 = 1
  ) %>% 
  group_by(upc) %>% 
  mutate(weights_1 = round(sum(pre_vol))) %>% 
  group_by(dma_code) %>% 
  mutate(weights_2 = round(sum(pre_vol))) %>% 
  group_by(upc, dma_code) %>% 
  mutate(weights_3 = round(sum(pre_vol))) %>% 
  ungroup() %>% 

  # 1.3 Post merger/Non merging ---------------------------------------------
  mutate(
    months_after_merger = months_between(cutoff_c %m+% months(1), make_date(year, month, 1)),
    months_after_merger_abs = abs(months_after_merger)
  ) %>% 
  group_by(upc) %>% 
  mutate(
    months_after_merger_abs_min = min(months_after_merger_abs),
    months_after_merger_tiebreak = max(if_else(months_after_merger_abs == months_after_merger_abs_min, months_after_merger, -Inf)),
    merging = if_else(months_after_merger_abs == months_after_merger_abs_min & months_after_merger == months_after_merger_tiebreak, merging, NA),
    merging = first(na.omit(merging))
  ) %>% 
  ungroup() %>% 
  select(-starts_with("months_after_merger")) %>% 
  mutate(
    Merging = as.numeric(merging),
    Non_Merging = 1 - Merging,
    Post_Non_Merging = post_merger * (1 - Merging),
    Post_Merging = post_merger * Merging
  ) %>% 
  
  # 1.4 Controls and Dist_Changes---------------------------------------------
  mutate(demand_instruments0 = demand_instruments0 / distance) %>% 
  mutate(Dist_Change = as.factor(case_when(
    distance_change <= -128~ 1,
    is.na(distance_change) ~ NA_real_,
    TRUE ~ 2
  ))) %>%
  mutate(Dist_Change_2 = as.factor(case_when(
    distance_change < 0~ 1,
    is.na(distance_change) ~ NA_real_,
    TRUE ~ 2
  ))) %>% 
  mutate(Dist_Change_3 = as.factor(case_when(
    distance_change < -50~ 1,
    is.na(distance_change) ~ NA_real_,
    TRUE ~ 2
  ))) %>%
  mutate(Dist_Change_4 = as.factor(case_when(
    distance_change < -100~ 1,
    is.na(distance_change) ~ NA_real_,
    TRUE ~ 2
  ))) %>% 
  mutate(Dist_Change_5 = as.factor(case_when(
    distance_change < -200~ 1,
    is.na(distance_change) ~ NA_real_,
    TRUE ~ 2
  ))) %>%

  # 1.5 Quantity ------------------------------------------------------------
  mutate(lquant = log(volume)) %>% 
  #rename(Post_Merging = post_merger_merging) %>% 
  
  # 1.6 One year post completed ---------------------------------------------
  mutate(
    month_date = make_date(year, month),
    after = as.numeric(months_between(cutoff_c, month_date) >= 12),
    Post_Merger_1y = post_merger*after,
    Post_Merging_1y = Post_Merging*after,
    Post_Non_Merging_1y = Post_Non_Merging*after
  ) %>% 

  # 1.7 Announced vs. completed dummies -------------------------------------
  mutate(
    btween = as.numeric(month_date <= cutoff_c & month_date >= cutoff_a),
    Merging_btw = Merging * btween,
    Non_Merging_btw = Non_Merging * btween
  ) %>% 

  # 1.8 Minor post ----------------------------------------------------------
  mutate(
    Major = as.numeric(major_competitor),
    Post_Minor = (1 - Major) * Non_Merging * post_merger,
    Post_Major = Major * Non_Merging * post_merger
  ) %>% 

  # 1.9 HHI and DHHI -------------------------------------------------------
  mutate(
    parent_code = as.character(parent_code),
    owner = if_else(is.na(parent_code), owner, paste0(owner, parent_code)),
    owner_post = if_else(merging, "Merging", owner)
  ) %>% 
  select(-dhhi, -pre_hhi, -post_hhi) %>% 
  group_by(dma_code, owner_post) %>% 
  mutate(
    rownum = 1:n(),
    tot_vol_owner_post = if_else(rownum == 1, sum(volume * (1 - post_merger)), NA_real_)
  ) %>% 
  group_by(dma_code, owner) %>% 
  mutate(
    rownum = 1:n(),
    tot_vol_owner_pre = if_else(rownum == 1, sum(volume * (1 - post_merger)), NA_real_)
  ) %>% 
  group_by(dma_code) %>% 
  mutate(
    tot_vol_ = sum(volume * (1 - post_merger)),
    share_owner_pre = tot_vol_owner_pre/tot_vol_,
    share_owner_post = tot_vol_owner_post/tot_vol_,
    pre_hhi = sum(share_owner_pre^2, na.rm = TRUE),
    post_hhi = sum(share_owner_post^2, na.rm = TRUE)
  ) %>% 
  ungroup() %>% 
  mutate(
    dhhi = post_hhi - pre_hhi,
    pre_hhi_s = pre_hhi * 10000,
    post_hhi_s = post_hhi * 10000,
    dhhi_s = dhhi * 10000
  ) %>% 
  select(-starts_with("share_"), -starts_with("tot_vol_")) %>% 
  
  # 1.10 HHI bins -----------------------------------------------------------
  ### 1.10.1 Coarse HHI and DHHI bins ---------------------------------------
  mutate(
    HHI_bins = cutr(post_hhi_s, c(1500, 2500)),
    DHHI_bins = cutr(dhhi_s, c(100, 200))
  ) %>% 

  ### 1.10.2 Finer HHI and DHHI bins ------------------------------------------
  mutate(
    HHI_binsf = cutr(post_hhi_s, c(375, 750, 1125, 1500, 1750, 2000, 2250, 2500)),
    DHHI_binsf = cutr(dhhi_s, seq(25, 200, 25)),
    DHHI_HHI = pmin(HHI_binsf, DHHI_binsf)
  ) %>% 
  
  ### 1.10.3 Nocke and Whinston bins ------------------------------------------
  mutate(
    DHHI_HHI_NW = case_when(
      dhhi_s >= 200 & post_hhi_s >= 2500 ~ 2L,
      dhhi_s >= 100 & post_hhi_s >= 1500 ~ 1L,
      is.na(dhhi_s) | is.na(post_hhi_s) ~ 0L,
      TRUE ~ 0L
    )
  ) %>% 

  # 1.11 Months after and pre dummies ---------------------------------------
  mutate(
    Months = months_between(cutoff_c, month_date) + 25,
    Months = if_else(Months<0 | Months>49, NA_real_, Months),
    Months_post = if_else(Months >= 25, Months - 25, NA_real_),
    Months_post2 = replace_na(Months_post, 0)
  ) %>% 
  
  # 1.8 Untreated DMAs ------------------------------------------------------
  mutate(mkt_size = volume/shares) %>% 
    group_by(dma_code) %>% 
    mutate(tot_vol_mp = sum(volume * (Merging == 1) * (post_merger == 0))) %>% 
    group_by(dma_code, year, month) %>% 
    mutate(
      row_num = 1:n(),
      mkt_size_unique = if_else(row_num == 1 & post_merger == 0, mkt_size, 0)
    ) %>% 
    group_by(dma_code) %>% 
    mutate(
      tot_mkt_size = sum(mkt_size_unique, na.rm = TRUE),
      mp_share = tot_vol_mp/tot_mkt_size
    ) %>% 
    select(-row_num) %>% 
    ungroup() %>% 
    mutate(trend_fe = factor(trend)) %>% 
    as_tibble()

  for (i in c(2, 5, 10)) {
    df_1 <- df_1 %>% 
      mutate(
        Untreated = if_else(mp_share <= i/100, 1, 0),
        Post_Merging_Treat = (1 - Untreated) * Merging * post_merger,
        Post_Non_Merging_Treat = (1 - Untreated) * Non_Merging * post_merger,
        Merging_Treated = Merging * (1 - Untreated),
        Non_Merging_Treated = (1 - Merging) * (1 - Untreated),
        Merging_Treated_Post = Merging * (1 - Untreated) * post_merger,
        Non_Merging_Treated_Post = (1 - Merging) * (1 - Untreated) * post_merger,
        Treated = (1 - Untreated),
        Treated_Post = (1 - Untreated) * post_merger
      ) %>% 
      rename_at(vars(Untreated:Treated_Post), paste0, "_", i)
  }

# 2. MAIN ROUTINE ---------------------------------------------------------


# 2.0 Helper functions ----------------------------------------------------
# 2.0.1 Function to extract table of coefficients  ------------------------
# ----- and variables from fixef object -----------------------------------
extract_coeftable <- function(x) {
  dep_var <- as.character(x$fml)[2]
  indep_vars <- as.character(x$fml)[3]
  fixef_vars <- as.character(x$fml_all$fixef)[2]
  collin_vars <- tibble(var = glue("o.{x$collin.var}"))
  x$coeftable %>% 
    as.data.frame() %>% 
    rownames_to_column("var") %>% 
    bind_rows(collin_vars, .) %>% 
    clean_names() %>% 
    mutate(
      dep_var = dep_var,
      indep_vars = indep_vars,
      fixed_effects = fixef_vars,
      .before = var
    ) %>% 
    mutate(obs = x$nobs) %>% 
    as_tibble()
}

# 2.0.2. Extract coefficient table from fixef_multi object ----------------
extract_coeftable_multi <- function(fit) {
  fit_list <- as.list(fit)
  map_dfr(fit_list, extract_coeftable)
}


# 2.0.3. Run regressions and get coefficient table ------------------------
run_reg_block <- function(dep_vars, indep_vars, fixed_effects, df_reg, coeftable = TRUE) {
  dv <- glue("c({paste(dep_vars, collapse = ', ')})")
  iv <- paste(indep_vars, collapse = " + ")
  fe <- paste(fixed_effects, collapse = " + ")
  fml <- glue("{dv} ~ {iv} | {fe}") %>% 
    as.formula()
  fit <- try(feols(fml, data = df_reg, weights = ~weight, cluster = "dma_code"), silent = TRUE)
  if (class(fit) == "try-error") {
    err_msg <- as.character(fit)
    tibble(
      dep_var_call = dv,
      indep_var_call = iv,
      fixed_effect_call = fe,
      error_msg = err_msg
    )
  }
  else if (coeftable) {
    extract_coeftable_multi(fit)
  } else {
    fit
  }
}

# 3. MAIN ROUTINE FOR TIMING ----------------------------------------------

additive_test <- function(fit, vc, test_vars) {
  estimate <- extract_coeftable(fit) %>% 
    filter(var %in% test_vars) %>% 
    pull(estimate) %>% 
    sum()
  vc_test <- vc[test_vars, test_vars]
  test_se <- sqrt(sum(vc_test))
  tibble(
    estimate = estimate,
    test_se = test_se
  )
}

#      glue("Months::{i}:Merging")

do_tests <- function(fit, vc, id, merging_ind, i) {
  if (id == "Granular timing for post only") {
    test_vars <- c(
      glue("Merging::{merging_ind}"),
      glue("Months_post::{i - 25}"),
      if_else(glue("Months_post::{i - 25}:Merging") %in% names(fit$coefficients), glue("Months_post::{i - 25}:Merging"), glue("Merging:Months_post::{i - 25}"))
    )
  } else if (id == "Granular timing pre and post" || id == "Granular timing pre and post trend") {
    test_vars <- c(
      glue("Merging::{merging_ind}"),
      glue("Months::1"),
      glue("Months::2"),
      glue("Months::3"),
      glue("Months::4"),
      glue("Months::5"),
      glue("Months::6"),
      glue("Months::7"),
      glue("Months::8"),
      glue("Months::9"),
      glue("Months::10"),
      glue("Months::11"),
      glue("Months::12"),
      glue("Months::13"),
      glue("Months::14"),
      glue("Months::15"),
      glue("Months::16"),
      glue("Months::17"),
      glue("Months::18"),
      glue("Months::19"),
      glue("Months::20"),
      glue("Months::21"),
      glue("Months::22"),
      glue("Months::23"),
      glue("Months::24"),
      if_else(glue("Merging:Months::1") %in% names(fit$coefficients), glue("Merging:Months::1"), glue("Months::1:Merging")),
      if_else(glue("Merging:Months::2") %in% names(fit$coefficients), glue("Merging:Months::2"), glue("Months::2:Merging")),
      if_else(glue("Merging:Months::3") %in% names(fit$coefficients), glue("Merging:Months::3"), glue("Months::3:Merging")),
      if_else(glue("Merging:Months::4") %in% names(fit$coefficients), glue("Merging:Months::4"), glue("Months::4:Merging")),
      if_else(glue("Merging:Months::5") %in% names(fit$coefficients), glue("Merging:Months::5"), glue("Months::5:Merging")),
      if_else(glue("Merging:Months::6") %in% names(fit$coefficients), glue("Merging:Months::6"), glue("Months::6:Merging")),
      if_else(glue("Merging:Months::7") %in% names(fit$coefficients), glue("Merging:Months::7"), glue("Months::7:Merging")),
      if_else(glue("Merging:Months::8") %in% names(fit$coefficients), glue("Merging:Months::8"), glue("Months::8:Merging")),
      if_else(glue("Merging:Months::9") %in% names(fit$coefficients), glue("Merging:Months::9"), glue("Months::9:Merging")),
      if_else(glue("Merging:Months::10") %in% names(fit$coefficients), glue("Merging:Months::10"), glue("Months::10:Merging")),
      if_else(glue("Merging:Months::11") %in% names(fit$coefficients), glue("Merging:Months::11"), glue("Months::11:Merging")),
      if_else(glue("Merging:Months::12") %in% names(fit$coefficients), glue("Merging:Months::12"), glue("Months::12:Merging")),
      if_else(glue("Merging:Months::13") %in% names(fit$coefficients), glue("Merging:Months::13"), glue("Months::13:Merging")),
      if_else(glue("Merging:Months::14") %in% names(fit$coefficients), glue("Merging:Months::14"), glue("Months::14:Merging")),
      if_else(glue("Merging:Months::15") %in% names(fit$coefficients), glue("Merging:Months::15"), glue("Months::15:Merging")),
      if_else(glue("Merging:Months::16") %in% names(fit$coefficients), glue("Merging:Months::16"), glue("Months::16:Merging")),
      if_else(glue("Merging:Months::17") %in% names(fit$coefficients), glue("Merging:Months::17"), glue("Months::17:Merging")),
      if_else(glue("Merging:Months::18") %in% names(fit$coefficients), glue("Merging:Months::18"), glue("Months::18:Merging")),
      if_else(glue("Merging:Months::19") %in% names(fit$coefficients), glue("Merging:Months::19"), glue("Months::19:Merging")),
      if_else(glue("Merging:Months::20") %in% names(fit$coefficients), glue("Merging:Months::20"), glue("Months::20:Merging")),
      if_else(glue("Merging:Months::21") %in% names(fit$coefficients), glue("Merging:Months::21"), glue("Months::21:Merging")),
      if_else(glue("Merging:Months::22") %in% names(fit$coefficients), glue("Merging:Months::22"), glue("Months::22:Merging")),
      if_else(glue("Merging:Months::23") %in% names(fit$coefficients), glue("Merging:Months::23"), glue("Months::23:Merging")),
      if_else(glue("Merging:Months::24") %in% names(fit$coefficients), glue("Merging:Months::24"), glue("Months::24:Merging"))
    )
  } else if (id == "Granular timing for post2 only") {
    test_vars <- c(
      glue("Merging::{merging_ind}"),
      glue("Months_post2::{i - 25}"),
      if_else(glue("Months_post2::{i - 25}:Merging") %in% names(fit$coefficients), glue("Months_post2::{i - 25}:Merging"), glue("Merging:Months_post2::{i - 25}"))
    )
  } else {
    stop("ID missing from do_tests function")
  }
  
  if (merging_ind == 0) test_vars <- test_vars[-c(26, 49)]
  test_vars <- test_vars[test_vars %in% rownames(vc)]
  if (length(test_vars) == 0) {
    df_out <- tibble(estimate = NA_real_, test_se = NA_real_)
  } else {
    df_out <- additive_test(fit, vc, test_vars)
  }
  df_out %>% 
    mutate(
      id = id,
      i = i,
      merging_ind = merging_ind,
      .before = estimate
    )
}


main_routine_for_timing <- function(weightnum) {
  df_trend <- df_1 %>% 
    rename(weight = !!sym(glue('weights_{weightnum}'))) %>%
    filter(Months <= 24)
  fits_trend <- feols(lprice ~ brand_code_uc + brand_code_uc:trend, data = df_trend, weights = ~weight, cluster = "dma_code")
  
  df_1$pred_lprice <- predict(fits_trend,df_1)
  df_1$resid_lprice <- df_1$lprice - df_1$pred_lprice
  
  df_reg <- df_1 %>% 
    rename(weight = !!sym(glue('weights_{weightnum}')))
  max_month <- max(df_reg$Months, na.rm=TRUE)
  min_month <- min(df_reg$Months, na.rm=TRUE)
  dv_3 <- "resid_lprice"
  iv_3 <- c(
    "i(Merging)",
    "sw(i(Months_post, ref = 0) + Merging:i(Months_post, ref = 0), i(Months, ref = 25) + Merging:i(Months, ref = 25), i(Months_post2, ref = 0) + Merging:i(Months_post2, ref = 0))"
  )
  fe_3 <- "entity_effects"
  fits_3 <- run_reg_block(dv_3, iv_3, fe_3, df_reg, FALSE)
  
  # 3.1. Granular timing for post only --------------------------------------
  fit_3.1 <- fits_3$`i(Merging) + i(Months_post, ref = 0) + Merging:i(Months_post, ref = 0)`
  vc_3.1 <- vcov(fit_3.1)
  params_3.1 <- cross(list(merging_ind = 0:1, i = 25:max_month)) %>% 
    bind_rows()
  out_3.1 <- pmap_dfr(params_3.1, do_tests, id = "Granular timing for post only", fit = fit_3.1, vc = vc_3.1)
  
  # 3.2. Granular timing pre and post ---------------------------------------
  fit_3.2 <- fits_3$`i(Merging) + i(Months, ref = 25) + Merging:i(Months, ref = 25)`
  vc_3.2 <- vcov(fit_3.2)
  params_3.2 <- cross(list(merging_ind = 0:1, i = min_month:max_month)) %>% 
    bind_rows()
  out_3.2 <- pmap_dfr(params_3.2, do_tests, id = "Granular timing pre and post", fit = fit_3.2, vc = vc_3.2)
  
  # 3.3 Granular timing for post2 only --------------------------------------
  fit_3.3 <- fits_3$`i(Merging) + i(Months_post2, ref = 0) + Merging:i(Months_post2, ref = 0)`
  vc_3.3 <- vcov(fit_3.3)
  params_3.3 <- cross(list(merging_ind = 0:1, i = 25:max_month)) %>% 
    bind_rows()
  out_3.3 <- pmap_dfr(params_3.3, do_tests, id = "Granular timing for post2 only", fit = fit_3.3, vc = vc_3.3)
  
  bind_rows(out_3.1, out_3.2, out_3.3) %>% 
    mutate(weight = weightnum, .before = estimate)
}

main_routine_for_timing_out <- map_dfr(0:3, main_routine_for_timing)
main_routine_for_timing_out_path <- glue("{output_path}/Months_pretest.csv")
write_csv(main_routine_for_timing_out, main_routine_for_timing_out_path, na = "")

