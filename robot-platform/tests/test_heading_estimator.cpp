#include <catch2/catch.hpp>
#include "Services/Motion/HeadingEstimator.h"
#include "Sensor/IMUSensor.h"

TEST_CASE("HeadingEstimator initialization", "[heading]") {
    HeadingEstimator est;
    REQUIRE(est.isInitialized() == false);
    REQUIRE(est.getHeadingDeg() == 0.0f);
}

TEST_CASE("HeadingEstimator first sample", "[heading]") {
    HeadingEstimator est;
    IMUSample sample;
    sample.valid = true;
    sample.timestamp = 1000;
    sample.gyro.gz = 10.0f;

    bool updated = est.update(sample);
    REQUIRE(updated == false);  // first sample doesn't integrate
    REQUIRE(est.isInitialized() == true);
    REQUIRE(est.getHeadingDeg() == 0.0f);
}

TEST_CASE("HeadingEstimator constant positive rotation", "[heading]") {
    HeadingEstimator est;
    IMUSample s1{ .valid = true, .timestamp = 1000, .gyro = {0,0,10} };
    est.update(s1);  // first

    IMUSample s2{ .valid = true, .timestamp = 1100, .gyro = {0,0,10} };
    est.update(s2);  // dt = 0.1s
    REQUIRE(est.getHeadingDeg() == Approx(1.0f));  // 10 * 0.1 = 1

    IMUSample s3{ .valid = true, .timestamp = 1200, .gyro = {0,0,10} };
    est.update(s3);
    REQUIRE(est.getHeadingDeg() == Approx(2.0f));
}

TEST_CASE("HeadingEstimator constant negative rotation", "[heading]") {
    HeadingEstimator est;
    IMUSample s1{ .valid = true, .timestamp = 1000, .gyro = {0,0,-10} };
    est.update(s1);
    IMUSample s2{ .valid = true, .timestamp = 1100, .gyro = {0,0,-10} };
    est.update(s2);
    REQUIRE(est.getHeadingDeg() == Approx(-1.0f));
}

TEST_CASE("HeadingEstimator zero gyro", "[heading]") {
    HeadingEstimator est;
    IMUSample s1{ .valid = true, .timestamp = 1000, .gyro = {0,0,0} };
    est.update(s1);
    IMUSample s2{ .valid = true, .timestamp = 1100, .gyro = {0,0,0} };
    est.update(s2);
    REQUIRE(est.getHeadingDeg() == 0.0f);
}

TEST_CASE("HeadingEstimator invalid dt (dt=0)", "[heading]") {
    HeadingEstimator est;
    IMUSample s1{ .valid = true, .timestamp = 1000, .gyro = {0,0,10} };
    est.update(s1);
    IMUSample s2{ .valid = true, .timestamp = 1000, .gyro = {0,0,10} };
    bool updated = est.update(s2);
    REQUIRE(updated == false);
    REQUIRE(est.getHeadingDeg() == 0.0f);
}

TEST_CASE("HeadingEstimator excessive dt", "[heading]") {
    HeadingEstimator est;
    IMUSample s1{ .valid = true, .timestamp = 1000, .gyro = {0,0,10} };
    est.update(s1);
    IMUSample s2{ .valid = true, .timestamp = 1200, .gyro = {0,0,10} }; // dt=0.2s > MAX_DT=0.1
    bool updated = est.update(s2);
    REQUIRE(updated == false);
    REQUIRE(est.getHeadingDeg() == 0.0f);
}

TEST_CASE("HeadingEstimator reset", "[heading]") {
    HeadingEstimator est;
    IMUSample s1{ .valid = true, .timestamp = 1000, .gyro = {0,0,10} };
    est.update(s1);
    IMUSample s2{ .valid = true, .timestamp = 1100, .gyro = {0,0,10} };
    est.update(s2);
    REQUIRE(est.getHeadingDeg() == Approx(1.0f));
    est.reset();
    REQUIRE(est.isInitialized() == false);
    REQUIRE(est.getHeadingDeg() == 0.0f);
    // Sau reset, sample tiếp theo chỉ thiết lập timestamp
    IMUSample s3{ .valid = true, .timestamp = 1200, .gyro = {0,0,10} };
    est.update(s3);
    REQUIRE(est.getHeadingDeg() == 0.0f);
    IMUSample s4{ .valid = true, .timestamp = 1300, .gyro = {0,0,10} };
    est.update(s4);
    REQUIRE(est.getHeadingDeg() == Approx(1.0f));
}

TEST_CASE("HeadingEstimator invalid sample", "[heading]") {
    HeadingEstimator est;
    IMUSample s1{ .valid = true, .timestamp = 1000, .gyro = {0,0,10} };
    est.update(s1);
    IMUSample s2{ .valid = false, .timestamp = 1100, .gyro = {0,0,10} };
    bool updated = est.update(s2);
    REQUIRE(updated == false);
    REQUIRE(est.getHeadingDeg() == 0.0f);
}