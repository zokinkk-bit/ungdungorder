# Script tạo mã QR - Cập nhật cho IP 192.168.1.2
import qrcode
import os

# Địa chỉ IP thật của máy tính Việt (IPv4 từ ipconfig)
# Lưu ý: Khi đổi mạng Wi-Fi khác, IP này có thể thay đổi, bạn cần cập nhật lại tại đây.
SERVER_IP = "192.168.1.2"
BASE_URL = f"http://{SERVER_IP}:8000/static/customer/index.html"

def create_qrs(number_of_tables):
    # Đường dẫn lưu mã QR trên ổ D
    save_path = r"D:\appoder\qr_codes"
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        print(f"📁 Đã tạo thư mục lưu trữ tại: {save_path}")

    print(f"🚀 Bắt đầu tạo QR Code cho {number_of_tables} bàn...")

    for i in range(1, number_of_tables + 1):
        # Tạo link đầy đủ kèm số bàn: http://192.168.1.2:8000/static/customer/index.html?table=1
        data = f"{BASE_URL}?table={i}"
        
        # Cấu hình QR code trông đẹp và dễ quét hơn
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Lưu file
        file_name = f"table_{i}.png"
        img.save(os.path.join(save_path, file_name))
        print(f"✅ Đã tạo xong: {file_name} (Link: {data})")

if __name__ == "__main__":
    # Bạn có thể đổi số 10 thành số bàn thực tế của quán
    create_qrs(10)
    print(f"\n✨ Xong! Việt hãy vào thư mục {r'D:\appoder\qr_codes'} để kiểm tra nhé.")