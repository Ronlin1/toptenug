from .normalizers import normalize
def evaluate_metric(values:list[float|int|None],normalization:str)->list[float|None]: return normalize(normalization,values)
