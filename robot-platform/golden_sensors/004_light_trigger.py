while True:
    val = read_light(0)
    if val > 500:
        # giả sử bật đèn (chưa có API LED)
        pass
    wait(50)