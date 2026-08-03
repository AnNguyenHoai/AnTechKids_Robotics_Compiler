# S3.3C.3 – Query Bitmask Encoding

## Official Bit Mapping

| Physical Sensor | Bit Position | Mask Value |
|-----------------|--------------|------------|
| Left            | 2            | 4 (0b100)  |
| Center          | 1            | 2 (0b010)  |
| Right           | 0            | 1 (0b001)  |

## Contract

- `GetTraceV2I2CData(port)` trả về bitmask theo quy ước trên.
- Tất cả các tầng Perception, Decision, Motion đều dùng chung quy ước này.
- Không được thay đổi ở các sprint sau.