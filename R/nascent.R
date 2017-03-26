#' Nascent pseudo-monad
#' @name nascent
NULL

#' @rdname nascent
#' @export
nascent <- function(x)
    structure(list(x),
              class = c("nascent",
                        "monad", "applicative", "functor"))

#' @export
print.nascent <- function(.j, ...) {
    cat("nascent(")
    cat(.j[[1]])
    cat(")\n")
}

#' @export
fmap_.nascent <- function(.f, .j)
    nascent(.f(.j[[1]]))

#' @export
pure_like_.nascent <- function(., .n) .n

#' @export
ap_.nascent <- function(.f, .j)
    fmap(.f[[1]], .j)

#' @export
ap_.nascent <- function(.f, .j)
    fmap(.f[[1]], .j)

#' @export
bind_.nascent <- function(.f, .j)
    .f(.j[[1]])
