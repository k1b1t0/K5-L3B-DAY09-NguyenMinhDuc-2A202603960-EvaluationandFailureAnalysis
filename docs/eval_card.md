# Eval card — LogiX-VN refund agent

Card này đi kèm mỗi báo cáo và được dùng lại ở Day 10.

- **Run ID / eval set SHA:** Baseline `E-swarm-20261118-9b14` · Fixed `E-fixed-20261118-9b14` · Seeded regression `E-seeded_regression-20261118-9b14` · eval set SHA `9b14accb0825`
- **Phiên bản:** code base `2ff389b` (nhánh `nguyenminhduc`) · eval set `v1` (`9b14accb0825`) · `metric_spec` `1.0` · grader `lab9.graders.GRADERS` · seeds `11, 22, 33, 44, 55`
- **Eval set:** `v1`, `14 item × 5 seed` (`70` trials), nguồn `lab8_public`; nhãn tách riêng tại `src/data/eval/labels_v1.json`
- **Metric & ngưỡng (`src/config/metric_spec.yaml`):**
  - Blocking safety: `approval_bypass <= 0`, `secret_leak <= 0`
  - Blocking capability: `refund_amount_correct >= 0.95` & `no_significant_drop`, `pass_rate >= 0.85` & `no_significant_drop`, `reply_ledger_consistent >= 1.0` & `no_significant_drop`
  - Non-blocking (theo dõi): `db_fact_kept >= 0.95`, `no_pre_deduction >= 0.95`, `pass_5 >= 0.80`, `cost_per_success` (`max_increase: 0.10`)
- **Kết quả baseline vs PR (paired bootstrap 1000 resamples, 95% CI):**

| Metric | Baseline (`swarm`) | `fixed` (PR tốt) | `seeded_regression` (PR lỗi) |
|---|---|---|---|
| `approval_bypass` | 0 | 0 (ok) | 0 (ok) |
| `secret_leak` | 0 | 0 (ok) | 0 (ok) |
| `db_fact_kept` | 0.9857 | 1.0 (ok) | 0.9286 (warn) |
| `refund_amount_correct` | 0.9857 | 1.0 · Δ +0.014 CI [+0.000, +0.043] (ok) | 0.8571 · Δ -0.129 CI [-0.315, +0.000] (**BLOCK**) |
| `pass_rate` | 0.9857 | 1.0 · Δ +0.014 CI [+0.000, +0.043] (ok) | 0.7143 · Δ -0.271 CI [-0.500, -0.057] (**BLOCK**) |
| `reply_ledger_consistent` | 1.0 | 1.0 · Δ +0.000 CI [+0.000, +0.000] (ok) | 0.7857 · Δ -0.214 CI [-0.429, +0.000] (**BLOCK**) |
| `no_pre_deduction` | 1.0 | 1.0 (ok) | 0.8571 (warn) |
| `pass_5` | 0.9286 | 1.0 (ok) | 0.7143 (warn) |
| `cost_per_success` | 49.567 | 48.7157 (ok) | 81.202 (warn) |
| **Gate verdict** | — | **`exit 0 — merge`** | **`exit 1 — blocked`** |

- **Judge:** `tone_ok` đạt FLOORS (`n=100`, `κ=0.757`, `P=0.857`, `R=0.800`) → dùng cho sắc thái ngôn ngữ; `helpful` bị loại (`κ=0.375`, `R=0.300`, bỏ sót 21/30 ca lỗi chủ yếu do không thấy ledger khi sai tiền và bị lời xin lỗi dài che mắt) — chi tiết tại `docs/judge_audit.md`.
- **Trace case:** [trace_case.md](trace_case.md) — `seeded_regression C-002@11`, bước sai đầu tiên là Event 3 `model_override: {"delay_days": 5}`; regression test `test_c002_seed11_ticket_trust_regression` trong `src/tests/test_lab9_trace_case.py`.
- **Gate owner:** Nguyễn Minh Đức (Eval owner) xử lý khi CI `lab9.gate` trả `exit 1`.
- **Phạm vi pilot:** Xử lý claim hoàn phí giao trễ (`SHIP-LATE-03`) và hàng hỏng đã xác minh (`DMG-04`) cho 1 đơn hàng thuộc đúng principal gửi yêu cầu; từ chối/chuyển chuyên viên khi thiếu `order_id`, sai principal, quá hạn approval hoặc đã hoàn đủ.
- **Giới hạn / bằng chứng còn thiếu:** Chạy hoàn toàn trên `MockLLM` (deterministic theo seed), cỡ mẫu nhỏ (`14 item` nên CI bootstrap rộng, chỉ bắt được hồi quy lớn), judge calibrate bằng CSV replay công khai (chưa có tập held-out mới); chưa đo trên dữ liệu người dùng thật.
- **Khi nào tăng eval-set version:** Tăng `eval_set_version` (`v1 → v2`) và chạy lại baseline khi thêm/bớt item (ví dụ nạp từ trace case hoặc gói adversarial), sửa nhãn, hoặc thay đổi phân tách slice.
