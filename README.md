<div align="center">

<img src="assets/logo-symbol-v2.png" alt="Biểu tượng khối 3D ghép nối, không có chữ" width="180" />

# OpenSCAD Design MCP

**Nhờ AI tạo mô hình 3D, xem trước và xuất tệp để chuẩn bị in.**

Hướng dẫn cho Windows 10/11 · Không cần biết lập trình để bắt đầu sử dụng

</div>

Bạn mô tả vật muốn tạo bằng lời, chẳng hạn “tạo một hộp không nắp, dài 60 mm, rộng 40 mm, cao 25 mm”. Ứng dụng AI dùng OpenSCAD Design MCP để dựng mô hình, tạo ảnh xem trước và kiểm tra kích thước. Bạn xem ảnh, yêu cầu sửa rồi lấy tệp để mở trong phần mềm in 3D.

Đây là công cụ bổ sung cho ứng dụng AI, không có cửa sổ trò chuyện riêng. **MCP** là cách để ứng dụng AI gọi các công cụ trên máy của bạn. Bạn chỉ cần kết nối một lần theo hướng dẫn dưới đây.

## Bắt đầu từ đâu?

1. [Cài đặt lần đầu](#cai-lan-dau).
2. [Chạy mô hình mẫu để kiểm tra máy](#chay-thu).
3. [Kết nối với ứng dụng AI bạn đang dùng](#ket-noi).
4. [Tạo mô hình đầu tiên bằng lời](#model-dau-tien).
5. [Tìm ảnh và tệp kết quả](#tep-ket-qua).

Nếu gặp lỗi, xem [cách xử lý](#go-loi). Nếu đã cài dự án ở `D:\Code\openscad-design-mcp`, mở PowerShell, chạy `cd D:\Code\openscad-design-mcp` rồi bắt đầu từ bước chạy thử.

<a id="cai-lan-dau"></a>

## 1. Cài đặt lần đầu

Cài ba phần mềm sau bằng bộ cài dành cho Windows:

| Phần mềm | Dùng để làm gì? | Lưu ý |
|---|---|---|
| [Python](https://www.python.org/downloads/windows/) | Chạy công cụ này | Phiên bản 3.11 trở lên; nếu bộ cài có **Add Python to PATH**, hãy chọn |
| [OpenSCAD](https://openscad.org/downloads.html) | Dựng mô hình và tạo ảnh | Có thể dùng vị trí cài mặc định |
| [Git](https://git-scm.com/download/win) | Tải dự án từ GitHub | Có thể giữ các lựa chọn mặc định của bộ cài |

Bạn cũng cần một ứng dụng AI hỗ trợ MCP, ví dụ Antigravity, Codex, OpenCode hoặc Claude Desktop. Tài khoản và chi phí sử dụng AI tùy ứng dụng; dự án này không cung cấp tài khoản AI.

Nhấn phím Windows, tìm **PowerShell** và mở nó. Nếu vừa cài phần mềm, đóng cửa sổ PowerShell cũ rồi mở cửa sổ mới.

**Cách dùng các khung lệnh:** sao chép phần bên trong khung, dán vào PowerShell, nhấn Enter và chờ chạy xong. Không sao chép dấu ba gạch ngược. Khi xuất hiện lại dòng bắt đầu bằng `PS ...>`, bạn có thể chạy bước tiếp theo. Nếu có lỗi, xử lý lỗi trước khi tiếp tục.

Kiểm tra Python và Git:

```powershell
python --version
git --version
```

Tải dự án vào thư mục người dùng Windows:

```powershell
cd $env:USERPROFILE
git clone https://github.com/tomyrese/openscad-design-mcp.git
cd openscad-design-mcp
```

Nếu Git báo thư mục đã tồn tại, hãy mở bản đã tải trước đó; không cần xóa thư mục để cài lại.

Tạo môi trường riêng và cài công cụ:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

`.venv` là thư mục chứa Python và thư viện riêng cho dự án. Các lệnh dưới đây dùng trực tiếp Python trong thư mục này, nên bạn không cần chạy lệnh “activate”. Lần cài đầu cần Internet để tải thư viện.

<a id="chay-thu"></a>

## 2. Chạy thử trước khi kết nối AI

Trong PowerShell đang mở tại thư mục dự án, chạy:

```powershell
.\.venv\Scripts\python.exe examples\cube_workflow.py
```

Chương trình tự tạo một khối **20 × 20 × 10 mm**, tạo ảnh xem trước, xuất STL và chạy kiểm tra. Hãy chờ đến khi lệnh kết thúc. Kết quả thành công có trường `"success": true`; nhiều dòng dữ liệu trong cửa sổ là bình thường.

Mở thư mục kết quả:

```powershell
explorer .\workspace\projects
```

Mở thư mục dự án vừa tạo, rồi mở thư mục `previews` để xem ảnh PNG. Mỗi lần chạy mẫu sẽ tạo một dự án mới. Nếu bước này lỗi, xem [xử lý sự cố](#go-loi) trước khi cấu hình AI.

<a id="ket-noi"></a>

## 3. Kết nối với ứng dụng AI

Đầu tiên, tạo tệp cấu hình mẫu có **đường dẫn đúng trên máy bạn**:

```powershell
.\.venv\Scripts\python.exe examples\client_configs.py
explorer .\workspace\client-configs
```

Lệnh này chỉ tạo mẫu, chưa thay đổi thiết lập của ứng dụng AI. Mở mẫu bằng Notepad rồi làm theo hướng dẫn tương ứng:

| Bạn đang dùng | Mẫu cần mở | Hướng dẫn |
|---|---|---|
| Antigravity IDE | `antigravity-claude.json` | [Kết nối Antigravity IDE](docs/CLIENTS.md#antigravity-ide) |
| Antigravity CLI | `antigravity-claude.json` | [Kết nối Antigravity CLI](docs/CLIENTS.md#antigravity-cli) |
| Codex app hoặc CLI | `codex.toml` | [Kết nối Codex](docs/CLIENTS.md#codex) |
| OpenCode | `opencode-v1.json` hoặc `opencode-v2.json` | [Chọn phiên bản và kết nối](docs/CLIENTS.md#opencode) |
| Claude Desktop | `antigravity-claude.json` | [Kết nối Claude Desktop](docs/CLIENTS.md#claude) |

Nếu ứng dụng đã có cấu hình, chỉ thêm mục `openscad-design`; đừng thay toàn bộ tệp và làm mất thiết lập cũ. Nếu đổi vị trí thư mục dự án hoặc cài lại Python/OpenSCAD, hãy tạo lại mẫu và cập nhật trong ứng dụng.

Khởi động lại ứng dụng AI, mở cuộc trò chuyện mới và gửi:

> Dùng công cụ openscad-design gọi get_system_status. Cho tôi biết có tìm thấy OpenSCAD và có tạo được ảnh PNG hay không. Hãy gọi công cụ thật, không chỉ hướng dẫn tôi chạy lệnh.

**Ứng dụng AI sẽ tự khởi chạy MCP khi cần.** Bạn không cần giữ PowerShell chạy máy chủ mỗi lần sử dụng.

<a id="model-dau-tien"></a>

## 4. Tạo mô hình đầu tiên

Thử gửi yêu cầu này trong ứng dụng AI đã kết nối:

> Tạo một hộp chữ nhật không nắp, kích thước bên ngoài 60 × 40 × 25 mm, thành và đáy dày 2 mm. Dùng openscad-design, tạo ảnh từ 6 góc để tôi xem. Kiểm tra kích thước bên ngoài và độ kín của mô hình trước khi xuất STL. Cho tôi đường dẫn ảnh, tệp STL và kết quả kiểm tra.

Xem ảnh rồi yêu cầu chỉnh sửa, ví dụ:

> Giữ chiều dài và chiều rộng, tăng chiều cao lên 30 mm. Lưu thành phiên bản mới, tạo lại ảnh và kiểm tra lại kích thước.

Để kết quả sát nhu cầu, nêu rõ **đơn vị**, **kích thước bên ngoài hay bên trong**, độ dày, lỗ bắt vít và những phần cần lắp với nhau. Nếu chưa biết kích thước, hãy yêu cầu AI hỏi bạn trước khi thiết kế.

Với khung drone, hãy phân biệt đường kính **động cơ** với đường kính **cánh quạt**, và khoảng cách chéo giữa tâm động cơ với kích thước bao ngoài. Những con số này không thể dùng thay cho nhau.

<a id="tep-ket-qua"></a>

## 5. Ảnh và tệp nằm ở đâu?

Mặc định, các mẫu cấu hình lưu dữ liệu tại `workspace` bên trong thư mục dự án. Mỗi thiết kế có thư mục riêng trong `workspace\projects`.

| Thư mục hoặc tệp | Nội dung | Cách sử dụng |
|---|---|---|
| `previews` | Ảnh PNG của mô hình | Nhấp đúp để xem |
| `exports` | Tệp mô hình đã xuất, như STL hoặc 3MF | Mở bằng phần mềm chuẩn bị in của bạn |
| `reports` | Kết quả kiểm tra dạng JSON | Có thể yêu cầu AI giải thích bằng lời |
| `versions` | Các phiên bản đã lưu | Yêu cầu AI khôi phục một phiên bản cũ |

Bạn có thể hỏi AI: “Cho tôi đường dẫn đầy đủ của ảnh và STL mới nhất”. Sao lưu cả thư mục `workspace` nếu muốn giữ thiết kế và lịch sử. Khi xóa dự án bằng công cụ, dữ liệu được chuyển sang `workspace\trash`.

STL/3MF chưa phải lệnh chạy máy in. Bạn cần mở tệp trong phần mềm *slicer* của máy in, chọn vật liệu và thông số in, xem trước các lớp rồi mới gửi sang máy in.

<a id="go-loi"></a>

## Khi gặp lỗi

| Hiện tượng | Cách xử lý |
|---|---|
| Không nhận lệnh `python` hoặc `git` | Kiểm tra đã cài phần mềm, mở PowerShell mới rồi thử lại |
| Không tìm thấy `.venv\Scripts\python.exe` | Mở đúng thư mục dự án; nếu chưa có `.venv`, làm lại bước tạo môi trường |
| `No module named openscad_design_mcp` | Chạy lại `.\.venv\Scripts\python.exe -m pip install -e .` tại thư mục dự án |
| `OpenSCAD not found` | Cài OpenSCAD hoặc chỉ rõ đường dẫn như ví dụ bên dưới |
| Chạy máy chủ nhưng không thấy cửa sổ nào | Bình thường: MCP chờ ứng dụng AI gửi yêu cầu; nhấn Ctrl+C để dừng nếu đã mở thủ công |
| AI không thấy công cụ | Kiểm tra đúng tệp cấu hình của ứng dụng, lưu tệp, khởi động lại và thử `get_system_status` |
| Báo lỗi JSON hoặc TOML | Dùng mẫu được tạo sẵn; kiểm tra dấu phẩy, ngoặc và mục bị trùng khi ghép vào cấu hình cũ |
| Xuất được STL nhưng ảnh PNG lỗi | Gọi `get_system_status` để xem lỗi tạo ảnh; kiểm tra OpenSCAD và trình điều khiển đồ họa |
| `version_conflict` | Yêu cầu AI đọc lại dự án và cập nhật dựa trên phiên bản hiện tại |
| `timeout` | Thử mô hình đơn giản trước; giảm độ chi tiết và số góc ảnh, rồi xem [tài liệu kỹ thuật](docs/TECHNICAL.md) |

Nếu OpenSCAD ở vị trí khác, thay đường dẫn trong lệnh sau bằng vị trí `openscad.exe` thật trên máy:

```powershell
$env:OPENSCAD_PATH = 'C:\Program Files\OpenSCAD\openscad.exe'
.\.venv\Scripts\python.exe examples\cube_workflow.py
.\.venv\Scripts\python.exe examples\client_configs.py
```

Biến trên có hiệu lực trong cửa sổ PowerShell hiện tại. Mẫu cấu hình mới sẽ ghi lại đường dẫn để ứng dụng AI dùng được sau này; nhớ cập nhật mẫu đó vào thiết lập ứng dụng.

<a id="gioi-han"></a>

## Hiểu đúng kết quả kiểm tra

“Hoàn thiện” nghĩa là mô hình đã vượt qua các bước kiểm tra được yêu cầu, không bảo đảm mọi máy in đều in được. Kiểm tra hiện tại không chứng nhận đầy đủ độ dày thành, vùng cần chống đỡ, độ bền hay dung sai lắp ghép. Hãy xem ảnh, kiểm tra kích thước và xem trước trong slicer trước khi in.

OpenSCAD chạy trên máy bạn. Công cụ có giới hạn đường dẫn và chặn một số thao tác đọc tệp trong mã mô hình, nhưng không phải môi trường cách ly ở cấp hệ điều hành: chỉ chạy mã từ nguồn bạn tin cậy. Ứng dụng AI có thể gửi nội dung hoặc kết quả công cụ đến nhà cung cấp AI tùy thiết lập của ứng dụng.

## Tìm hiểu thêm

- [Hướng dẫn chi tiết từng ứng dụng AI](docs/CLIENTS.md).
- [17 công cụ, cấu hình nâng cao và lệnh kiểm thử](docs/TECHNICAL.md).
- [Kết quả đo hiệu năng và kiểm thử sau tối ưu](PERFORMANCE.md).
- [Báo cáo kiểm chứng trước lượt tối ưu](VERIFICATION.md).
- [Logo và mô tả thiết kế](docs/BRANDING.md).
