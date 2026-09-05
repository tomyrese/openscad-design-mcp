# Tài liệu kỹ thuật

Người mới nên bắt đầu từ [README](../README.md).

## Bảng tra cứu 17 MCP Tools

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
| `compare_dimensions` | So sánh kích thước thực tế với kích thước yêu cầu theo dung sai tuyệt đối / phần trăm. | `project_id`, `expected_dimensions`, `tolerance`, `percent_tolerance` |
| `check_printability` | Kiểm tra một số điều kiện in 3D (kín nước, nằm trong bàn in, đơn khối). | `project_id`, `build_volume`, `require_watertight` |
| `finalize_model` | Chạy toàn bộ quy trình kiểm định và đánh dấu mô hình đã hoàn thiện. | `project_id`, `output_format`, `expected_dimensions`, `build_volume`, `require_watertight` |

---

## Chạy máy chủ thủ công

```powershell
.\.venv\Scripts\python.exe -m openscad_design_mcp
```

Máy chủ dùng `stdio`: đọc yêu cầu từ stdin, trả dữ liệu giao thức qua stdout và ghi log qua stderr. Việc cửa sổ chờ mà không hiện giao diện là bình thường. Dùng `examples\cube_workflow.py` để kiểm tra thực tế từ đầu đến cuối.

## Cấu hình nâng cao

Mặc định lấy workspace từ thư mục làm việc hiện tại. Các mẫu do `examples/client_configs.py` tạo đặt đường dẫn tuyệt đối đến `workspace` của bản cài để không phụ thuộc thư mục khởi chạy của ứng dụng AI. Script chỉ ghi đè các mẫu trong `workspace/client-configs`, không sửa cấu hình ứng dụng.

| Biến môi trường | Mặc định | Ý nghĩa |
|---|---|---|
| `OPENSCAD_PATH` | Tự tìm trong PATH và vị trí Windows thông dụng | Đường dẫn đến `openscad.exe` |
| `OPENSCAD_MCP_WORKSPACE` | `workspace` trong thư mục làm việc | Nơi lưu dự án |
| `OPENSCAD_MCP_PREVIEW_WORKERS` | 8 | Số tác vụ ảnh chạy đồng thời, từ 1 đến 8 |
| `OPENSCAD_MCP_VALIDATE_TIMEOUT` | 30 | Giới hạn giây cho biên dịch kiểm tra |
| `OPENSCAD_MCP_PREVIEW_TIMEOUT` | 60 | Giới hạn giây cho mỗi lần kết xuất ảnh |
| `OPENSCAD_MCP_EXPORT_TIMEOUT` | 180 | Giới hạn giây cho xuất mô hình |
| `OPENSCAD_MCP_INSPECT_TIMEOUT` | 60 | Giới hạn giây cho phân tích mesh |

Các giới hạn còn lại được định nghĩa trong [config.py](../src/openscad_design_mcp/config.py). Thời gian chờ của ứng dụng AI và giới hạn của OpenSCAD là hai cấu hình riêng: tăng một bên không tự tăng bên kia.

Máy ít RAM có thể giảm `PREVIEW_WORKERS` xuống 2 hoặc 4. Số luồng lớn hơn không luôn nhanh hơn với mọi mô hình. Xem [phương pháp đo và kết quả](../PERFORMANCE.md) trước khi so sánh.

Bộ nhớ đệm tái sử dụng kết quả hợp lệ khi mã nguồn, phiên bản và môi trường xử lý phù hợp. STL từ bước kiểm tra được giữ để tránh biên dịch lại khi xuất hoặc phân tích. Thay đổi mã nguồn làm mất hiệu lực kết quả cũ. Không hiểu các số đo warm cache là tốc độ dựng một mô hình mới.

Ảnh preview nhanh có thể khác kết quả dựng hình đầy đủ. Dùng chế độ render đầy đủ và kiểm tra tệp xuất khi cần xác nhận hình học cuối cùng. SVG/DXF dành cho hình học 2D; không phải mọi mô hình 3D đều xuất trực tiếp sang hai định dạng này.

## Kiểm thử và đo hiệu năng

Cài thêm công cụ phát triển:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Chạy tại thư mục gốc của dự án:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\mypy.exe src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe examples\cube_workflow.py
.\.venv\Scripts\python.exe examples\benchmark.py
```

Các bài tích hợp cần OpenSCAD thật và khả năng tạo PNG. Một số bài kiểm tra symlink trên Windows có thể bị bỏ qua nếu tài khoản không có quyền tạo symlink. Báo cáo phải nêu rõ bài bị bỏ qua, môi trường và việc dùng cache.

## Giới hạn cần giữ trong tài liệu và ứng dụng

`finalize_model` đánh dấu trạng thái hoàn thiện khi các kiểm tra được yêu cầu đạt; người dùng vẫn có thể tạo phiên bản chỉnh sửa tiếp theo. Đây không phải chứng nhận khả năng in, độ bền hoặc an toàn cơ khí.

Dự án có kiểm tra đường dẫn, checksum, phiên bản và thời gian thực thi. Những lớp kiểm tra này không tạo sandbox hệ điều hành và không thay thế hạn ngạch ổ đĩa. Chỉ chạy mã OpenSCAD đáng tin cậy và sao lưu dữ liệu cần giữ.
