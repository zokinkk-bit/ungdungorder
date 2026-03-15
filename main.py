# File: main.py
# Hệ thống Quản lý Order - Việt Admin
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import urllib.parse
import json

import models
from database import engine, get_db

# Khởi tạo database
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- QUẢN LÝ WEBSOCKET ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def notify_all(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/admin")
async def admin_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- API CHO KHÁCH HÀNG ---
@app.get("/api/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@app.post("/api/order")
async def receive_order(order_data: dict, db: Session = Depends(get_db)):
    try:
        table = order_data.get('table', 0)
        item = order_data.get('item', 'Món không tên')
        qty = order_data.get('quantity', 1)

        new_order = models.Order(
            table_number=int(table),
            item_name=item,
            quantity=int(qty),
            total_price=0.0,
            status="pending"
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        payload = {
            "type": "new_order",
            "id": new_order.id,
            "table": new_order.table_number,
            "item_name": new_order.item_name,
            "quantity": new_order.quantity,
            "time": datetime.now().strftime("%H:%M:%S")
        }
        await manager.notify_all(payload)
        return {"status": "success", "order_id": new_order.id}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# --- API QUẢN TRỊ ---

@app.get("/api/admin/pending-orders")
def get_pending_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.status == "pending").all()
    return [
        {
            "id": o.id,
            "table": o.table_number,
            "item_name": o.item_name,
            "quantity": o.quantity,
            "time": o.created_at.strftime("%H:%M:%S") if o.created_at else ""
        } for o in orders
    ]

@app.post("/api/admin/products")
async def add_product(data: dict, db: Session = Depends(get_db)):
    existing_p = db.query(models.Product).filter(models.Product.name == data['name']).first()
    if existing_p:
        existing_p.price = float(data['price'])
    else:
        new_p = models.Product(name=data['name'], price=float(data['price']), image="")
        db.add(new_p)
    db.commit()
    await manager.notify_all({"type": "menu_update"})
    return {"status": "success"}

@app.delete("/api/admin/products/{product_name}")
async def delete_product(product_name: str, db: Session = Depends(get_db)):
    real_name = urllib.parse.unquote(product_name)
    product = db.query(models.Product).filter(models.Product.name == real_name).first()
    if product:
        db.delete(product)
        db.commit()
        await manager.notify_all({"type": "menu_update"})
        return {"status": "success"}
    return {"status": "error"}

@app.post("/api/orders/{order_id}/complete")
def complete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order:
        product = db.query(models.Product).filter(models.Product.name == order.item_name).first()
        if product:
            order.total_price = order.quantity * product.price
            order.status = "completed"
            db.commit()
            return {"status": "success"}
        else:
            order.status = "completed"
            db.commit()
            return {"status": "error", "msg": "Không tìm thấy món trong Menu để lấy giá"}
    return {"status": "error"}

@app.get("/api/admin/revenue")
def get_revenue(db: Session = Depends(get_db)):
    # Lấy danh sách các đơn đã xong để hiện chi tiết
    orders = db.query(models.Order).filter(models.Order.status == "completed").all()
    total = sum(order.total_price for order in orders)
    
    return {
        "revenue": total,
        "history": [
            {
                "table": o.table_number,
                "item": o.item_name,
                "qty": o.quantity,
                "amount": o.total_price,
                "time": o.created_at.strftime("%H:%M") if o.created_at else "Vừa xong"
            } for o in orders
        ]
    }

@app.post("/api/admin/reset")
def reset_data(data: dict, db: Session = Depends(get_db)):
    # MẬT KHẨU ADMIN LÀ: 123
    if data.get("password") == "huyhieu123":
        db.query(models.Order).delete()
        db.commit()
        return {"status": "success"}
    else:
        raise HTTPException(status_code=401, detail="Sai mật khẩu Admin!")

if __name__ == "__main__":
    import uvicorn
    import os
    # Lấy cổng từ hệ thống Cloud, nếu không có thì mặc định là 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)