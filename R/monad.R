#' Functor typeclass
#' @name functor
NULL

#' @rdname functor
#' @export
fmap <- function(...)
    fmap_(...)

#' @rdname functor
#' @export
fmap_ <- function(.f, .m, ...)
    UseMethod("fmap_", .m)

#' Applicative typeclass
#' @name applicative
NULL

#' @rdname applicative
#' @export
pure <- function(...)
    nascent(...)

#' @rdname applicative
#' @export
pure_like <- function(...)
    pure_like_(...)

#' @rdname applicative
#' @export
pure_like_ <- function(...)
    UseMethod("pure_like_")

#' @rdname applicative
#' @export
ap <- function(...)
    ap_(...)

#' @rdname applicative
#' @export
ap_ <- function(.f, .m, ...) {
    if (length(class(.f)) == length(class(.m)) &&
        class(.f) == class(.m)) {}
    else if (!is.null(attr(.f, "type")) && !is.null(attr(.m, "type")) &&
             attr(.f, "type") == attr(.m, "type")) {}
    else if (is(.m, "nascent"))
        .f <- pure_like(.m, .f)
    else if (is(.f, "nascent"))
        .m <- pure_like(.f, .m)
    else
        stop("type mismatch in ap")
    UseMethod("ap_")
}

#' Monad typeclass
#' @name monad
NULL

#' @rdname monad
#' @export
bind <- function(.f, .m, ...) {
    res <- bind_(.f, .m, ...)

    if (length(class(res)) == length(class(.m)) &&
        class(res) == class(.m)) {}
    else if (!is.null(attr(res, "type")) && !is.null(attr(.m, "type")) &&
             attr(res, "type") == attr(.m, "type")) {}
    else if (is(.m, "nascent")) {}
    else if (is(res, "nascent"))
        res <- pure_like(.m, res)
    else
        stop("type mismatch in bind")

    res
}

#' @rdname monad
#' @export
bind_ <- function(.f, .m, ...)
    UseMethod("bind_", .m)

#' @rdname functor
#' @export
`%$%` <- function(f, x) f(x)

## #' @rdname functor
## #' @export
## `%<<<%` <- function(f, g) function(...) f(g(...))

#' @rdname functor
#' @export
`%&%` <- function(x, f) f(x)

#' @rdname functor
#' @export
`%<$>%` <- function(...) fmap(...)

#' @rdname applicative
#' @export
`%<*>%` <- function(...) ap(...)

#' @rdname monad
#' @export
`%>>=%` <- function(m, f) bind(f, m)

#' @rdname monad
#' @export
`%=<<%` <- function(...) bind(...)
