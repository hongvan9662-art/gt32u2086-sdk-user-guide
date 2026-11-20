# Tài liệu GT32U2086 SDK User Guide

Kho này chứa nội dung của trang tài liệu web GT32U2086 SDK. Mỗi lần có thay đổi, GitHub tự tạo lại trang web và file PDF rồi đăng lên. Địa chỉ trang web nằm ở **Settings → Pages** (nút **Visit site**).

Có **2 cách sửa nội dung**, dùng cách nào cũng được.

---

## Cách 1: Sửa thẳng trên trang web (sửa nhanh vài chữ)

1. Mở thư mục **pages**, bấm vào file của chương cần sửa (xem bảng ở cuối trang này).
2. Bấm biểu tượng **bút chì** (Edit this file) ở góc trên bên phải.
3. Sửa chữ như soạn văn bản thường. Lưu ý:
   - Không xoá phần `{#...}` ở cuối dòng tiêu đề, đó là mã liên kết.
   - Một số ký tự cần thêm dấu `\` phía trước, ví dụ `\_`, `\#`, `\*`. Xem mục 3 trong file `HUONG_DAN_SUA.md`.
4. Bấm **Commit changes…**, ghi ngắn gọn đã sửa gì, rồi bấm **Commit changes**.
5. Khoảng 3–5 phút sau, trang web và file PDF tự cập nhật. Xem tiến độ ở tab **Actions**: chấm vàng là đang chạy, dấu tích xanh là xong.

## Cách 2: Sửa trong file Word (sửa nhiều, hoặc thêm mục mới)

1. **Luôn tải bản Word mới nhất trong kho về trước khi sửa:** bấm vào file `source_GT32U2086_SDK_User_Guide.docx` → nút **Download** (biểu tượng mũi tên tải xuống). Nếu sửa trên một bản cũ trong máy, những gì người khác đã cập nhật vào Word sẽ bị mất.
2. Sửa trong Word, giữ nguyên các kiểu chữ (Heading 1–5, Code, List Bullet…) như hướng dẫn trong `HUONG_DAN_SUA.md`.
3. Về trang chính của kho, bấm **Add file → Upload files**, kéo file Word vào, bấm **Commit changes**. Tên file khác cũng được, GitHub tự đổi về tên chuẩn.
4. GitHub tự cập nhật các trang từ file Word, đồng thời **giữ lại những chỗ đã sửa thẳng trên trang web** (cách 1).

## Khi cùng một đoạn bị sửa khác nhau ở cả Word và trang web

GitHub không tự chọn bên nào. Khi đó:

- Tab **Actions** hiện dấu **X đỏ**.
- Trang web vẫn được tạo lại, nhưng **chưa có nội dung của file Word mới**.
- Bấm vào lần chạy có dấu X đỏ, kéo xuống phần **Summary** để xem đoạn nào bị trùng và nội dung ở mỗi bên.

Cách xử lý (chọn một):

1. Sửa file Word cho giống chỗ đã sửa trên trang web, rồi tải file Word lên lại.
2. Lấy nội dung Word ở những đoạn trùng: tab **Actions** → bấm **Tao trang tai lieu** ở bên trái → nút **Run workflow** → đánh dấu ô *"Lấy nội dung file Word ở những đoạn bị sửa khác nhau"* → **Run workflow**. Những chỗ sửa khác trên trang web vẫn được giữ.

## Lưu ý

- **File Word không tự có những chỗ sửa trên trang web.** Để file Word luôn đầy đủ, người giữ file Word nên chép các chỗ đó vào Word. Xem những gì đã sửa trên web: mở thư mục **pages** → nút **History** (biểu tượng đồng hồ).
- Mọi thay đổi đều được lưu lại. Muốn xem hoặc lấy lại bản cũ của một trang: mở file → **History**.
- Chỉ những người được mời (Settings → Collaborators) mới sửa được. Người ngoài chỉ xem, hoặc gửi đề xuất sửa để chủ kho duyệt.

## File của từng chương

| File trong thư mục pages | Nội dung |
|---|---|
| `01_chapter_1.md` | Chapter 1: GT32U2086 SDK Overview and Development Environment |
| `02_chapter_2.md` | Chapter 2: GT32U2086 Application Requirements |
| `03_chapter_3.md` | Chapter 3: First Application and UART Firmware Programming |
| `04_chapter_4.md` | Chapter 4: Project Configuration and Module Organization |
| `05_chapter_5.md` | Chapter 5: Basic Peripherals and Communication Interfaces |
| `06_chapter_6.md` | Chapter 6: Advanced Peripherals and Data Processing |
| `07_chapter_7.md` | Chapter 7: Task Initialization and Management on GT32U2086 |
| `08_chapter_8.md` | Chapter 8: Scheduling and Software Timers |
| `09_chapter_9.md` | Chapter 9: Inter-Task Communication and Synchronization |
| `10_chapter_10.md` | Chapter 10: PC Flashing Tool and Firmware Updates |
| `11_chapter_11.md` | Chapter 11: Troubleshooting |
| `12_appendix_a.md` | Appendix A: Status Codes and API Reference |
| `part1.md` … `part5.md` | Trang của từng PART (thẻ mục lục, tự tạo) |
| `README.md` (thư mục gốc) | Trang chủ |
