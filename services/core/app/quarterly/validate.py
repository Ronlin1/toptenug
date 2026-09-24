from dataclasses import dataclass,field
@dataclass(frozen=True)
class ValidationInput:
    provenance_complete:bool; stale_critical_sources:bool; algorithm_version:str; expected_algorithm_version:str; ranks:list[int]; factor_coverages:list[float]; metric_pairs:list[tuple[str,float,float]]=field(default_factory=list); minimum_factor_coverage:float=0
@dataclass(frozen=True)
class ValidationReport:
    errors:tuple[str,...]=(); blocking_anomalies:tuple[str,...]=()
    @property
    def ok(self)->bool:return not self.errors and not self.blocking_anomalies
class QuarterValidator:
    def __init__(self,*,max_growth_ratio:float=20)->None:self.max_growth_ratio=max_growth_ratio
    def validate(self,p:ValidationInput)->ValidationReport:
        errors=[]; anomalies=[]
        if not p.provenance_complete:errors.append('provenance_incomplete')
        if p.stale_critical_sources:errors.append('critical_source_stale')
        if p.algorithm_version!=p.expected_algorithm_version:errors.append('algorithm_version_mismatch')
        if len(p.ranks)!=len(set(p.ranks)):errors.append('duplicate_rank')
        if p.ranks and sorted(p.ranks)!=list(range(1,len(p.ranks)+1)):errors.append('non_contiguous_rank')
        if any(c<p.minimum_factor_coverage for c in p.factor_coverages):errors.append('factor_coverage_below_minimum')
        for metric,prev,current in p.metric_pairs:
            if prev<0 or current<0:errors.append(f'impossible_negative:{metric}'); continue
            if prev==0:
                if current>0:anomalies.append(f'zero_baseline_jump:{metric}')
                continue
            ratio=current/prev
            if ratio>=self.max_growth_ratio:anomalies.append(f'extreme_jump:{metric}:{ratio:.2f}x')
        return ValidationReport(tuple(errors),tuple(anomalies))
