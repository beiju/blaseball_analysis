from ebcic import ebcic


def error_bounds(k, n):
    p = ebcic.Params(
        k=k,
        n=n,
        confi_perc=95,
    )

    lower, upper = ebcic.exact(p)
    percent = k / n
    return (
        percent - upper,
        lower - percent
    )
