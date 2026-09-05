# OpenSCAD Design MCP

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![MCP Protocol](https://img.shields.io/badge/MCP-stdio-green.svg)](https://modelcontextprotocol.io/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-lightgrey.svg)](https://www.microsoft.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**OpenSCAD Design MCP** là Model Context Protocol (MCP) server hiệu năng cao dành cho Windows, cung cấp cho các AI Assistant (Antigravity IDE/CLI, Claude Desktop, Cursor, Codex, OpenCode...) khả năng thiết kế 3D, kết xuất ảnh đa góc nhìn song song siêu tốc, quản lý phiên bản snapshot bất biến và kiểm định hình học (mesh/kích thước/khả năng in 3D).

---

## 📑 Mục lục
- [Tính năng nổi bật](#tính-năng-nổi-bật)
- [Bắt đầu nhanh (3 phút)](#bắt-đầu-nhanh-3-phút)
- [Cấu hình AI Client](#cấu-hình-ai-client)
  - [1. Antigravity IDE](#1-antigravity-ide)
  - [2. Antigravity CLI](#2-antigravity-cli)
  - [3. Claude Desktop](#3-claude-desktop)
  - [4. Cursor / VS Code](#4-cursor-vs-code)
  - [5. OpenAI Codex](#5-openai-codex)
  - [6. OpenCode](#6-opencode)
- [Quy trình thiết kế mô hình chuẩn](#quy-trình-thiết-kế-mô-hình-chuẩn)
- [Bảng tra cứu 17 MCP Tools](#bảng-tra-cứu-17-mcp-tools)
- [Kinh nghiệm tối ưu hóa mã OpenSCAD](#kinh-nghiệm-tối-ưu-hóa-mã-openscad)
- [Cấu hình biến môi trường](#cấu-hình-biến-môi-trường)
- [Xử lý sự cố thường gặp (FAQ)](#xử-lý-sự-cố-thường-gặp-faq)

---

## 🚀 Tính năng nổi bật

- ⚡ **Render Preview Song Song Siêu Tốc**: Xuất 6 góc nhìn camera đồng thời qua OpenCSG preview với đa luồng (`ThreadPoolExecutor`), render hoàn tất chỉ trong **~0.5 giây** (nhanh hơn 100x so với render CGAL truyền thống).
- 🛡️ **Quản Lý Phiên Bản Bất Biến**: Lưu trữ lịch sử snapshot từng lần sửa đổi với mã băm SHA-256, hỗ trợ rollback và kiểm soát xung đột qua `expected_version`.
- 🔍 **Kiểm Định Hình Học & Khả Năng In 3D**: Tự động đo đạc thể tích, diện tích bề mặt, bounding box, kiểm tra độ kín nước (watertight), phát hiện lỗi non-manifold, mặt trùng lặp hoặc lật ngược mặt.
- 🗄️ **Mesh Inspection Cache**: Tự động ghi nhớ kết quả kiểm tra hình học của phiên bản hiện tại, phản hồi tức thì các truy vấn đo đạc kích thước mà không phải xuất lại STL.
- 📦 **Đa Dạng Định Dạng Xuất Bản**: Xuất chuẩn 3D (`STL`, `3MF`, `OFF`, `AMF`) và 2D CAD (`DXF`, `SVG`).
- 🔒 **An Toàn & Độc Lập**: Hoạt động hoàn toàn qua chuẩn giao tiếp `stdio`, không yêu cầu API key, không mở port mạng, quản lý file trong workspace cô lập.

---

## ⚡ Bắt đầu nhanh (3 phút)

### Bước 1: Yêu cầu hệ thống
1. **Python 3.11+**: Tải từ [python.org](https://www.python.org/downloads/windows/) (Nhớ tích chọn *Add Python to PATH* khi cài đặt).
2. **OpenSCAD**: Tải từ [openscad.org](https://openscad.org/downloads.html) (Khuyến nghị cài đặt tại `C:\Program Files\OpenSCAD\openscad.exe`).
3. **Git for Windows**: Tải từ [git-scm.com](https://git-scm.com/download/win).

### Bước 2: Cài đặt OpenSCAD Design MCP
Mở **PowerShell** và chạy các lệnh sau:

```powershell
# 1. Clone repository
New-Item -ItemType Directory -Force D:\Code | Out-Null
cd D:\Code
git clone https://github.com/tomyrese/openscad-design-mcp.git
cd openscad-design-mcp

# 2. Tạo môi trường ảo và cài đặt dependencies
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

# 3. Đặt biến môi trường hệ thống cho OpenSCAD
[Environment]::SetEnvironmentVariable('OPENSCAD_PATH', 'C:\Program Files\OpenSCAD\openscad.exe', 'User')
```

### Bước 3: Kiểm tra hoạt động
Chạy script kiểm thử workflow hoàn chỉnh (tạo khối hộp, render 6 góc nhìn, kiểm tra mesh và xuất STL):

```powershell
.\.venv\Scripts\python.exe examples\cube_workflow.py
```
> Nếu output trả về JSON có `"finalized": true` và thời gian chạy ~2s, hệ thống đã sẵn sàng 100%!

---

## 🤖 Cấu hình AI Client

### 1. Antigravity IDE
Trong Antigravity IDE:
1. Mở menu panel Agent: **… → MCP Servers → Manage MCP Servers → View raw config**.
2. Thêm cấu hình sau vào mục `mcpServers`:

```json
{
  "mcpServers": {
    "openscad-design": {
      "command": "D:\\Code\\openscad-design-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "openscad_design_mcp"],
      "env": {
        "OPENSCAD_PATH": "C:\\Program Files\\OpenSCAD\\openscad.exe",
        "OPENSCAD_MCP_WORKSPACE": "D:\\Code\\openscad-design-mcp\\workspace"
      }
    }
  }
}
```
3. Lưu file và reload lại IDE.

---

### 2. Antigravity CLI
Chạy lệnh đăng ký MCP server trực tiếp:

```powershell
agy mcp add --env "OPENSCAD_PATH=C:\Program Files\OpenSCAD\openscad.exe" --env "OPENSCAD_MCP_WORKSPACE=D:\Code\openscad-design-mcp\workspace" openscad-design "D:\Code\openscad-design-mcp\.venv\Scripts\python.exe" -m openscad_design_mcp
```
Kiểm tra danh sách server với `agy mcp list`.

---

### 3. Claude Desktop
Mở tệp cấu hình tại `%APPDATA%\Claude\claude_desktop_config.json` và thêm:

```json
{
  "mcpServers": {
    "openscad-design": {
      "command": "D:\\Code\\openscad-design-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "openscad_design_mcp"],
      "env": {
        "OPENSCAD_PATH": "C:\\Program Files\\OpenSCAD\\openscad.exe",
        "OPENSCAD_MCP_WORKSPACE": "D:\\Code\\openscad-design-mcp\\workspace"
      }
    }
  }
}
```

---

<a id="4-cursor-vs-code"></a>
### 4. Cursor / VS Code
*(Hỗ trợ Cursor và các Extension trên VS Code như Cline, Roo Code, Continue)*
Đối với các extension hỗ trợ MCP trên VS Code / Cursor:
1. Mở tệp cài đặt MCP của extension (ví dụ: `cline_mcp_settings.json` hoặc cấu hình MCP trong settings).
2. Thêm:

```json
{
  "mcpServers": {
    "openscad-design": {
      "command": "D:\\Code\\openscad-design-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "openscad_design_mcp"],
      "env": {
        "OPENSCAD_PATH": "C:\\Program Files\\OpenSCAD\\openscad.exe",
        "OPENSCAD_MCP_WORKSPACE": "D:\\Code\\openscad-design-mcp\\workspace"
      }
    }
  }
}
```

---

### 5. OpenAI Codex
Thêm vào `%USERPROFILE%\.codex\config.toml`:

```toml
[mcp_servers.openscad-design]
command = 'D:\Code\openscad-design-mcp\.venv\Scripts\python.exe'
args = ['-m', 'openscad_design_mcp']
startup_timeout_sec = 30
tool_timeout_sec = 600

[mcp_servers.openscad-design.env]
OPENSCAD_PATH = 'C:\Program Files\OpenSCAD\openscad.exe'
OPENSCAD_MCP_WORKSPACE = 'D:\Code\openscad-design-mcp\workspace'
```

---

### 6. OpenCode
Thêm vào `opencode.json` (hoặc `%USERPROFILE%\.config\opencode\opencode.json`):

```json
{
  "mcp": {
    "openscad-design": {
      "type": "local",
      "command": [
        "D:\\Code\\openscad-design-mcp\\.venv\\Scripts\\python.exe",
        "-m",
        "openscad_design_mcp"
      ],
      "environment": {
        "OPENSCAD_PATH": "C:\\Program Files\\OpenSCAD\\openscad.exe",
        "OPENSCAD_MCP_WORKSPACE": "D:\\Code\\openscad-design-mcp\\workspace"
      },
      "enabled": true
    }
  }
}
```

---

## 🔄 Quy trình thiết kế mô hình chuẩn

Quy trình khép kín giúp AI Agent và người dùng cộng tác thiết kế mô hình 3D chính xác:

```
                  ┌───────────────────────────────┐
                  │ 1. create_project             │ ──> Khởi tạo & lưu Version 1
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ 2. render_preview_set         │ ──> Render 6 góc nhìn song song (~0.5s)
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ 3. compare_dimensions         │ ──> Kiểm tra kích thước hình học
                  └──────────────┬────────────────┘
                                 │
                   [Chưa đạt yêu cầu?]
                  ┌──────────────┴────────────────┐
                  │                               │
            (Cần chỉnh sửa)                   (Đã chuẩn)
                  │                               │
                  ▼                               ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │ 4. update_model           │   │ 5. finalize_model         │
    │    (tăng expected_version)│   │    (Xuất STL, báo cáo)    │
    └─────────────┬─────────────┘   └─────────────┬─────────────┘
                  │                               │
                  └──────> Quay lại Bước 2        └──────> Hoàn tất!
```

---

## 🛠️ Bảng tra cứu 17 MCP Tools

### 1. Thông tin hệ thống & Môi trường
| Tool | Mô tả | Tham số chính |
|---|---|---|
| `get_system_status` | Kiểm tra phiên bản Python, OpenSCAD, thư viện và thực hiện probe PNG thực tế. | *Không có* |

### 2. Quản lý dự án & Phiên bản
| Tool | Mô tả | Tham số chính |
|---|---|---|
| `create_project` | Tạo dự án mới, lưu snapshot Version 1 và tự động validate code. | `name`, `description`, `requirements`, `initial_scad_code`, `units` |
| `list_projects` | Liệt kê tất cả các dự án trong workspace cùng trạng thái mới nhất. | *Không có* |
| `get_project` | Lấy chi tiết metadata, mã SCAD hiện tại, danh sách exports và báo cáo. | `project_id` |
| `read_model` | Đọc mã nguồn SCAD đã được xác thực checksum của phiên bản hiện tại. | `project_id` |
| `update_model` | Cập nhật mã nguồn SCAD có kiểm soát xung đột phiên bản (`expected_version`). | `project_id`, `scad_code`, `change_summary`, `expected_version` |
| `list_versions` | Xem lịch sử các phiên bản bất biến kèm checksum SHA-256. | `project_id` |
| `restore_version` | Khôi phục một phiên bản lịch sử thành phiên bản mới nhất. | `project_id`, `version`, `expected_version` |
| `delete_project` | Xóa an toàn dự án (chuyển vào thư mục `trash/`). | `project_id`, `confirm_project_id` |

### 3. Kết xuất hình ảnh (Rendering)
| Tool | Mô tả | Tham số chính |
|---|---|---|
| `render_preview` | Render ảnh PNG độ nét cao theo một góc nhìn hoặc tọa độ camera tùy chỉnh. | `project_id`, `view`, `width`, `height`, `projection`, `colorscheme`, `render_mode` |
| `render_preview_set` | Render đồng thời nhiều góc nhìn (mặc định 6 góc) song song đa luồng. | `project_id`, `views`, `width`, `height`, `render_mode` |

### 4. Xuất file & Kiểm định chất lượng (Verification)
| Tool | Mô tả | Tham số chính |
|---|---|---|
| `validate_scad` | Biên dịch thử nghiệm để kiểm tra lỗi cú pháp và hình học rỗng. | `project_id` |
| `export_model` | Xuất mô hình ra tệp `stl`, `3mf`, `off`, `amf`, `dxf`, `svg`. | `project_id`, `output_format` |
| `inspect_mesh` | Phân tích cấu trúc lưới: thể tích, diện tích, độ kín (watertight), số đỉnh, số mặt. | `project_id` |
| `compare_dimensions` | So sánh kích thước thực tế với kích thước yêu cầu theo dung sai (mm / %). | `project_id`, `expected_dimensions`, `tolerance`, `percent_tolerance` |
| `check_printability` | Kiểm tra toàn diện khả năng in 3D (kín nước, nằm trong bàn in, đơn khối). | `project_id`, `build_volume`, `require_watertight` |
| `finalize_model` | Chạy toàn bộ quy trình kiểm định và khóa hoàn thiện mô hình. | `project_id`, `output_format`, `expected_dimensions`, `build_volume`, `require_watertight` |

---

## 💡 Kinh nghiệm tối ưu hóa mã OpenSCAD

### 1. Tận dụng biến `$preview` để tăng tốc độ phản hồi
Trong OpenSCAD, biến built-in `$preview` sẽ có giá trị `true` khi xem trước (Fast OpenCSG) và `false` khi xuất file (CGAL Render). Hãy áp dụng:

```openscad
// Mịn vừa phải khi preview (~0.2s), siêu mịn khi xuất STL
$fn = $preview ? 24 : 64;
```

### 2. Thiết kế mô hình kín nước (Watertight Solid)
- **Luôn dùng phép gộp/trừ rõ ràng**: Đảm bảo các khối giao nhau chồng lấn nhẹ một khoảng nhỏ (ví dụ `0.01mm`) khi thực hiện `difference()` để tránh hiện tượng mặt trùng (Z-fighting hoặc 0-thickness walls).
- **Tránh các cạnh Non-Manifold**: Không để hai khối giao nhau chỉ chạm nhau tại một điểm hoặc một cạnh duy nhất.

### 3. Đặt gốc tọa độ thông minh
- Khuyến nghị sử dụng `center = true` cho thân chính hoặc đặt tâm đáy tại gốc `[0, 0, 0]` để camera tự động canh khung (`autocenter`, `viewall`) hoàn hảo nhất.

---

## ⚙️ Cấu hình biến môi trường

| Tên biến | Mặc định | Ý nghĩa |
|---|---|---|
| `OPENSCAD_PATH` | Tự động dò tìm | Đường dẫn đến tệp `openscad.exe`. |
| `OPENSCAD_MCP_WORKSPACE` | `./workspace` | Thư mục lưu trữ dự án, exports, preview và reports. |
| `OPENSCAD_MCP_VALIDATE_TIMEOUT` | `30.0` | Timeout tối đa khi validate mã SCAD (giây). |
| `OPENSCAD_MCP_PREVIEW_TIMEOUT` | `60.0` | Timeout tối đa cho mỗi tác vụ render ảnh (giây). |
| `OPENSCAD_MCP_EXPORT_TIMEOUT` | `180.0` | Timeout tối đa khi xuất file STL/3MF (giây). |
| `OPENSCAD_MCP_INSPECT_TIMEOUT` | `60.0` | Timeout tối đa khi phân tích lưới hình học (giây). |
| `OPENSCAD_MCP_LOCK_TIMEOUT` | `10.0` | Timeout chờ khóa đồng bộ workspace (giây). |
| `OPENSCAD_MCP_MAX_CODE_BYTES` | `2097152` | Giới hạn độ dài mã nguồn SCAD (2 MB). |

---

## ❓ Xử lý sự cố thường gặp (FAQ)

> [!TIP]
> **Client báo không tìm thấy OpenSCAD?**
> Hãy kiểm tra đường dẫn `OPENSCAD_PATH` trong biến môi trường hoặc cấu hình JSON. Đảm bảo đường dẫn Windows sử dụng dấu `\\` trong JSON (ví dụ: `"C:\\Program Files\\OpenSCAD\\openscad.exe"`).

> [!NOTE]
> **Tại sao không dùng được lệnh `include <...>` hay `use <...>`?**
> Để đảm bảo an toàn sandbox và tính toàn vẹn phiên bản, OpenSCAD MCP chặn các lệnh nạp tệp bên ngoài. Tất cả module cần thiết nên được định nghĩa trực tiếp trong mã SCAD của dự án.

> [!IMPORTANT]
> **Lỗi `version_conflict` khi gọi `update_model`?**
> Khi bạn hoặc AI muốn cập nhật mã, tham số `expected_version` phải khớp chính xác với `current_version` hiện tại của dự án. Nếu có xung đột, hãy gọi `read_model` để lấy phiên bản mới nhất trước khi cập nhật.

---

## 📄 Bản quyền
Dự án được phân phối theo giấy phép [MIT License](LICENSE).
