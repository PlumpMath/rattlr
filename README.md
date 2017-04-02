# rattlr
<img src="https://raw.githubusercontent.com/farrellm/rattlr/master/snakes-99168.png"
 alt="rattlr logo" align="right" width = "200" />

> Your scientists were so preoccupied with whether or not they could,
> they didn’t stop to think if they should.
> - Ian from Jurasic Park

Transparent interop between R and Python

## Requirements

* Python 3
* NumPy
* Pandas

## Installation

Rattlr has not yet been submitted to CRAN. For now, you can install it via the `devtools` package:

```R
install.packages('devtools')
devtools::install_github('farrellm/rattlr')
```

## Tutorial
Startup a Python interpreter
```R
library(rattlr)

pc <- python_connect()
```

Shutdown a Python interpreter
```R
python_disconnect(pc)
```

Execute Python expressions and get result in R
```R
even_squares <- rattlr(pc,
                       "[x ** 2 for x in range(0, 9) if x % 2 == 0]")
# > even_squares
# [1]  0  4 16 36 64
```

Python variables begining with an underscore ('\_') are persisted in Python; they are not directly available in R.
```R
rattlr(pc,
       "_x = 1",
       "_y = 2",
       "_z = 3")

rattlr(pc,
       "[_x, _y, _z]")
# [1] 1 2 3
```
Python variables not begining with an underscore copied back to R as variables.
```R
rattlr(pc,
       "r = [7, 8, 9]")
# > r
# [1] 7 8 9
```

R variables are freely avaiable in Python, generally as NumPy arrays or Pandas dataframes
```R
s <- 8
v <- c(1,1,2,3,5)
m <- diag(3)

rattlr(pc, "str((type(s), s.shape))")
# [1] "(<class 'numpy.ndarray'>, (1,))"

rattlr(pc, "str((type(v), v.shape))")
# [1] "(<class 'numpy.ndarray'>, (5,))"

rattlr(pc, "str((type(m), m.shape))")
# [1] "(<class 'numpy.ndarray'>, (3, 3))"

rattlr(pc, "str((type(iris), iris.shape))")
# [1] "(<class 'pandas.core.frame.DataFrame'>, (150, 5))"
```

Modify an R dataframe from Python
```R
rattlr(pc,
       "iris['s2'] = iris['Sepal.Length'] ** 2")
```

Import and use libraries in Python
```R
rattlr(pc,
       "import os",
       "os.path.join('dir', 'file')")
# [1] "dir/file"
```
