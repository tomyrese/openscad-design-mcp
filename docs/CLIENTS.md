# Kết nối ứng dụng AI

[← Trở về hướng dẫn bắt đầu](../README.md)

Hướng dẫn này dùng Windows và Python cài trực tiếp trên Windows. Nếu ứng dụng chạy trong WSL, container hoặc máy khác, cần cài dự án và tạo cấu hình trong môi trường đó; đường dẫn Windows không dùng thay thế được.

## Chuẩn bị mẫu đúng đường dẫn

Mở PowerShell tại thư mục dự án và chạy:

```powershell
.\.venv\Scripts\python.exe examples\client_configs.py
explorer .\workspace\client-configs
```

Nhấp chuột phải vào mẫu cần dùng, chọn **Open with → Notepad**. Mẫu đã chứa đường dẫn Python, OpenSCAD và thư mục lưu thiết kế của máy bạn.

Nếu chưa có cấu hình, dùng toàn bộ nội dung mẫu. Nếu đã có cấu hình, sao lưu tệp cũ rồi chỉ ghép mục `openscad-design` vào nhóm tương ứng. Không tạo hai nhóm cùng tên. Các tệp JSON cần dấu phẩy giữa những mục đứng cạnh nhau; không thêm dấu phẩy sau mục cuối. Khi nhờ người khác hỗ trợ, không gửi mật khẩu hoặc khóa API trong cấu hình.

<a id="antigravity-ide"></a>

## Antigravity IDE

1. Trong khung trò chuyện của IDE, chọn **… → MCP Servers → Manage MCP Servers → View raw config**.
2. Trong tệp ứng dụng vừa mở, thêm mục `openscad-design` từ mẫu `antigravity-claude.json` vào nhóm `mcpServers`.
3. Lưu tệp, làm mới danh sách MCP hoặc khởi động lại IDE.
4. Mở cuộc trò chuyện mới và thử yêu cầu ở cuối trang.

Vị trí cấu hình hiện được tài liệu ghi là `%USERPROFILE%\.gemini\config\mcp_config.json`, hoặc `.agents\mcp_config.json` trong dự án. Hãy ưu tiên tệp được mở bởi giao diện nếu bản ứng dụng của bạn dùng vị trí khác. [Nguồn: Antigravity MCP](https://www.antigravity.google/docs/mcp).

<a id="antigravity-cli"></a>

## Antigravity CLI

CLI là ứng dụng chạy trong cửa sổ dòng lệnh. Nếu chưa quen, bạn có thể chọn IDE ở trên. Cài và đăng nhập CLI theo [hướng dẫn chính thức](https://www.antigravity.google/docs/cli/install/).

1. Nhấn **Windows + R**, nhập `%USERPROFILE%\.gemini\config`, rồi Enter. Nếu chưa có thư mục, tạo các thư mục `.gemini` và `config` trong thư mục người dùng.
2. Mở hoặc tạo `mcp_config.json`. Ghép mục `openscad-design` từ mẫu `antigravity-claude.json` vào nhóm `mcpServers`, rồi lưu.
3. Chạy `agy` trong PowerShell.
4. Trong giao diện trò chuyện CLI, nhập `/mcp` để xem trạng thái và tải lại cấu hình.

Có thể dùng `.agents\mcp_config.json` trong dự án nếu chỉ muốn cấu hình cho dự án đó. [Nguồn: cấu hình MCP cho Antigravity CLI](https://www.antigravity.google/docs/mcp#antigravity-cli).

<a id="codex"></a>

## Codex app và Codex CLI

1. Nhấn **Windows + R**, nhập `%USERPROFILE%\.codex`, rồi Enter.
2. Mở `config.toml` bằng Notepad. Nếu chưa có, tạo tệp đúng tên; tránh lưu thành `config.toml.txt`.
3. Sao chép hai nhóm trong mẫu `codex.toml`: `[mcp_servers.openscad-design]` và `[mcp_servers.openscad-design.env]` vào tệp này. Nếu đã có nhóm tương ứng, cập nhật nhóm đó, tránh thêm bản trùng.
4. Lưu tệp và khởi động lại Codex.

Nếu dùng CLI, chạy `codex mcp list` để xem máy chủ đã khai báo; nhập `/mcp` trong phiên trò chuyện để kiểm tra kết nối. Máy chủ cục bộ này không cần đăng nhập OAuth riêng. Mẫu đặt thời gian chờ công cụ tối đa 1.500 giây cho mô hình phức tạp; đây không phải thời gian mỗi lệnh thường mất. [Nguồn: MCP trong Codex](https://developers.openai.com/codex/mcp).

<a id="opencode"></a>

## OpenCode

Cài ứng dụng theo [hướng dẫn OpenCode](https://opencode.ai/docs/). Trong giao diện trò chuyện, dùng `/connect` nếu cần kết nối nhà cung cấp AI.

Kiểm tra phiên bản tại PowerShell:

```powershell
opencode --version
```

| Phiên bản đang dùng | Mẫu | Nhóm chứa máy chủ |
|---|---|---|
| 1.x | `opencode-v1.json` | `mcp` |
| 2.x | `opencode-v2.json` | `mcp.servers` |

1. Mở hoặc tạo `opencode.json` trong thư mục dự án bạn sẽ mở bằng OpenCode.
2. Dùng mẫu đúng phiên bản. Nếu tệp đã có cấu hình khác, chỉ ghép mục máy chủ vào nhóm trong bảng.
3. Lưu rồi mở lại OpenCode tại thư mục đó.
4. Thử yêu cầu kiểm tra kết nối ở cuối trang.

Cấu hình dùng chung có thể đặt tại `%USERPROFILE%\.config\opencode\opencode.json`. Nếu PowerShell chặn tệp `opencode.ps1`, thử gọi `opencode.cmd` thay cho `opencode`; không cần đổi chính sách bảo mật toàn máy chỉ để chạy lệnh.

Mẫu v2 tắt `codemode` cho máy chủ này để cung cấp công cụ trực tiếp. Cấu trúc hai phiên bản khác nhau, không ghép cả hai mẫu. [Nguồn v1](https://opencode.ai/docs/mcp-servers/), [nguồn v2](https://opencode.ai/v2/docs/mcp-servers).

<a id="claude"></a>

## Claude Desktop

1. Nhấn **Windows + R**, nhập `%APPDATA%\Claude`, rồi Enter.
2. Mở hoặc tạo `claude_desktop_config.json` bằng Notepad.
3. Ghép mục `openscad-design` từ mẫu `antigravity-claude.json` vào nhóm `mcpServers`, rồi lưu.
4. Thoát hẳn Claude Desktop và mở lại, sau đó thử trong cuộc trò chuyện mới.

Khi tạo tệp bằng Notepad, chọn **Save as type: All files** để tránh đuôi `.txt`. Bạn cũng có thể mở cấu hình từ mục dành cho nhà phát triển trong thiết lập Claude Desktop.

## Biết đã kết nối thành công bằng cách nào?

Gửi yêu cầu:

> Dùng openscad-design gọi get_system_status. Báo lại kết quả tìm OpenSCAD và thử tạo PNG. Hãy gọi công cụ thật.

Kết quả công cụ thành công cần có `success: true`; khả năng tạo ảnh được báo qua `render_available`. Nếu ảnh chưa khả dụng, xem lỗi chi tiết trước khi tạo mô hình phức tạp.

Sau đó quay về [tạo mô hình đầu tiên](../README.md#model-dau-tien). Ứng dụng tự chạy máy chủ khi kết nối; không cần mở thêm một PowerShell chạy MCP.

Các hướng dẫn cấu hình được đối chiếu tài liệu ngày 05/09/2026. Kiểm tra cục bộ của dự án không thay thế kiểm thử giao diện trên mọi phiên bản ứng dụng AI.
