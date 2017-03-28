#' Connect to Python interpreter
#' @export
python_connect <- function(python_path = "python3") {
    pipe_dir <- tempfile("pipes_")
    out_pipe <- file.path(pipe_dir, "rToPython")
    in_pipe <- file.path(pipe_dir, "pythonToR")

    dir.create(pipe_dir)
    system2(paste(c("mkfifo", in_pipe), sep = " "))
    system2(paste(c("mkfifo", out_pipe), sep = " "))

    pc <- list()
    pc$proc <- pipe(paste(python_path,
                          file.path(find.package("rattlr"), "python/rattlr.py"),
                          pipe_dir, sep = " "),
                    "w")
    pc$pipe_dir <- pipe_dir
    pc$out_pipe <- file(out_pipe, "wb")
    pc$in_pipe <- file(in_pipe, "rb")

    pc
}

#' Send object to Python and wait for response
#' @export
python_send <- function(pc, obj) {
    j <- unclass(jsonlite::toJSON(obj))
    size <- as.integer(nchar(j) + 1)
    writeBin(size, con = pc$out_pipe, size = 4)
    writeBin(j, con = pc$out_pipe)
    flush(pc$out_pipe)

    size <- readBin(pc$in_pipe, what = "int", n = 1, size = 4)
    raw <- readBin(pc$in_pipe, what = "raw", n = size)
    jsonlite::fromJSON(rawToChar(raw), simplifyDataFrame = FALSE)
}

#' Evaluate expressions and/or statements in Python
#' @export
python_eval <- function(pc, exprs = c(), imports = c(), envir = NULL) {
    obj <- list(exprs = exprs,
                imports = imports)
    response <- python_send(pc, obj)

    while (!is.null(envir) && response$type == "request") {
        response <-
            if (exists(response$name, envir = envir)) {
                python_send(pc, list(name = response$name,
                                     value = envir[[response$name]]))
            } else {
                python_send(pc, list(missing = "missing"))
            }
    }

    response
}

#' Evaluate expressions and/or statements in Python and assign bindings
#' @export
python_eval_assign <- function(pc, exprs = c(), imports = c(), envir = globalenv()) {
    response <- python_eval(pc, exprs, imports, envir)

    lapply(response$bindings, function(b) {
        assign(b$name, b$value, envir = envir)
    })
    response$bindings <- NULL

    response
}

#' Evaluate expressions and/or statements in Python and assign bindings
#' @export
rattlr <- function(pc, ..., envir = globalenv()) {
    exprs <- c(...)
    response <- python_eval_assign(pc = pc, exprs = exprs, envir = envir)

    if (response$type == "primitive")
        response$value
    else
        response
}

#' Disconnect from a Python interpreter
#' @export
python_disconnect <- function(pc) {
    writeBin(as.integer(0), con = pc$out_pipe, size = 4)
    flush(pc$out_pipe)
    close(pc$in_pipe)
    close(pc$out_pipe)
}
