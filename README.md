# openscad-design-mcp

MCP Server Python cho Windows 10/11, giúp AI quản lý mã OpenSCAD, render, xuất mesh,
đo kích thước và kiểm tra mô hình 3D. Transport duy nhất của chương trình là `stdio`.
MCP quản lý công cụ và dữ liệu; AI client quyết định sửa mã. Không có vòng lặp AI nội bộ,
không cần API key, không dùng Docker.

## Bắt đầu từ đâu?

1. [Cài server và OpenSCAD](#cài-đặt-trên-windows).
2. [Kiểm tra bằng CLI/PowerShell](#cli-và-powershell) trước khi nối AI client.
3. Chọn [Antigravity IDE](#antigravity-ide), [Antigravity CLI](#antigravity-cli),
   [Codex](#cấu-hình-codex), [OpenCode](#opencode) hoặc [Claude Desktop](#cấu-hình-claude-desktop).
4. Gọi `get_system_status`, rồi thử [quy trình cube](#quy-trình-cube).

Server chạy local; mỗi client tự khởi động tiến trình stdio. Không cần mở server trong
một terminal riêng khi đã cấu hình client, không có cổng HTTP để điền vào trường URL.
Tài khoản/model của AI client được cấu hình trong client; server này không cần khóa AI.

Các ví dụ dùng thư mục `D:\Code\openscad-design-mcp`. Nếu dùng thư mục khác, thay
**mọi** đường dẫn Python/workspace tương ứng. JSON dùng `\\` cho dấu phân cách Windows;
TOML dùng chuỗi nháy đơn để giữ nguyên `\`. Không ghi `%USERPROFILE%`, `~` hoặc
`$env:...` vào giá trị đường dẫn JSON rồi giả định client sẽ tự mở rộng.

## Cài đặt trên Windows

Cài [Git for Windows](https://git-scm.com/download/win), Python 3.11 trở lên từ
[python.org](https://www.python.org/downloads/windows/) và
[OpenSCAD](https://openscad.org/downloads.html). Chọn thêm Python vào PATH, mở
PowerShell mới và kiểm tra `git --version`, `python --version`.

Clone một lần; bỏ qua bước clone nếu đã có thư mục dự án:

```powershell
New-Item -ItemType Directory -Force D:\Code | Out-Null
cd D:\Code
git clone https://github.com/tomyrese/openscad-design-mcp.git
cd openscad-design-mcp
```

Cài server trong môi trường riêng:

```powershell
cd D:\Code\openscad-design-mcp
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
$env:OPENSCAD_PATH = 'C:\Program Files\OpenSCAD\openscad.exe'
$env:OPENSCAD_MCP_WORKSPACE = 'D:\Code\openscad-design-mcp\workspace'
& $env:OPENSCAD_PATH --version
.\.venv\Scripts\python.exe -m pip check
```

Không bắt buộc activate môi trường. Nếu muốn chạy kiểm thử và có manifold tùy chọn:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev,manifold]'
```

Log đi stderr; không thêm `print()` vào server.
`manifold3d` là tùy chọn; nếu không có wheel phù hợp, cài `.[dev]` vẫn phân tích được mesh.
Trimesh là bộ phân tích chính; không tự sửa mesh bằng manifold vì có thể che lỗi mô hình.

Tìm OpenSCAD theo thứ tự: `OPENSCAD_PATH`, `openscad`/`openscad.exe` trong PATH,
`C:\Program Files\OpenSCAD\openscad.exe`, `C:\Program Files (x86)\OpenSCAD\openscad.exe`.
Giá trị môi trường chỉ là đường dẫn executable, không thêm dấu nháy bên trong giá trị.
Để lưu biến môi trường cho các phiên mới:

```powershell
[Environment]::SetEnvironmentVariable('OPENSCAD_PATH', 'C:\Program Files\OpenSCAD\openscad.exe', 'User')
```

Khởi động lại ứng dụng client sau khi sửa biến môi trường. Đường dẫn Unicode và khoảng trắng
được truyền bằng danh sách đối số subprocess, không thông qua shell.
Để tương thích OpenSCAD 2021.01 trên Windows, tên input/output truyền cho CLI là
đường dẫn tương đối do server tạo, với working directory đặt bằng API Unicode của Python.

## CLI và PowerShell

Đây là cách kiểm tra server không cần tài khoản AI. Tại thư mục dự án, sau khi đặt hai
biến môi trường ở trên, chạy module hoặc executable đã được pip tạo:

```powershell
.\.venv\Scripts\python.exe -m openscad_design_mcp
```

Hoặc:

```powershell
.\.venv\Scripts\openscad-design-mcp.exe
```

Chương trình chờ JSON-RPC qua stdin; không gõ câu hỏi tự nhiên vào đây. Dùng Ctrl+C
để dừng. Để thực sự gọi công cụ, tạo file `mcp.local.json` tại thư mục dự án với nội
dung JSON mẫu trong phần Antigravity IDE bên dưới, rồi dùng FastMCP CLI đã cài cùng server:

```powershell
.\.venv\Scripts\fastmcp.exe list mcp.local.json --json --input-schema --output-schema
.\.venv\Scripts\fastmcp.exe call mcp.local.json get_system_status --json --timeout 120
.\.venv\Scripts\fastmcp.exe call mcp.local.json list_projects --json
```

`list` phải thấy 17 tools; status cần `success=true`, `render_available=true` và phiên
bản OpenSCAD. FastMCP 4 trả JSON status trong `structured_content` của kết quả CLI;
một số MCP client dùng tên trường protocol `structuredContent`.
Lệnh `list_projects` không tạo model. Để thử tạo cube, render, STL và finalize thật:

```powershell
.\.venv\Scripts\python.exe examples\cube_workflow.py
```

Script tạo một dự án mới mỗi lần chạy, in báo cáo JSON và trả exit code 1 nếu finalize
không đạt. Các ảnh, STL và báo cáo được lưu trong `workspace/projects/<project-id>/`.
`--timeout` của FastMCP CLI là timeout kết nối, không thay thế giới hạn subprocess của server.

## Antigravity IDE

Cài và đăng nhập Antigravity IDE từ [trang chính thức](https://antigravity.google/),
mở thư mục model/dự án muốn làm việc. Theo
[hướng dẫn MCP của Google](https://www.antigravity.google/docs/mcp):

1. Trong panel Agent, mở **… → MCP Servers → Manage MCP Servers → View raw config**.
2. Ghép mục `openscad-design` dưới `mcpServers`; giữ các server đã có.
3. Lưu file, refresh danh sách MCP hoặc mở lại IDE, bật server nếu đang disabled.
4. Trong Agent, yêu cầu: “Dùng MCP openscad-design gọi get_system_status và báo khả năng render.”

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

Tài liệu Google hiện chỉ ra file global `%USERPROFILE%\.gemini\config\mcp_config.json`
hoặc file theo dự án `.agents/mcp_config.json`. Nếu bản IDE đang dùng mở file khác khi
bấm **View raw config**, chỉnh chính file IDE mở; không tạo thêm cấu hình trùng tên.
JSON trên cũng dùng được làm `mcp.local.json` để kiểm tra FastMCP CLI.

Không điền `serverUrl` vì đây là server stdio. Không cần OAuth cho server này.
Nếu client ngắt một finalize dài, chạy validate/render từng góc/export/inspect riêng
để đọc lỗi, giảm độ phức tạp model; chỉnh timeout client theo phiên bản đang dùng nếu
có hỗ trợ. Không coi việc tăng timeout server là đã tăng timeout IDE.

## Antigravity CLI

Cài Antigravity CLI bằng lệnh PowerShell trong
[hướng dẫn cài đặt chính thức](https://www.antigravity.google/docs/cli/install/):

```powershell
irm https://antigravity.google/cli/install.ps1 | iex
```

Mở PowerShell mới, chạy `agy --help`, rồi `agy` để hoàn tất thiết lập/đăng nhập lần đầu.
Nếu Antigravity đã đăng nhập trên máy, CLI có thể dùng thông tin đăng nhập từ keyring;
nếu chưa, làm theo luồng đăng nhập được client hiển thị. Chấp thuận workspace đang mở
khi bạn tin cậy thư mục đó.
Nếu chưa tìm thấy `agy`, dùng trình cài/thiết lập PATH của Antigravity rồi mở lại terminal.

Bản CLI đã kiểm tra trên máy hỗ trợ lệnh sau; các cờ phải đứng **trước tên server**:

```powershell
agy mcp add --env "OPENSCAD_PATH=C:\Program Files\OpenSCAD\openscad.exe" --env "OPENSCAD_MCP_WORKSPACE=D:\Code\openscad-design-mcp\workspace" openscad-design "D:\Code\openscad-design-mcp\.venv\Scripts\python.exe" -m openscad_design_mcp
agy mcp list
cd D:\Code\openscad-design-mcp
agy
```

Trong phiên tương tác, dùng `/mcp` để xem trạng thái/reload/log, rồi yêu cầu gọi
`get_system_status`. Có thể dùng `agy mcp enable openscad-design` nếu đã tắt server.
Nếu bản CLI không có lệnh `mcp add`, dùng JSON của phần IDE tại global
`%USERPROFILE%\.gemini\config\mcp_config.json` hoặc `<thư mục đang mở>\.agents\mcp_config.json`,
theo [cấu hình Antigravity CLI](https://www.antigravity.google/docs/mcp#antigravity-cli).
Chọn một nơi cấu hình để tránh định nghĩa trùng. Dùng `agy mcp add --help` kiểm tra cú pháp
khi nâng cấp; không dùng các cờ tự bỏ qua quyền để thiết lập MCP.

## Cấu hình Codex

Áp dụng cho Codex app, CLI và IDE extension chạy trên cùng máy/host. Cài client và đăng
nhập trước theo [hướng dẫn Codex](https://developers.openai.com/codex/cli).
Nếu dùng CLI, kiểm tra `codex --version` và `codex mcp --help` trong PowerShell.

Khi đã cài Node.js/npm, có thể cài Codex CLI và bắt đầu đăng nhập:

```powershell
npm install -g @openai/codex
codex
```

Hoàn tất đăng nhập theo hướng dẫn client, rồi dùng cấu hình bên dưới. Nếu PowerShell
chặn script npm, dùng `codex.cmd` nếu bản cài của bạn cung cấp launcher đó.

Thêm đoạn này vào `%USERPROFILE%\.codex\config.toml` (hoặc `.codex/config.toml`
của dự án đã tin cậy). Định dạng được đối chiếu với
[tài liệu MCP chính thức của OpenAI](https://developers.openai.com/codex/mcp)
ngày 05/09/2026. Đổi đường dẫn nếu bạn chuyển dự án:

```toml
[mcp_servers.openscad-design]
command = 'D:\Code\openscad-design-mcp\.venv\Scripts\python.exe'
args = ['-m', 'openscad_design_mcp']
startup_timeout_sec = 30
tool_timeout_sec = 1500

[mcp_servers.openscad-design.env]
OPENSCAD_PATH = 'C:\Program Files\OpenSCAD\openscad.exe'
OPENSCAD_MCP_WORKSPACE = 'D:\Code\openscad-design-mcp\workspace'
```

Timeout client 1500 giây dành cho finalize nhiều góc; mỗi subprocess vẫn có timeout riêng.
Nếu tăng giới hạn server, hãy tăng timeout client tương ứng. Không cần đổi cấu hình Codex
hiện có khác. Khởi động lại client và gọi `get_system_status`.

Có thể đăng ký từ CLI thay cho nhập bảng TOML thủ công:

```powershell
codex mcp add openscad-design --env "OPENSCAD_PATH=C:\Program Files\OpenSCAD\openscad.exe" --env "OPENSCAD_MCP_WORKSPACE=D:\Code\openscad-design-mcp\workspace" -- "D:\Code\openscad-design-mcp\.venv\Scripts\python.exe" -m openscad_design_mcp
codex mcp list
```

Sau khi đăng ký bằng CLI, bổ sung `startup_timeout_sec` và `tool_timeout_sec` vào bảng
`[mcp_servers.openscad-design]` đã được tạo; không thêm bảng thứ hai cùng tên.
Trong Codex CLI, chạy `codex`, dùng `/mcp` để xem kết nối. Trong app/extension,
khởi động lại client hoặc server từ phần quản lý MCP rồi yêu cầu gọi `get_system_status`.
MCP local này không cần `codex mcp login`; tài khoản Codex được đăng nhập riêng.

Các đường dẫn Windows trên dành cho client native Windows. Nếu chạy Codex trong WSL,
hãy cài Python/OpenSCAD/môi trường trong WSL và cấu hình đường dẫn Linux tương ứng;
không sao chép nguyên `D:\...\python.exe` vào môi trường Linux. Xem
[tài liệu Windows/WSL của Codex](https://developers.openai.com/codex/windows).

## OpenCode

### Cài client và chọn phiên bản cấu hình

Cài theo [hướng dẫn Windows của OpenCode](https://opencode.ai/docs/), hoặc khi đã có
Node.js/npm trên Windows, dùng:

```powershell
npm install -g opencode-ai
opencode --version
cd D:\Code\openscad-design-mcp
opencode
```

Trong TUI, dùng `/connect` để thiết lập nhà cung cấp/model của bạn. Đây là xác thực
AI client, không phải xác thực MCP. Thoát client trước khi sửa file, mở lại sau khi lưu.
Nếu PowerShell chặn `opencode.ps1`, dùng `opencode.cmd` với cùng đối số.

Chọn **một** cấu hình bên dưới theo phiên bản. File theo dự án là `opencode.json`
(hoặc `opencode.jsonc`) trong thư mục bạn chạy OpenCode; global là
`%USERPROFILE%\.config\opencode\opencode.json`. Ghép cấu hình vào file hiện có, giữ
provider/model và các MCP khác. Không đặt đồng thời cả mẫu v1 và v2.

### OpenCode 1.x — đã đối chiếu CLI 1.18.25 trên máy

Theo [MCP của OpenCode 1.x](https://opencode.ai/docs/mcp-servers/), tên server nằm trực
tiếp trong `mcp`; `command` là mảng gồm executable và đối số; biến môi trường là
`environment`, không phải `env`:

```json
{
  "$schema": "https://opencode.ai/config.json",
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
      "enabled": true,
      "timeout": 30000
    }
  }
}
```

`timeout` v1 ở đây là 30.000 ms cho việc lấy tool, không cam kết tăng thời gian thực
thi finalize. Khi client ngắt tác vụ dài, kiểm tra giới hạn của phiên bản đang dùng
hoặc chia các bước để chẩn đoán. Kiểm tra kết nối:

```powershell
opencode mcp list
opencode
```

Yêu cầu: “Dùng tool openscad-design_get_system_status, sau đó liệt kê dự án.”
Chấp thuận lời gọi tool nếu client hỏi quyền. `opencode mcp debug` dành cho chẩn đoán
OAuth; server stdio này không cần `mcp auth`.

### OpenCode 2.x

[Tài liệu v2](https://opencode.ai/v2/docs/mcp-servers) chuyển danh sách vào `mcp.servers`,
dùng `disabled` và các timeout tách biệt theo mili giây:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
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
        "disabled": false,
        "codemode": false,
        "timeout": {
          "startup": 30000,
          "catalog": 30000,
          "execution": 1500000
        }
      }
    }
  }
}
```

`codemode=false` hiển thị các tool trực tiếp. Dùng giao diện quản lý MCP của bản v2
để kiểm tra trạng thái, rồi gọi `get_system_status`. Nếu báo unknown field `servers`,
kiểm tra `opencode --version` và dùng cấu hình v1 nếu đang chạy 1.x.

## Cấu hình Claude Desktop

Ghép mục `openscad-design` vào `mcpServers` trong
`%APPDATA%\Claude\claude_desktop_config.json`, giữ các server đang có:

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

## Công cụ và phản hồi

| Công cụ | Chức năng |
|---|---|
| `get_system_status` | Python, executable, version, flags/format phát hiện từ `--help`, thư viện và probe PNG thật |
| `create_project` | Tạo UUID, metadata và snapshot đầu tiên; chạy validate, vẫn lưu dự án khi model sai |
| `list_projects`, `get_project`, `read_model` | Liệt kê, đọc metadata/code, exports và báo cáo gần nhất |
| `update_model` | Kiểm tra `expected_version`, lưu snapshot mới, hủy trạng thái finalize cũ |
| `validate_scad` | Compile STL và kiểm tra mesh không rỗng; phân loại errors/warnings từ CLI |
| `render_preview` | PNG kiểm tra bằng Pillow, view/camera/projection/colorscheme, chọn version |
| `render_preview_set` | Mặc định sáu góc; giữ kết quả thành công khi một góc thất bại |
| `export_model` | STL, 3MF, OFF, AMF, DXF, SVG nếu executable quảng bá hỗ trợ |
| `inspect_mesh` | Dùng last_export STL/3MF cùng version, kiểm checksum; nếu thiếu xuất STL tạm |
| `compare_dimensions` | So sánh X/Y/Z; `null` bỏ qua trục; dung sai tuyệt đối và phần trăm |
| `check_printability` | Kiểm tra mesh kín, thành phần rời, lỗi tam giác, thể tích và bàn in |
| `finalize_model` | Validate → render → export → inspect → dimensions → printability → báo cáo JSON |
| `list_versions`, `restore_version` | Lịch sử SHA-256; khôi phục thành phiên bản mới với `expected_version` |
| `delete_project` | Yêu cầu hai ID trùng nhau, chuyển vào trash và trả đường dẫn khôi phục |

Các tool trả Pydantic output schema và structured content theo
[API FastMCP](https://gofastmcp.com/servers/tools). Dạng phản hồi:

```json
{
  "success": true,
  "tool": "read_model",
  "project_id": "0123456789abcdef0123456789abcdef",
  "data": {"scad_code": "cube(10);", "version": 1},
  "warnings": [],
  "errors": [],
  "artifacts": [],
  "duration_ms": 1
}
```

`artifacts` chứa đường dẫn tuyệt đối, SHA-256, version, kích thước byte và loại file.
Client cần quyền đọc tệp local để xem PNG; server không tự upload ảnh hay trả base64.
Lỗi nghiệp vụ nằm trong envelope, không trả traceback. Đầu vào không khớp JSON schema
bị FastMCP từ chối ở tầng protocol trước khi chạy tool, theo chuẩn lỗi MCP.
`create_project.success` biểu thị đã tạo/lưu thành công; kiểm thêm `data.validation.success`.

## Quy trình cube

AI gọi lần lượt với các tham số dưới đây. Thay `PROJECT_ID` bằng ID thực nhận được:

```json
{
  "name": "Cube 20 × 20 × 10",
  "description": "Mẫu kiểm tra",
  "requirements": "Kín, một component, kích thước 20 × 20 × 10 mm",
  "initial_scad_code": "cube([20, 20, 10], center = true);",
  "units": "mm"
}
```

1. `create_project` với object trên.
2. `validate_scad` với `{"project_id":"PROJECT_ID"}`.
3. `render_preview_set` với `{"project_id":"PROJECT_ID"}`.
4. `export_model` với `{"project_id":"PROJECT_ID","output_format":"stl"}`.
5. `inspect_mesh` với `{"project_id":"PROJECT_ID"}`.
6. `finalize_model` với:

```json
{
  "project_id": "PROJECT_ID",
  "output_format": "stl",
  "expected_dimensions": {"x": 20, "y": 20, "z": 10},
  "tolerance": 0.1,
  "build_volume": {"x": 220, "y": 220, "z": 250},
  "require_watertight": true,
  "render_views": ["isometric", "front", "right", "back", "left", "top"]
}
```

`data.finalized` chỉ true nếu mọi bước bắt buộc và mọi điều kiện kiểm tra đạt.
Khi false, dùng `suggested_actions` và diagnostics để sửa:

```json
{
  "project_id": "PROJECT_ID",
  "scad_code": "cube([20, 20, 10], center = true);",
  "change_summary": "Sửa kích thước",
  "expected_version": 1
}
```

Gọi `update_model`, rồi kiểm tra lại. Chạy toàn bộ workflow qua MCP stdio thật bằng:

```powershell
.\.venv\Scripts\python.exe examples\cube_workflow.py
```

## Camera, đơn vị và điều kiện hoàn thành

Named views: isometric, front, back, left, right, top, bottom. Front nhìn từ -Y,
right từ +X, top từ +Z. Mặc định orthographic, Cornfield, 800 × 600.
View `custom` nhận `camera` là 6 số eye/center hoặc 7 số translate/rotation/distance;
không tự autocenter/viewall custom. Ví dụ `camera=[80,-80,60,0,0,0]`.
Set/finalize chỉ nhận named views vì không có camera riêng mỗi góc.
Không có required flag thì trả lỗi; thiếu flag tự căn khung thì trả cảnh báo.
PNG được verify rồi decode bởi Pillow. Không kiểm tra tự động chất lượng bố cục hay ảnh toàn nền.

SCAD và STL không mang đơn vị đáng tin cậy. `units` là quy ước cho toàn dự án:
mm mặc định, hỗ trợ cm/m/in; không tự scale geometry hay nội dung export.
Kích thước mục tiêu, dung sai, bàn in dùng cùng đơn vị dự án; thể tích dùng đơn vị³,
diện tích dùng đơn vị². Heuristic kích thước được đổi sang mm trước khi đánh giá.
Khi có dung sai phần trăm, ngưỡng là `max(tolerance, target * percent_tolerance / 100)`.
Các trục mục tiêu `null` được bỏ qua.

Chính sách mặc định yêu cầu một component, kích thước dương hữu hạn, winding nhất quán,
không duplicate/degenerate face, không edge có hơn hai face; nếu yêu cầu watertight thì
phải kín và thể tích dương. Nhiều chi tiết rời được coi là chưa đạt; tạo dự án riêng cho từng chi tiết.
`require_watertight=false` chỉ bỏ điều kiện kín và thể tích khi không tính được,
không bỏ kiểm tra các lỗi khác. Bàn in kiểm tra extents sau tịnh tiến, không thử xoay tối ưu;
cube có center=true không bị đánh trượt chỉ vì tọa độ âm.

Độ dày thành, support, overhang, khe lắp và tự giao cắt chưa có thuật toán kiểm tra,
luôn ghi `unknown`. Kích thước dưới 0,1 mm hoặc trên 10 m chỉ là cảnh báo heuristic.
Finalized nghĩa là vượt các cổng kiểm tra đã triển khai, không phải bảo đảm in thành công.
`requirements` là mô tả cho AI, không phải bộ điều kiện hình học tự thực thi.

## Ví dụ drone

Yêu cầu AI client:

> Tạo một drone mini 4 cánh sử dụng động cơ đường kính 7 mm. Khoảng cách chéo giữa tâm
> các động cơ là 65 mm. Thân có khoang đặt pin và bo điều khiển. Độ dày thành tối thiểu
> 1,2 mm. Mỗi motor mount phải có đường kính trong 7,2 mm. Render sáu góc nhìn, xuất STL,
> kiểm tra mesh kín, kiểm tra kích thước và hoàn thiện model.

7 mm là đường kính **động cơ**, không phải đường kính cánh quạt. AI cần tự tạo SCAD,
dùng `create_project` để lưu rồi theo quy trình trên. Khoảng cách chéo tâm motor 65 mm
không phải kích thước bounding box; AI phải tính kích thước tổng từ thiết kế trước khi
truyền `expected_dimensions`. Đường kính trong và thành 1,2 mm không được kiểm chứng
bởi phép đo bounding box. Cần kiểm tra mã/thực hiện phép đo bổ sung và chọn kích thước
pin, bo điều khiển, cánh quạt trước khi sử dụng thực tế.

## Dữ liệu và tính toàn vẹn

```text
workspace/
  .locks/workspace.lock
  .tmp/
  projects/<uuid>/
    project.json
    current/model.scad
    versions/<version>/model.scad
    versions/<version>/version.json
    previews/
    exports/
    reports/
  trash/<uuid>-<unique-id>/
```

Tên người dùng chỉ nằm trong metadata; đường dẫn dùng UUID hex 32 ký tự.
UTC ISO 8601 cho mọi timestamp; SHA-256 theo byte UTF-8 không BOM.
Mã đầu vào được chuẩn hóa CRLF/CR thành LF trước khi lưu và tính checksum.
Một file lock liên tiến trình tuần tự hóa toàn bộ request trên cùng workspace, gồm finalize.
Lock timeout trả `workspace_busy`; cách này ưu tiên nhất quán hơn thông lượng.
MCP là tầng truy cập được hỗ trợ; khi dùng `DesignService` trực tiếp, caller phải giữ
`service.workspace.lock` nếu có truy cập đồng thời.

Snapshot không bị sửa bởi tool. Khi update: kiểm expected_version, kiểm snapshot cũ,
tạo snapshot mới, ghi current bằng replace atomic, metadata commit cuối.
Nếu update thất bại trước commit, rollback snapshot mới và khôi phục current.
Snapshot của version đã commit là nguồn chuẩn; lần đọc sau sửa lại current nếu lệch.
Sự cố mất điện đúng giữa các bước có thể để snapshot chưa commit hoặc thư mục stage;
server không ghi đè snapshot đó. Dừng server, sao lưu workspace và kiểm metadata/history
trước khi chuyển snapshot chưa commit ra nơi lưu trữ phục hồi rồi thử lại.
Atomic replace không phải giao dịch nhiều tệp chống mất điện tuyệt đối.

Xóa chỉ chuyển vào trash. Muốn khôi phục dự án đã xóa: dừng server, kiểm tra thư mục đích
`restore_path` chưa tồn tại, dùng `Move-Item -LiteralPath` chuyển `trash_path` về đó.
Không có tự động xóa trash hoặc version cũ. Runtime workspace đã nằm trong `.gitignore`;
nếu cấu hình workspace khác trong repo, tự thêm đường dẫn đó vào ignore.

## Biến môi trường

| Biến | Mặc định |
|---|---:|
| `OPENSCAD_MCP_WORKSPACE` | `workspace` trong working directory lúc khởi động |
| `OPENSCAD_MCP_VALIDATE_TIMEOUT` | 30 giây |
| `OPENSCAD_MCP_PREVIEW_TIMEOUT` | 60 giây |
| `OPENSCAD_MCP_EXPORT_TIMEOUT` | 180 giây |
| `OPENSCAD_MCP_INSPECT_TIMEOUT` | 60 giây |
| `OPENSCAD_MCP_LOCK_TIMEOUT` | 10 giây |
| `OPENSCAD_MCP_MAX_CODE_BYTES` | 2097152 |
| `OPENSCAD_MCP_MAX_PREVIEW_DIMENSION` | 4096 |
| `OPENSCAD_MCP_MAX_PREVIEWS` | 12 |
| `OPENSCAD_MCP_MAX_EXPORT_BYTES` | 524288000 |
| `OPENSCAD_MCP_MAX_IMAGE_BYTES` | 67108864 |
| `OPENSCAD_MCP_MAX_LOG_BYTES` | 1048576 cho mỗi stdout/stderr |

Độ phân giải từ 16 đến maximum; maximum không vượt 4096. Số góc từ 1 đến maximum,
maximum không vượt 12. Timeout subprocess không vượt 3600 giây; lock tối đa 60 giây.
Giá trị cấu hình sai làm server dừng khi khởi động. Validate gồm tối đa 30 giây compile
và 60 giây inspect; capability probe có hai lệnh tối đa 10 giây. Finalize là tổng hữu hạn
của các bước, không retry vô hạn. Giới hạn file/log được theo dõi mỗi 25 ms và kiểm lại
khi kết thúc, nên tiến trình có thể vượt tạm giới hạn giữa hai lần kiểm tra.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pytest -m 'not integration'
.\.venv\Scripts\python.exe -m pytest -m integration
```

Unit test mock OpenSCAD; integration test tự skip nếu không tìm thấy executable.
Mypy kiểm tra theo phiên bản Python đang chạy; Ruff kiểm cú pháp mục tiêu Python 3.11.
Fixture cube thật nằm ở `tests/fixtures/cube.scad`. Có kiểm thử MCP in-process và
stdio subprocess, schema 17 tools, timeout/log/output limits, Unicode, symlink,
version conflict/restore/atomic rollback, mesh, dimensions, finalize đạt và không đạt.

## Lỗi thường gặp và giới hạn bảo mật

| Hiện tượng khi setup | Cách kiểm tra |
|---|---|
| Client không thấy MCP | Kiểm tra đúng file cấu hình/đúng host, lưu và restart/reload; chạy lệnh list của client |
| `No module named openscad_design_mcp` | Dùng đúng Python trong `.venv`, chạy lại `python.exe -m pip install -e .` bằng chính Python đó |
| `spawn ENOENT` hoặc không mở được executable | Kiểm `Test-Path` với đường dẫn Python tuyệt đối trong config; không trỏ tới thư mục `.venv` |
| JSON báo escape không hợp lệ | Dùng `\\` trong JSON; không sao chép nguyên chuỗi TOML vào JSON |
| OpenCode báo unknown field | Dùng mẫu tương ứng 1.x/2.x; không đổi `environment` thành `env` |
| IDE không nhận biến môi trường mới | Đặt biến trong mục `env`/`environment` của MCP và restart client |
| Thấy tools nhưng agent không gọi | Kiểm tra quyền tool/model của client; yêu cầu tên `get_system_status` rõ ràng |

Các cấu hình được đối chiếu tài liệu ngày 05/09/2026. JSON/TOML và FastMCP CLI đã
được kiểm tra trực tiếp; Antigravity/Codex CLI được đối chiếu `--help`, OpenCode 1.18.25
được kiểm tra phiên bản. Chưa xác nhận end-to-end bằng tài khoản AI trong từng IDE hoặc
OpenCode v2. Xem [VERIFICATION.md](VERIFICATION.md) cho kiểm thử server và workflow thật.

- Không tìm thấy OpenSCAD: kiểm tra cài đặt và `OPENSCAD_PATH`; server vẫn quản lý code,
  nhưng không thể validate/render/export đến khi executable sẵn sàng.
- Syntax error, model rỗng: đọc `data.stderr`, `errors`; cập nhật mã với version hiện tại.
  Thông tin thống kê render trên stderr không bị coi là lỗi. Warning không tự làm fail.
- Include/use/import/surface: bị chặn trước khi chạy, kể cả đường dẫn tương đối.
  Tự đưa module SCAD đáng tin cậy vào mã, không tải thư viện hay URL tự động.
- DXF/SVG cần hình học 2D, ví dụ `projection() cube(10);`. `export_model` hỗ trợ;
  `validate_scad` và finalize là quy trình 3D nên yêu cầu STL có mesh.
- PNG không render được: kiểm tra driver/OpenGL/session Windows tương tác. STL vẫn có
  thể hoạt động. `get_system_status` probe render thực thay vì chỉ kiểm executable.
- Timeout: giảm `$fn`, bớt boolean phức tạp hoặc tăng timeout hợp lý.
- `version_conflict`: đọc lại model/version rồi áp dụng sửa đổi; không cố ghi đè.
- `unsafe_path`: không dùng symlink/junction trong workspace hoặc các thư mục cha.
- `workspace_busy`: một tool đang giữ lock; chờ hoàn tất và thử lại.

Chỉ chạy **mã SCAD đáng tin cậy**, dưới tài khoản ít quyền. Đây không phải sandbox OS.
Server không nhận đường dẫn hoặc đối số CLI tùy ý từ client; chặn traversal, absolute ID,
symlink/junction, mã quá lớn, file ngoài workspace và các lệnh đọc file SCAD thông dụng.
OpenSCAD vẫn cần đọc thư viện hệ thống/font/cấu hình để hoạt động. Bộ lọc SCAD là lớp
phòng vệ, không phải parser bảo mật hoàn hảo hay bảo vệ trước lỗi trong executable.
Không có hard quota RAM/CPU/ổ đĩa cấp OS; tổng số dự án, version, artifact chưa có quota.
Process timeout cố kill cả cây con bằng psutil; không tương đương Windows Job Object.
Một tiến trình khác có quyền sửa workspace có thể tạo race giữa kiểm tra path và mở file;
hãy giới hạn ACL workspace và không chia sẻ với người dùng không tin cậy.
Không nhận mesh upload hoặc gọi mạng từ server. Sanitizer loại control/ANSI và che đường
dẫn trong diagnostics, nhưng `echo()` trong mã có thể chứa nội dung do người dùng đưa vào.
Giữ stdout dành riêng cho protocol. Sao lưu workspace định kỳ.
