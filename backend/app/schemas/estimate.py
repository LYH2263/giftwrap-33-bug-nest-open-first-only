from pydantic import BaseModel

class EstimateRequest(BaseModel):
    # 单盒测算（保留兼容）；与 box_ids 二选一，同时给时以 box_ids 为准
    box_id: int | None = None
    # 套盒合并：一次提交多个 clean 礼盒 id
    box_ids: list[int] | None = None
    overlap: float | None = None
    wrap_style: str = "cross"
    save: bool = False
    note: str = ""
