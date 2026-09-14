

31/7/2026: 
           - đã review xong với GPT về đường hướng phát triển mới, tiếp theo cần nói GPT tiếp tục phát triển
           - Hiện tại đã hỗ trợ được motor, linesensor(cần test lại), ultra sensor(cần test lại) -> đủ để lắp mạch demo

2/8: Xử lý xong vấn đề line sensor, tiếp theo cần xử lý vấn đề test cho sensor. Vô GPt để check plan tiếp

7/8: vừa xử lý xong phần UI, GPT mới review, tiếp theo sẽ yêu cầu GPT tạo task tiếp

10/8: Đã gửi cho GPT review, tiếp theo sẽ yêu cầu làm tiếp
      - GPT vừa review xong phần intergration test(VM), tiếp theo sẽ là yêu cầu GPT giao task và tiếp tục làm, tuy nhiên cần hardware nên sẽ sắp xếp làm ở lab

14/8: điều chỉnh factor rồi nạp code test, sau đó sẽ tiếp tục verify lại soft hiện tại

- Quay lại thì tiếp tục làm test 3. Em muốn làm một test rất quan trọng tiếp theo

Không cần sửa code.

TEST 12 — Forward → STOP → Ultra

19/8/2026:
- Đã merge code H1, cần nạp code hardware để test - test case đã cung cấp ở GPT, hãy làm theo hướng dẫn

- Đã yêu cầu GPT tạo task, tiếp theo cần download task và yêu cầu deepseek làm

22/8: Hiện đang làm C5, cần verify các chương trình robosim để đảm bảo chạy được thông suốt

23/8: đã làm việc với GPT H21, làm tiếp để sửa line

25/8: Đã làm H23-C, tiếp sẽ flash và test rồi feedback

27/8: với branch motion_debug đã fix được làm robot có thể follow line, tuy nhiên độ ổn định chưa cao cần thay thế motor trái để có torque lớn hơn rồi tối ưu hóa tiêp code

6/9:
      - đã yêu cầu GPT fix, chưa merge vào codebase. Tiếp theo cần làm theo hướng dẫn GPT để test và flash được qua OTA. Sau khi quay lại merge PR46

7/9/2026:
      - Đã làm xong H29 D, đã merge xong PR74. Tất cả test case đã pass, tiếp theo cần audit và làm tiếp

11/9:
      - Chưa merge PR112, tiếp cần merge 112 và pull về chạy lại test

13/9:
      - Đã tạo bug fix, chưa merge git -> merge git, chạy test