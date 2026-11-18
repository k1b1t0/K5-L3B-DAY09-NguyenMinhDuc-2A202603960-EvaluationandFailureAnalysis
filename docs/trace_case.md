# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Case điều tra (`seeded_regression C-002@11`)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11` (trace run `R-seeded_regression-C-002-s11`, report `E-seeded_regression-20261118-9b14`) |
| Triệu chứng | `TrialPass` fail (`status resolved != denied`); `RefundAmountCorrect` fail (`ledger=20000` vs nhãn `0`). Reply nói `"Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."` |
| Bước sai đầu tiên | **Event 3** `model_override`: `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event 1 (`handoff`) giao đúng phạm vi công cụ read-only; Event 2 (`investigator`) truy vấn đúng sự thật DB cho `O-202` (`status="delivered"`, `delay_days=2`). Sang Event 3, agent mới tự ý lấy số `5` từ ticket đè lên `delay_days=2` của DB. |
| Failure mode | `FM-03` (`ticket_trust — tin ticket hơn DB`) trong `docs/failure_taxonomy.md` |
| Đối chứng | Trên `fixed C-002@11`: không có event `model_override`; sau Event 2 (`delay_days=2`), Event 3 là `quote` (`amount_vnd=0`, `no_entitlement`), ledger `refund_vnd=0`, `status="denied"`. |
| Regression test | `test_c002_seed11_ticket_trust_regression` trong `src/tests/test_lab9_trace_case.py` dùng `DbFactKept` + `RefundAmountCorrect` (đã chạy: fail đúng trên `seeded_regression`, pass trên `fixed`). |
| Chưa chắc chắn | Trace chỉ ghi `model_override` vì variant chủ động log; một biến thể thực tế (như `quiet_override`) có thể sửa `delay_days` trong bộ nhớ mà không ghi event này — khi đó phải bắt ở bước `quote`/outcome (`RefundAmountCorrect`). |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
