from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parents[2]
    network = (repo_root / "robot-platform/main/src/Communication/RobotNetworkService.cpp").read_text(encoding="utf-8")
    deploy = (repo_root / "tools/deploy_robot.py").read_text(encoding="utf-8")
    main_ino = (repo_root / "robot-platform/main/main.ino").read_text(encoding="utf-8")

    assert '#include <Update.h>' in network
    assert 'kHttpOtaPath[] = "/api/v1/ota"' in network
    assert 'HTTP_POST, handleHttpOtaFinish, handleHttpOtaUpload' in network
    assert 'Update.begin(UPDATE_SIZE_UNKNOWN, U_FLASH)' in network
    assert 'Update.write(upload.buf, upload.currentSize)' in network
    assert 'Update.end(true)' in network
    assert 'g_server.authenticate(kHttpOtaUser, RobotWiFiConfig::otaPassword())' in network
    assert 'http_ota_upload(args.robot, ota_password, firmware)' in deploy
    assert 'HTTP OTA target:' in deploy
    assert 'isUpdateInProgress()' in main_ino

    print("H27-B1 HTTP OTA transport contract: PASS")


if __name__ == "__main__":
    main()
