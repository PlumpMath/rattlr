#' Maybe monad
#' @name maybe
NULL

#' @rdname maybe
#' @export
nothing <-
    structure(list(),
              type = "maybe",
              class = c("nothing", "maybe",
                        "monad", "applicative", "functor"))

#' @rdname maybe
#' @export
just <- function(.v)
    structure(list(.v),
              type = "maybe",
              class = c("just", "maybe",
                        "monad", "applicative", "functor"))

#' @export
print.nothing <- function(...)
    cat("nothing\n")

#' @export
print.just <- function(.j, ...) {
    cat("just(")
    cat(.j[[1]])
    cat(")\n")
}

#' @export
fmap_.nothing <- function(...) nothing

#' @export
fmap_.just <- function(.f, .j)
    just(.f(.j[[1]]))

#' @export
pure_like_.maybe <- function(., .n)
    just(.n[[1]])

#' @export
ap_.nothing <- function(...) nothing

#' @export
ap_.just <- function(.f, .j)
    fmap(.f[[1]], .j)

#' @export
bind_.nothing <- function(...) nothing

#' @export
bind_.just <- function(.f, .j)
    .f(.j[[1]])

## fmap(sin, nothing)
## fmap(sin, just(pi / 2))

## ap(nothing, nothing)
## ap(nothing, just(pi / 2))
## ap(just(sin), nothing)
## ap(just(sin), just(pi / 2))
