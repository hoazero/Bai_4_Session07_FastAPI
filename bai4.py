from datetime import datetime
from fastapi import FastAPI, status, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()


# PHẦN 1: PHÂN TÍCH & ĐỀ XUẤT ĐA GIẢI PHÁP (ANALYSIS)
# 1. Khảo sát Input/Output:
#    - Input: order_id (Kiểu dữ liệu số nguyên int) lấy từ Path Parameter.
#    - Output thành công (200 OK): Trả về dữ liệu payment_status và method.
#    - Output thất bại (404/500): Trả về lỗi JSON đã được bọc gọn (Error Envelope).
#
# 2. Đề xuất giải pháp cho hệ thống lớn (hàng vạn đơn hàng/ngày):
#    - Giải pháp 1 (Duyệt List): Giữ nguyên orders_list, dùng vòng lặp for để tìm. 
#      Độ phức tạp thuật toán là O(n). Dữ liệu càng lớn, API phản hồi càng chậm.
#    - Giải pháp 2 (Dùng Dict): Chuyển đổi dữ liệu sang dạng Dictionary (Bảng băm).
#      Độ phức tạp là O(1), truy xuất trực tiếp qua Key, tối ưu latency tối đa.

# PHẦN 2: SO SÁNH & LỰA CHỌN GIẢI PHÁP (TRADE-OFF RATINGS)
# +-------------------+-------------------------+------------------------------+
# | Tiêu chí          | Giải pháp 1: Duyệt List | Giải pháp 2: Dùng Dict       |
# +-------------------+-------------------------+------------------------------+
# | Tốc độ tìm kiếm   | Chậm: O(n)              | Cực nhanh: O(1)              |
# | Bộ nhớ tiêu hao   | Thấp, tối ưu            | Cao hơn (tốn overhead băm)   |
# | Độ dễ hiểu        | Đơn giản, cơ bản        | Cần tư duy cấu trúc dữ liệu  |
# | Khả năng bảo trì  | Kém khi dữ liệu phình to| Rất tốt cho hệ thống lớn     |
# | Bối cảnh phù hợp  | < 1.000 phần tử cố định | Hệ thống lớn, traffic cao    |
# +-------------------+-------------------------+------------------------------+
# => KẾT LUẬN: Đội ngũ kỹ thuật chọn GIẢI PHÁP 2 (DÙNG DICT) vì cửa hàng phát sinh
# hàng vạn đơn hàng mới mỗi ngày. Đánh đổi một chút RAM để lấy tốc độ xử lý O(1),
# triệt tiêu High Latency là quyết định bắt buộc đối với hệ thống Backend.


orders_dict = {
    1: {"id": 1, "code": "SP001", "payment_status": "PAID", "method": "BANK_TRANSFER"},
    2: {"id": 2, "code": "SP002", "payment_status": "UNPAID", "method": "NONE"}
}

class PaymentResponse(BaseModel):
    payment_status: str
    method: str


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "statusCode": 500,
            "data": None,
            "error": "Internal Server Error",
            "message": "Hệ thống đang gặp sự cố gián đoạn. Vui lòng thử lại sau.",
            "timestamp": datetime.time().isoformat(), 
            "path": request.url.path
        }
    )

@app.get(
    "/orders/{order_id}/payment", 
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK
)
def get_order_payment(order_id: int):

    try:
        if order_id < 0:
            raise ZeroDivisionError()
            
        if order_id not in orders_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Đơn hàng với ID {order_id} không tồn tại trên hệ thống."
            )
            
        return orders_dict[order_id]

    except HTTPException as http_exc:
        raise http_exc
    except Exception as system_exc:
        raise system_exc