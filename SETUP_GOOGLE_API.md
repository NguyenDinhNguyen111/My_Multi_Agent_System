# 🔐 Hướng dẫn Thiết lập Google Workspace API (OAuth 2.0)

Để hệ thống Trợ lý ảo Đa tác nhân có quyền đọc/gửi email và đặt lịch họp, hệ thống cần được cấp quyền thông qua cơ chế OAuth 2.0 của Google. Quá trình này sẽ cung cấp file `credentials.json`.

Dưới đây là các bước thực hiện chi tiết trên nền tảng Google Cloud Console.

## Bước 1: Tạo dự án trên Google Cloud Platform (GCP)
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/).
2. Đăng nhập bằng tài khoản Google của bạn.
3. Nhấn vào mục thả xuống chọn dự án ở góc trên bên trái.
4. Nhấn nút **New Project** (Dự án mới).
5. Đặt tên dự án (ví dụ: `Multi-Agent-Office-Assistant`) và nhấn **Create** (Tạo). Đợi vài giây để hệ thống khởi tạo.
6. Khi hệ thống khởi tạo thành công, nhấn chọn dự án (Select Project) mới vừa được tạo ở phần thông báo (Notifications) hiện ra.

## Bước 2: Kích hoạt các API cần thiết
1. Trong thanh tìm kiếm ở giữa trên cùng, gõ **"Gmail API"** và chọn kết quả tương ứng.
2. Nhấn nút **Enable** (Bật).
3. Tiếp tục quay lại thanh tìm kiếm, gõ **"Google Calendar API"**.
4. Nhấn nút **Enable** (Bật).

## Bước 3: Cấu hình Màn hình đồng ý OAuth (OAuth Consent Screen)
Đây là màn hình sẽ xuất hiện khi ứng dụng yêu cầu cấp quyền từ người dùng.
1. Ở menu bên trái, chọn **APIs & Services** (API và Dịch vụ) > **OAuth consent screen** > **Get Started**.
2. Điền các thông tin bắt buộc:
   - **App name**: Tên ứng dụng (VD: *Tro Ly Ao Van Phong*).
   - **User support email**: Chọn email của bạn.
   - **Audience**: chọn **External**
   - **Contact information**: Nhập email của bạn.
   - **Finish**: chọn "I agree to the Google API Services: User Data Policy." rồi nhấn Continue. 
   - Cuối cùng là chọn **Create**
3. Ở menu bên trái, chọn **Data Access** > Nhấn **Add or Remove Scopes**. Bạn cần đảm bảo cấp chính xác 2 quyền hạn sau để khớp với mã nguồn hệ thống:
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/calendar`
   - Nhấn **Update**, sau đó kéo xuống và chọn **Save**.
4. Ở menu bên trái, chọn **Audience** > kéo xuống phần **Test users (Người dùng thử nghiệm):** *Bước này cực kỳ quan trọng!* Do ứng dụng chưa được Google kiểm duyệt công khai, bạn phải tự thêm email của mình vào danh sách này. Nhấn **Add Users** và nhập email Google bạn dự định sử dụng để kiểm thử (Có thể nhập chính email hiện tại). Nhấn **Save**.

## Bước 4: Tạo thông tin xác thực (Credentials)
1. Ở menu bên trái, chọn **Clients**.
2. Nhấn **Create Clients**.
3. Ở mục **Application type**, chọn **Desktop app** (Ứng dụng cho máy tính để bàn).
4. Đặt tên (VD: `Streamlit Local Client`) và nhấn **Create**.
5. Một cửa sổ hiện ra thông báo thành công. Nhấn vào nút **Download JSON**.
6. **Quan trọng:** Đổi tên file vừa tải về thành `credentials.json` và lưu nó vào thư mục gốc của dự án.

## Bước 5: Lần chạy đầu tiên (First Run & Authentication)
1. Khi khởi chạy hệ thống lần đầu, bạn cần chạy file `setup_auth.py`
2. Một tab trình duyệt web sẽ tự động mở lên yêu cầu bạn đăng nhập.
3. Chọn đúng tài khoản email đã đăng ký ở phần *Test users*.
4. Nếu Google hiển thị cảnh báo *"Google hasn’t verified this app"*, nhấn vào **Advanced** (Nâng cao) > Chọn **Go to... (unsafe)** để tiếp tục.
5. Nhấn **Continue/Allow** để cấp quyền.
6. Quay lại thư mục mã nguồn, bạn sẽ thấy hệ thống tự động sinh ra file `token.json`. Ở những lần chạy tiếp theo, hệ thống sẽ sử dụng file token này và không yêu cầu đăng nhập lại.

> ⚠️ **Lưu ý Bảo mật:** File `credentials.json` và `token.json` mang quyền truy cập trực tiếp vào email và lịch trình. Tuyệt đối **KHÔNG** tải hai file này lên GitHub hay bất kỳ kho lưu trữ công khai nào.