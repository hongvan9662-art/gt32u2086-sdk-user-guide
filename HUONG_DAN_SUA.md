# Hướng dẫn sửa tài liệu GT32U2086 SDK (bản web)

Tài liệu web được Doxygen tạo ra từ các file trong thư mục này. **Chỉ sửa file nguồn**, không sửa trong `build/` vì thư mục đó bị tạo lại sau mỗi lần build.

## 1. Thư mục

| Đường dẫn | Nội dung | Ai sửa |
|---|---|---|
| `source_GT32U2086_SDK_User_Guide.docx` | File Word gốc mà bản web đang dùng | Bạn |
| `README.md` | Trang chủ: tiêu đề, thẻ mục lục các PART, link PDF | Tự tạo từ Word |
| `pages/01_chapter_1.md` … `12_appendix_a.md` | Mỗi chương là một file | Bạn / kỹ sư |
| `pages/part1.md` … `part5.md` | Trang của từng PART: thẻ mục lục các chương | Tự tạo từ Word |
| `theme/gt32u2086.js` | Thanh đường dẫn, thẻ mục lục, nút Copy | Kỹ sư |
| `tools/docx_to_pages.py` | Chuyển file Word thành các trang | Kỹ sư |
| `tools/sync_from_word.py` | Cập nhật trang từ file Word mới, giữ chỗ sửa trên web | Kỹ sư |
| `.github/workflows/build.yml` | GitHub tự tạo trang và đăng lên GitHub Pages | Kỹ sư |
| `.github/README.md` | Hướng dẫn sửa cho thành viên (hiện ở trang chính của kho GitHub) | Bạn |
| `images/` | Logo GTINX (bản màu và bản trắng cho chế độ tối) | Bạn |
| `theme/gt32u2086.css` | Màu, font, cỡ chữ | Bạn |
| `theme/header.html`, `theme/footer.html` | Thanh trên cùng và dòng bản quyền | Bạn |
| `Doxyfile` | Cấu hình Doxygen (tên dự án, phiên bản…) | Kỹ sư |
| `build.sh` | Lệnh tạo web và PDF | Kỹ sư |

## 2. Cập nhật khi có file Word mới

### Khi tài liệu nằm trên GitHub (cách nên dùng)

Chỉ cần tải file Word mới lên kho (Add file → Upload files). GitHub tự chạy `tools/sync_from_word.py` rồi `build.sh` và đăng trang lên GitHub Pages (xem `.github/workflows/build.yml`).

`tools/sync_from_word.py` cập nhật các trang từ file Word nhưng **giữ những chỗ đã sửa thẳng trên trang web**: nó so 3 bản của mỗi trang (bản tạo từ Word lần trước, bản hiện tại, bản tạo từ Word mới). Nếu cùng một đoạn bị sửa khác nhau ở cả hai nơi, nó không cập nhật gì từ Word và báo lỗi kèm danh sách đoạn trùng (tab Actions → lần chạy có dấu X đỏ → Summary). Cách xử lý xem trong `.github/README.md`.

Bản "tạo từ Word lần trước" được lưu ở tag `word-base` trong kho. Không xoá tag này.

### Khi làm trên máy tính

```
python3 tools/sync_from_word.py
./build.sh
```

Chép file Word mới vào thư mục này với tên `source_GT32U2086_SDK_User_Guide.docx` trước khi chạy. Lệnh đầu cập nhật trang chủ, trang PART, trang chương và dữ liệu thanh đường dẫn từ file Word (giữ chỗ sửa trên web như trên); thư mục phải là kho git đã có tag `word-base`. Lệnh sau tạo web và PDF.

Nếu muốn tạo lại toàn bộ trang từ Word, bỏ hết chỗ sửa trên web: `python3 tools/docx_to_pages.py source_GT32U2086_SDK_User_Guide.docx`.

### Cách đánh dấu trong Word để web tự định dạng

| Muốn có trên web | Cách viết trong file Word |
|---|---|
| Tên bảng / tên hình (căn giữa, nằm trên bảng/hình) | Dùng style **Caption**, hoặc bắt đầu đoạn bằng `Table 1-2.` / `Figure 3-1.`. Viết trên hay dưới bảng/hình đều được, web luôn đưa lên trên. |
| Khung IMPORTANT / CAUTION / WARNING (thanh đỏ) | Đoạn văn bắt đầu bằng `IMPORTANT:` / `CAUTION:` / `WARNING:`, hoặc bảng 1 cột có hàng đầu ghi `IMPORTANT` (các hàng dưới là nội dung). |
| Khung NOTE (kẻ trên và dưới) | Đoạn văn bắt đầu bằng `NOTE:`, hoặc bảng 1 cột có hàng đầu ghi `NOTE`. |
| Hình | Chèn hình vào Word như bình thường; web tự lấy hình ra. |

Bảng thường: hàng đầu là tiêu đề (nền xám, chữ đậm), cột đầu chữ đậm, cột chữ căn trái, cột mã ngắn (≤ 12 ký tự) căn giữa.

## 3. Sửa chữ trực tiếp (sửa nhỏ, khẩn)

Mở file chương (ví dụ `pages/03_chapter_3.md`) bằng VS Code, Typora hoặc Obsidian và sửa như văn bản thường.

- `#` là tên chương (mỗi file chỉ có một dòng `#`). `##` là mục 3.1, 3.2…; `###` là mục nhỏ hơn.
- Phần `{#ch03_...}` ở cuối tiêu đề là mã liên kết. Giữ nguyên, không xoá.
- Dòng trống để tách đoạn.
- Bảng: các ô cách nhau bằng dấu `|`, xuống dòng là sang hàng mới.
- Code: đặt giữa hai dòng ```` ``` ````. Trong khối code, gõ bình thường, không cần ký tự thoát.

**Ký tự đặc biệt trong đoạn văn** (bên ngoài khối code), cần thêm dấu `\` phía trước:

| Muốn hiện | Gõ |
|---|---|
| `_` ở đầu hoặc cuối một từ (ví dụ `__APP_NAME__`) | `\_` |
| `#include` | `\#include` |
| `--port` | `\--port` |
| `*` | `\*` |
| `<module>` | `&lt;module&gt;` |
| `1.` ở đầu dòng (giữ số bước như bản Word) | `1\.` |

## 4. Thêm hình (khi có hình chính thức)

Đặt file hình (`.svg`, `.png`) vào thư mục `images/`, rồi chèn vào chương bằng dòng:

```
![Tên hình](ten_file.svg)
```

Nếu vẽ bằng draw.io, lưu dạng `.drawio.svg` để sau này mở ra sửa tiếp được.

## 5. Đổi màu, font, cỡ chữ

Mở `theme/gt32u2086.css`. Mọi thông số nằm trong hai khối ở đầu file:

- `:root`: chế độ sáng. Màu chính `#0070C0`, font Inter, cỡ chữ Heading 1–5 và chữ thường.
- `html.dark-mode`: chế độ tối. Màu chính `#4DA3E0`.

Đổi logo: thay hai file trong `images/`, giữ nguyên tên file.
Đổi dòng bản quyền: sửa `theme/footer.html` (có 2 chỗ) và dòng `COPYRIGHT` trong `tools/make_pdf.js`.
Đổi số phiên bản: sửa chữ `User Guide v1.0` trong `tools/postprocess.py` (tên mục trong menu trái) và dòng `VERSION` trong `tools/make_pdf.js` (bìa và chân trang PDF).
Đổi chữ "Document" dưới GT32U2086 SDK ở đầu trang: sửa `PROJECT_BRIEF` trong `Doxyfile`.
Thẻ mục lục: số dòng hiện sẵn trước khi bấm mũi tên là `MAX_LINES = 5` trong `theme/gt32u2086.js`.

## 6. Build và xem

Máy cần có Doxygen (1.9.8 trở lên) và Node.js kèm Playwright (Playwright dùng để xuất PDF).

```
./build.sh
```

Sau đó mở `build/html/index.html` bằng trình duyệt. File PDF nằm ở `build/html/GT32U2086_SDK_User_Guide.pdf`. Để đăng lên web, chép toàn bộ thư mục `build/html/` lên máy chủ hoặc GitHub Pages.

## 7. Nối với code SDK (dành cho kỹ sư)

Phụ lục A hiện giữ nguyên như bản Word. Để Doxygen tự sinh phần tra cứu API từ code, thêm thư mục header của SDK vào `INPUT` trong `Doxyfile` (ví dụ `INPUT = README.md pages ../neon-mdf/components`), đặt `FILE_PATTERNS = *.md *.h` và `EXTRACT_ALL = YES`. Sau đó viết chú thích `/** @brief ... */` trong các file `.h`.
