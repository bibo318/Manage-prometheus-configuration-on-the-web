# Dự Án Quản Lý Cấu Hình Promethues

Dự án này là một ứng dụng web được xây dựng bằng Flask, hỗ trợ quản lý cấu hình hệ thống. Nó cung cấp một giao diện người dùng trực quan để thêm, xem, chỉnh sửa và xóa cấu hình. Ngoài ra, dự án cũng bao gồm một script phụ (`passgen.py`) dùng để tạo hash mật khẩu, hỗ trợ tăng cường bảo mật.

## Tính Năng Chính

- **Quản Lý Cấu Hình**: Cho phép người dùng thêm và quản lý các cấu hình hệ thống qua giao diện web.
- **Xác Thực Người Dùng**: Đảm bảo an toàn thông tin với chức năng đăng nhập và xác thực.
- **Giao Diện Trực Quan**: Giao diện dễ sử dụng, với các chức năng như thêm, xóa, và xem cấu hình được tích hợp sẵn.
- **Tạo Hash Mật Khẩu**: `passgen.py` hỗ trợ tạo hash cho mật khẩu, tăng cường bảo mật cho ứng dụng.

## Công Nghệ Sử Dụng

- **Flask**: Framework chính cho ứng dụng web.
- **Werkzeug**: Được sử dụng cho bảo mật và hash mật khẩu.
- **HTML/CSS**: Để tạo giao diện người dùng trong thư mục `templates`.

Dự án này phù hợp cho việc quản lý cấu hình trong các hệ thống nhỏ hoặc dùng làm cơ sở để phát triển các ứng dụng quản lý phức tạp hơn.
- **Lưu ý**: Phải thay đổi các đường dẫn tới file cấu hình.
