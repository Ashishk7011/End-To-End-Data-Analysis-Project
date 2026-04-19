def format(value):
    if value >= 1e6:
        return f'{value/1e6:.2f}M'
    elif value >= 1e3:
        return f'{value/1e3:.2f}K'
    else:
        return str(value)