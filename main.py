from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE TẠM THỜI (Sẽ mất khi Render restart, nhưng dùng tốt cho lúc này) ---
# Cấu trúc mới: Mỗi dữ liệu đều có 'owner'
products = [] # Ví dụ: {"name": "Cafe", "price": 20000, "owner": "viet_admin", "image": "..."}
orders = []   # Ví dụ: {"id": 1, "table": "5", "item": "Cafe", "owner": "viet_admin", "status": "pending"}

# Quản lý kết nối WebSocket cho từng chủ quán
class ConnectionManager:
    def __init__(self):
        # Lưu kết nối theo owner: { "viet_admin": [ws1, ws2], "quan_khac": [ws3] }
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, owner: str):
        await websocket.accept()
        if owner not in self.active_connections:
            self.active_connections[owner] = []
        self.active_connections[owner].append(websocket)

    def disconnect(self, websocket: WebSocket, owner: str):
        if owner in self.active_connections:
            self.active_connections[owner].remove(websocket)

    async def send_personal_message(self, message: dict, owner: str):
        if owner in self.active_connections:
            for connection in self.active_connections[owner]:
                await connection.send_json(message)

manager = ConnectionManager()

# --- MODELS ---
class Product(BaseModel):
    name: str
    price: int
    image: str = ""
    owner: str  # Bắt buộc có chủ sở hữu

class Order(BaseModel):
    table: str
    item: str
    quantity: int
    owner: str  # Bắt buộc biết khách đặt ở quán nào

# --- API CHO KHÁCH HÀNG ---

# Lấy menu của một quán cụ thể
@app.get("/api/products/{owner}")
async def get_products(owner: str):
    shop_menu = [p for p in products if p["owner"] == owner]
    return shop_menu

# Đặt món gửi kèm thông tin quán
@app.post("/api/order")
async def create_order(order: Order):
    new_order = {
        "id": len(orders) + 1,
        "table": order.table,
        "item": order.item,
        "quantity": order.quantity,
        "owner": order.owner,
        "status": "pending",
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    }
    orders.append(new_order)
    # Chỉ thông báo cho đúng chủ quán đó qua WebSocket
    await manager.send_personal_message({"type": "new_order", **new_order}, order.owner)
    return {"status": "success", "order_id": new_order["id"]}

# --- API CHO ADMIN (QUẢN LÝ) ---

# Thêm món vào menu của mình
@app.post("/api/admin/products")
async def add_product(product: Product):
    products.append(product.dict())
    # Thông báo để menu khách hàng tự cập nhật (nếu đang mở)
    await manager.send_personal_message({"type": "menu_update"}, product.owner)
    return {"status": "success"}

# Lấy đơn hàng của riêng mình
@app.get("/api/admin/pending-orders/{owner}")
async def get_admin_orders(owner: str):
    return [o for o in orders if o["owner"] == owner and o["status"] == "pending"]

# Xong đơn
@app.post("/api/orders/{order_id}/complete")
async def complete_order(order_id: int):
    for o in orders:
        if o["id"] == order_id:
            o["status"] = "completed"
            return {"status": "success"}
    raise HTTPException(status_code=404, detail="Order not found")

# Xóa món của riêng mình
@app.delete("/api/admin/products/{owner}/{name}")
async def delete_product(owner: str, name: str):
    global products
    products = [p for p in products if not (p["name"] == name and p["owner"] == owner)]
    await manager.send_personal_message({"type": "menu_update"}, owner)
    return {"status": "success"}

# --- WEBSOCKET ---
@app.websocket("/ws/{owner}")
async def websocket_endpoint(websocket: WebSocket, owner: str):
    await manager.connect(websocket, owner)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, owner)