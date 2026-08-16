#include <catch2/catch.hpp>
#include "Services/Motion/HeadingController.h"

TEST_CASE("HeadingController initialization", "[heading_controller]") {
    HeadingController ctrl;
    ctrl.init(1.0f, 0.0f, 0.0f, 20.0f);
    REQUIRE(ctrl.isActive() == false);
}

TEST_CASE("HeadingController start and target capture", "[heading_controller]") {
    HeadingController ctrl;
    ctrl.init(1.0f, 0.0f, 0.0f, 20.0f);
    ctrl.start(10.0f);
    REQUIRE(ctrl.isActive() == true);
    REQUIRE(ctrl.getTargetHeading() == Approx(10.0f));
}

TEST_CASE("HeadingController zero error", "[heading_controller]") {
    HeadingController ctrl;
    ctrl.init(1.0f, 0.0f, 0.0f, 20.0f);
    ctrl.start(10.0f);
    float corr = ctrl.update(10.0f, 0.01f);
    REQUIRE(corr == Approx(0.0f));
}

TEST_CASE("HeadingController positive error", "[heading_controller]") {
    HeadingController ctrl;
    ctrl.init(1.0f, 0.0f, 0.0f, 20.0f);
    ctrl.start(0.0f);
    // current = -5° => error = +5°
    float corr = ctrl.update(-5.0f, 0.01f);
    REQUIRE(corr > 0.0f); // correction dương để quay về target
}

TEST_CASE("HeadingController negative error", "[heading_controller]") {
    HeadingController ctrl;
    ctrl.init(1.0f, 0.0f, 0.0f, 20.0f);
    ctrl.start(0.0f);
    // current = +5° => error = -5°
    float corr = ctrl.update(5.0f, 0.01f);
    REQUIRE(corr < 0.0f);
}

TEST_CASE("HeadingController correction limit", "[heading_controller]") {
    HeadingController ctrl;
    ctrl.init(10.0f, 0.0f, 0.0f, 5.0f); // maxCorrection = 5
    ctrl.start(0.0f);
    float corr = ctrl.update(-10.0f, 0.01f); // error = 10°, Kp=10 => 100, but limit 5
    REQUIRE(corr <= 5.0f);
    REQUIRE(corr >= -5.0f);
}

TEST_CASE("HeadingController reset", "[heading_controller]") {
    HeadingController ctrl;
    ctrl.init(1.0f, 0.0f, 0.0f, 20.0f);
    ctrl.start(0.0f);
    ctrl.update(5.0f, 0.01f);
    ctrl.stop();
    REQUIRE(ctrl.isActive() == false);
    // Sau khi stop, update không làm thay đổi correction
    float corr = ctrl.update(5.0f, 0.01f);
    REQUIRE(corr == 0.0f);
}

TEST_CASE("HeadingController angle wrapping", "[heading_controller]") {
    HeadingController ctrl;
    ctrl.init(1.0f, 0.0f, 0.0f, 20.0f);
    ctrl.start(179.0f); // target 179°
    // current = -179° => shortest error = -2° (not +358°)
    float corr = ctrl.update(-179.0f, 0.01f);
    REQUIRE(ctrl.getLastError() == Approx(-2.0f));
}