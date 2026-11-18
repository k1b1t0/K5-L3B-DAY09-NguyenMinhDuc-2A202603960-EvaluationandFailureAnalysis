# Judge audit

Chạy:
- `python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5`
- `python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Observed / RG Corrected | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|---|
| `tone_ok` | 100 | 0.757 | 0.857 | 0.800 | 0.280 → 0.300 | Đạt (tp=24, fp=4, fn=6, tn=66) | **Dùng** (theo dõi thêm sau sửa rubric) |
| `helpful` | 100 | 0.375 | 1.000 | 0.300 | 0.090 → 0.300 | **Không đạt** (tp=9, fp=0, fn=21, tn=70) | **Loại** (cấm dùng làm gate) |

## Audit ≥5 case bất đồng (kèm hành động sửa rubric / grader)
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú & hành động sửa |
|---|---|---|---|---|---|
| 1 | `H-008` ("Em đã hoàn tiền cho anh rồi nha, anh check giúp em.") | PASS | FAIL | Người | Judge tưởng "thân thiện". **Sửa rubric `tone_ok`:** cấm đại từ thân mật/suồng sã (`em`, `bạn`, `nha`, `nhé`); bắt buộc dùng `anh/chị` và xưng `LogiX`. |
| 2 | `H-029` ("Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm.") | PASS | FAIL | Người | Judge bị đánh lừa bởi chữ "Dạ, vui lòng" đầu câu. **Sửa rubric `tone_ok`:** phạt giọng ra lệnh/chặn giao tiếp (`không cần nhắn thêm`) bất kể từ đệm lịch sự. |
| 3 | `H-051` ("Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ.") | FAIL | PASS | Người | Judge quá khắt khe khi phạt từ `refund`. **Sửa rubric `tone_ok`:** cho phép thuật ngữ CSKH phổ thông của LogiX (`refund`, `claim`) nếu câu lịch sự, rõ nghĩa. |
| 4 | `H-070` ("Dạ, LogiX đã hoàn 90.000đ cho đơn O-909 ạ 😂😂") | PASS | FAIL | Người | Emoji cười cợt không phù hợp ngữ cảnh khiếu nại. **Sửa rubric `tone_ok`:** bổ sung quy tắc cấm emoji giải trí/cảm thán trong phản hồi khiếu nại hoàn tiền. |
| 5 | `H-081` ("Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ.") | FAIL | PASS | **Judge** | Người gán nhãn sai do đọc nhầm ticket. **Hành động:** sửa lại gold label của `H-081` và kiểm tra chéo (2-annotator review) cho các ca từ chối. |
| 6 | `HL-016` ("Dạ, LogiX thành thật xin lỗi... đã hoàn 55.000đ cho đơn O-404...") | PASS | FAIL | Người | Ledger thực ghi `35.000đ`, reply nói `55.000đ` nhưng xin lỗi dài dòng khiến judge cho PASS (verbosity bias). **Hành động:** tách kiểm tra số tiền sang **code grader** đối chiếu ledger (`FM-08`), không giao cho judge. |
| 7 | `HL-047` ("Ok bạn, đơn O-515 xử lý rồi nhé.") | PASS | FAIL | Người | Sai xưng hô và thiếu thông tin kết quả cụ thể. **Hành động:** chuyển tiêu chí xưng hô sang rubric `tone_ok` và kiểm tra đủ ý/số tiền bằng code + rubric rõ ràng. |

## Kết luận
- **Tiêu chí bị loại:** `helpful` (`κ = 0.375 < 0.6`, `R = 0.300 < 0.7`, `fn = 21`). Không được dùng `helpful` làm gate vì bỏ sót **21/30 ca lỗi thật** (`70%` miss rate): `18/21` ca `fn` là lỗi **sai số tiền so với ledger** (judge không thấy ledger và bị đánh lừa bởi lời xin lỗi dài dòng), khiến tỉ lệ lỗi quan sát chỉ còn `0.09` dù tỉ lệ lỗi thật sau hiệu chỉnh Rogan-Gladen là `0.30`.
- **Nguyên tắc áp dụng:** Mọi tiêu chí về tiền, trạng thái và phê duyệt phải chấm bằng **code**; chỉ dùng `tone_ok` làm judge cho sắc thái ngôn ngữ sau khi cập nhật rubric ở bảng trên.
- **Rủi ro còn lại:** Hai bộ CSV đều là dữ liệu replay đã công khai; sau khi sửa rubric `tone_ok`, cần thu thập và gán nhãn tập held-out mới để đo lại `κ`, `P`, `R` trước khi đưa vào gate tự động.
