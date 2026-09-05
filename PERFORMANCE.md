# Kiểm thử độ ổn định và hiệu suất

Đo ngày 05/09/2026 trên Windows, Python 3.12.4, OpenSCAD 2021.01.
Mốc trước tối ưu: commit `a8aa675`. Mỗi model chạy 3 lần, dùng trung vị wall time.
Cùng chế độ preview, sáu góc 800 × 600. Không giảm độ phân giải hay bỏ kiểm tra mesh.

| Model | Bước | Trước (s) | Sau (s) | Trước / sau |
|---|---|---:|---:|---:|
| cube | create | 1.0750 | 1.0932 | 0.98× |
| cube | validate | 0.0009 | 0.0084 | 0.10× |
| cube | previews | 0.3789 | 0.3734 | 1.01× |
| cube | export | 0.1443 | 0.0143 | 10.06× |
| cube | inspect | 0.9123 | 0.0084 | 108.63× |
| cube | finalize | 0.5267 | 0.4075 | 1.29× |
| plate | create | 2.1861 | 2.2242 | 0.98× |
| plate | validate | 0.0008 | 0.0086 | 0.09× |
| plate | previews | 0.3994 | 0.4107 | 0.97× |
| plate | export | 1.2458 | 0.0275 | 45.29× |
| plate | inspect | 0.9358 | 0.0086 | 108.23× |
| plate | finalize | 1.6592 | 0.4231 | 3.92× |

Cube: hộp 20 × 20 × 10. Plate: tấm 60 × 40 × 4 có sáu lỗ tròn, mỗi lỗ 48 đoạn.
Thứ tự benchmark: create → validate → previews → export → inspect → finalize.
Create bao gồm validate và inspect lần đầu. Các bước sau được phép dùng cache đã kiểm checksum.
Đây là phép đo workflow có tái sử dụng, không phải tốc độ biên dịch lạnh tăng tương ứng.
Cold create gần như không được tăng tốc. Validate cache chậm hơn khoảng vài mili giây vì giờ kiểm
checksum nguồn và artifact trước khi dùng lại; bản cũ bỏ qua kiểm tra nguồn khi cache hit.

## Thay đổi

- Giữ STL đã validate trong exports và dùng lại khi export STL; không compile cùng hình học hai lần.
- Lưu đúng kết quả inspection sau validate, thay vì bị mất do đọc lại metadata.
- Cache gắn với checksum SCAD, revision, compiler, phiên bản Trimesh và SHA-256 của file export.
- Cache cũ thiếu thông tin nguồn được xây lại; lỗi validate/timeout không được cache thành công.
- Kiểm checksum trước cache hit; file đổi/mất hoặc update/restore làm hết hiệu lực cache.
- Inspect 3MF kiểm chính bytes của 3MF mới xuất, không lấy nhầm metrics STL trước đó.
- Capability probe có khóa và tự làm mới khi binary/đường dẫn môi trường thay đổi.
- Render giữ thứ tự kết quả, cố định revision, có giới hạn worker cấu hình được.

## Điều chỉnh worker

`OPENSCAD_MCP_PREVIEW_WORKERS` từ 1 đến 8, mặc định 8 như mức song song tối đa trước tối ưu.
Đã thử 4 và 8: trên hai model này, 8 nhanh hơn; đây không phải kết luận cho mọi CPU/model.
Nếu máy ít RAM hoặc model boolean lớn, dùng 2 hoặc 4 để giảm số tiến trình OpenSCAD đồng thời.
Không có hard quota RAM cấp OS. Timeout, giới hạn output/log và khóa workspace vẫn được giữ.

## Chạy lại

```powershell
.\.venv\Scripts\python.exe examplesenchmark.py --output workspaceenchmark.json --repeats 3
.\.venv\Scripts\python.exe examplesenchmark.py --output workspace\workers4.json --repeats 3 --workers 4
.\.venv\Scripts\python.exe -m pytest -q
```

Benchmark tạo dự án/artifact trong workspace/benchmarks; dữ liệu này không vào Git.
JSON thô của lượt đo hiện tại: workspace/baseline.json và workspace/performance-final.json.

## Giới hạn kết luận

Lượt kiểm tra cuối: **81 passed, 1 skipped** trong 29,35 giây; Ruff format/lint và
mypy (12 source files) đạt. Test symlink thật skip vì thiếu quyền Windows; junction
và timeout cây tiến trình được kiểm tra thật. Source/tests/benchmark không có token comment.
Suite gồm MCP stdio, schema và integration OpenSCAD. Khởi động lại MCP trong client
để nạp mã mới; cache runtime cũ được xây lại khi thiếu thông tin nguồn cần thiết.

Kết quả phụ thuộc CPU, ổ đĩa, driver OpenGL, tải nền và hình học. Ba lần đo trên hai model
không chứng minh hiệu suất tối đa tuyệt đối hay độ ổn định cho mọi đầu vào.
Các test stress gồm 20 revision/finalize mock, finalize lặp với OpenSCAD thật rồi đổi kích thước,
cache lỗi/tamper/restore, worker bound/order, và kill cây tiến trình khi timeout.
Ảnh preview là chế độ nhanh hiện có; kiểm tra hình học vẫn dùng export STL/3MF và Trimesh.
Kiểm tra tệp lớn vẫn cần đọc SHA-256 toàn bộ file; không bỏ bước này để tăng tốc.
STL validation được giữ thêm trên đĩa, cùng lịch sử artifact; chưa có quota tổng dung lượng.
Metadata và workspace phải do tài khoản đáng tin cậy quản lý; cache không phải sandbox chống sửa metadata.
