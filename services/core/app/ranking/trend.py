def percent_change(current:float|int|None,baseline:float|int|None)->float|None:
    if current is None or baseline is None or float(baseline)<=0:return None
    return (float(current)-float(baseline))/float(baseline)
