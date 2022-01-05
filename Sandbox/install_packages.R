# 0. Overhead -------------------------------------------------------------
# 0.1 Load/install packages -----------------------------------------------
rm(list = ls())
installed_packages <- .packages(all.available = TRUE)
load_packages <- function(x) {
  if (!x %in% installed_packages) install.packages(x)
  library(x, character.only = TRUE)
}
