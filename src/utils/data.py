import dataclasses


@dataclasses.dataclass
class ComputeNodeParams:
    group: str
    allocation_time: str
    cluster: str
    partition: str
    cores: int
    
    
__all__ = ["ComputeNodeParams"]