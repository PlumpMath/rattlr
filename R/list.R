#' @export
fmap_.list <- function(.f, .l)
    lapply(.l, .f)

#' @export
pure_like_.list <- function(., .n)
    unclass(.n)

#' @export
ap_.list <- function(.f, .l)
    do.call(c, lapply(.f, function(f) lapply(.l, f)))

#' @export
bind_.list <- function(.f, .l)
    do.call(c, lapply(.l, .f))
