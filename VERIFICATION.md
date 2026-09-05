# Kết quả kiểm chứng ngày 05/09/2026

Thực hiện trên Windows, Python 3.12.4 và OpenSCAD 2021.01 tại
`C:\Program Files\OpenSCAD\openscad.exe`.

| Kiểm tra | Kết quả |
|---|---|
| `python -m pip install -e .` | Thành công |
| `python -m pip check` | Không có dependency bị lỗi |
| `python -m ruff format --check .` | Đạt |
| `python -m ruff check .` | Đạt |
| `python -m mypy` | Không lỗi trong 12 source files |
| `python -m pytest -q` | 64 passed, 1 skipped, 17,63 giây |
| Integration OpenSCAD thật | 8 passed trong tổng số trên |
| Unit/MCP tests | 56 passed, 1 skipped trong tổng số trên |
| MCP schema | Đủ 17 tools, có output schema, không lộ tham số self |
| Module stdio | Khởi chạy bằng `python -m openscad_design_mcp`, gọi tool thành công |
| Syntax Python 3.11 | AST parse thành công với feature_version 3.11 |
| Comment Python | Không có token COMMENT trong source, tests, example |

Test symlink thật được skip vì tài khoản Windows thiếu quyền tạo symbolic link.
Test Windows junction chạy thật và đạt. Chưa chạy toàn bộ suite trên Python 3.11
hoặc trên một máy Windows 10 riêng; runtime kiểm chứng là Python 3.12.4.

Cube `cube([20, 20, 10], center = true);` đã được tạo và finalize qua MCP stdio thật:

- Project ID: `4f6570506d2d4c60b647508653b5d09d`.
- Sáu PNG: isometric, front, right, back, left, top; 800 × 600.
- Đã xem ảnh isometric trực quan: model nằm trọn khung và có hình khối đúng.
- STL kín, winding nhất quán, một component, 8 vertices sau gộp trùng, 12 faces.
- Kích thước 20 × 20 × 10 mm, thể tích 4000 mm³.
- `finalized: true`; báo cáo nằm trong `workspace/projects/<project-id>/reports/`.
- Kết quả toàn bộ MCP nằm trong `workspace/cube-workflow-result.json`.

Integration test còn kiểm chứng export/inspect 3MF, export OFF/AMF/DXF/SVG,
SCAD sai cú pháp, model rỗng và probe PNG thực. Workspace thử nghiệm có dấu tiếng Việt
và dấu cách. Runtime được bỏ qua bởi `.gitignore`.

Các phiên bản đã sử dụng:

| Thư viện | Phiên bản |
|---|---|
| FastMCP | 4.0.3 |
| Trimesh | 5.1.0 |
| manifold3d | 3.5.2 |
| Pillow | 12.3.0 |
| Pydantic | 2.13.5 |
| NumPy | 2.5.2 |
| SciPy | 1.18.1 |
| NetworkX | 3.6.1 |
| lxml | 6.1.3 |
| pytest | 9.1.1 |
| Ruff | 0.16.6 |
| mypy | 2.3.1 |

Xem README để biết giới hạn thuật toán, chính sách finalize và giới hạn sandbox.
Thư mục ban đầu không có Git repository; không thực hiện commit hoặc thay đổi cấu hình client.
