#include <catch2/catch.hpp>
#include "Services/Motion/HeadingController.h"
#include "Services/Robot/RobotAPI.h" // chỉ dùng để lấy config? Tốt nhất là test logic riêng.

// Vì RobotAPI sử dụng static function và phụ thuộc hardware, ta sẽ test logic mixing riêng.
// Ta sẽ tạo một hàm mixing mock để kiểm tra.

// Hàm mixing mô phỏng (sao chép từ RobotAPI::_applyMotion)
struct MixingResult {
    int left;
    int right;
};

MixingResult mixWithHeading(int baseSpeed, int direction, float correction,
                            float leftScale, float rightScale, float speedScale) {
    int baseLeft = (int)(baseSpeed * speedScale * leftScale);
    int baseRight = (int)(baseSpeed * speedScale * rightScale);
    int leftEff, rightEff;

    if (direction < 0) {
        // Backward
        leftEff = -baseLeft - (int)correction;
        rightEff = -baseRight + (int)correction;
    } else {
        leftEff = baseLeft - (int)correction;
        rightEff = baseRight + (int)correction;
    }

    // Clamp
    if (leftEff > 100) leftEff = 100;
    if (leftEff < -100) leftEff = -100;
    if (rightEff > 100) rightEff = 100;
    if (rightEff < -100) rightEff = -100;

    return {leftEff, rightEff};
}

TEST_CASE("Motor mixing with heading correction", "[motor_mixing]") {
    float leftScale = 0.820f;
    float rightScale = 1.000f;
    float speedScale = 1.000f;
    int baseSpeed = 50;

    SECTION("Zero correction") {
        auto result = mixWithHeading(baseSpeed, 1, 0, leftScale, rightScale, speedScale);
        REQUIRE(result.left == 41);
        REQUIRE(result.right == 50);
    }

    SECTION("Forward positive correction (turn left)") {
        auto result = mixWithHeading(baseSpeed, 1, 5, leftScale, rightScale, speedScale);
        REQUIRE(result.left == 36);
        REQUIRE(result.right == 55);
        // Với L < R, turn left (positive correction -> left)
        REQUIRE(result.left < result.right);
    }

    SECTION("Forward negative correction (turn right)") {
        auto result = mixWithHeading(baseSpeed, 1, -5, leftScale, rightScale, speedScale);
        REQUIRE(result.left == 46);
        REQUIRE(result.right == 45);
        // Với L > R, turn right
        REQUIRE(result.left > result.right);
    }

    SECTION("Backward positive correction (turn left)") {
        auto result = mixWithHeading(baseSpeed, -1, 5, leftScale, rightScale, speedScale);
        // Công thức: left = -baseLeft - corr = -41 -5 = -46, right = -baseRight + corr = -50 +5 = -45
        REQUIRE(result.left == -46);
        REQUIRE(result.right == -45);
        // Với L < R (âm hơn) -> turn left
        REQUIRE(result.left < result.right);
    }

    SECTION("Backward negative correction (turn right)") {
        auto result = mixWithHeading(baseSpeed, -1, -5, leftScale, rightScale, speedScale);
        // left = -41 - (-5) = -36, right = -50 + (-5) = -55
        REQUIRE(result.left == -36);
        REQUIRE(result.right == -55);
        // Với L > R -> turn right
        REQUIRE(result.left > result.right);
    }

    SECTION("Correction symmetry") {
        auto pos = mixWithHeading(baseSpeed, 1, 5, leftScale, rightScale, speedScale);
        auto neg = mixWithHeading(baseSpeed, 1, -5, leftScale, rightScale, speedScale);
        // (+5): L=36, R=55. (-5): L=46, R=45.
        // Sự khác biệt: left diff = 46-36=10, right diff = 45-55=-10 -> đối xứng
        REQUIRE((pos.right - pos.left) == 19);  // 55-36
        REQUIRE((neg.right - neg.left) == -1); // 45-46
        // Sự đối xứng thể hiện qua việc correction +5 và -5 tạo ra sự khác biệt ngược dấu
    }

    SECTION("Saturation") {
        auto result = mixWithHeading(95, 1, 20, leftScale, rightScale, speedScale);
        REQUIRE(result.left <= 100);
        REQUIRE(result.right <= 100);
        REQUIRE(result.left >= -100);
        REQUIRE(result.right >= -100);
    }
}