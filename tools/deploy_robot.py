#!/usr/bin/env python3
"""One-click student program deployment with isolated production firmware workspaces."""
from __future__ import annotations
import argparse,base64,json,os,re,shutil,socket,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.deployment_contract import create_manifest,sha256_file,validate_manifest,write_manifest
from tools.deployment_runtime import DEFAULT_PROCESS_TIMEOUT_SECONDS,DeploymentRuntimeError,deployment_runtime_environment,platformio_command,run_process
from tools import build_isolation,firmware_workspace,runtime_paths
CAPABILITY_BY_OPCODE={"Forward":"motion.basic","Backward":"motion.basic","TurnLeft":"motion.basic","TurnRight":"motion.basic","SetMotorSpeed":"motion.speed","MoveInitialize":"motion.encoder_angle","MoveRunAngle":"motion.encoder_angle","ReadUltrasonic":"sensor.ultrasonic","ReadTouch":"sensor.touch","ReadLight":"sensor.light","ReadColor":"sensor.color","ReadLine":"sensor.line","GetTraceValue":"sensor.line","GetTraceState":"sensor.line","GetTraceRaw":"sensor.line","GetLightSensorData":"sensor.light","LineBasis":"line.follow","LineFollow":"line.follow","LineStop":"line.follow","LineMillisecond":"line.follow","LineIntersectionStop":"line.follow","LineTurnEncounterLine":"line.follow","LineForBmp":"line.follow","LineSetInitialize":"line.follow","Set3CLed":"actuator.led","SetLightSensorLed":"actuator.led","SetServo":"actuator.servo","SetSeeringEngine":"actuator.servo","SetSeeringEngineTime":"actuator.servo","SetMotor":"actuator.motor","SetMotorServo":"actuator.motor","SetMotorStraightAngle":"actuator.motor","SetMp3Play":"peripheral.mp3","SetLizard":"peripheral.lizard","DisplayVariable":"gui.variable"}

def run(command:list[str],*,env:dict[str,str]|None=None,cwd:Path=ROOT,timeout:float=DEFAULT_PROCESS_TIMEOUT_SECONDS)->None:
 print("$"," ".join(command),flush=True)
 try:r=run_process(command,cwd=cwd,env=env,timeout=timeout,on_output=lambda line:print(line,end="",flush=True))
 except DeploymentRuntimeError as exc:raise RuntimeError(str(exc)) from exc
 if r.returncode!=0:raise RuntimeError(f"Command failed with exit code {r.returncode}: {' '.join(command)}")

def infer_capabilities(header:Path)->list[str]:
 text=header.read_text(encoding="utf-8"); return sorted({"runtime.control",*(CAPABILITY_BY_OPCODE[o] for o in set(re.findall(r"Opcode::([A-Za-z0-9_]+)",text)) if o in CAPABILITY_BY_OPCODE)})

def request_json(url:str,timeout:float)->dict:
 import urllib.request
 with urllib.request.urlopen(url,timeout=timeout) as response:return json.loads(response.read().decode("utf-8"))

def normalize_robot_host(host:str)->str:
 value=(host or "").strip()
 if not value or "://" in value or "/" in value or "\\" in value or len(value)>253 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*",value):raise ValueError("Robot host must be a valid hostname or IP address.")
 return value

def wait_for_robot(host:str,timeout:float=30.0,poll_interval:float=.5)->dict:
 host=normalize_robot_host(host);deadline=time.monotonic()+timeout;last_error=None
 while time.monotonic()<deadline:
  try:
   health=request_json(f"http://{host}/api/v1/health",2.0)
   if health.get("status")=="ok" and health.get("ready") is True:return health
   last_error=RuntimeError(f"Robot not ready: {health}")
  except (OSError,ValueError,json.JSONDecodeError) as exc:last_error=exc
  time.sleep(min(poll_interval,max(0,deadline-time.monotonic())))
 raise RuntimeError(f"Robot health check timed out for {host}: {last_error}")

def validate_bootstrap_config(path:Path)->dict:
 try:data=json.loads(path.read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError) as exc:raise RuntimeError(f"Invalid bootstrap config: {exc}") from exc
 if data.get("type")!="antechkids.robot.bootstrap" or data.get("schema_version")!=1:raise RuntimeError("Unsupported robot bootstrap config")
 wifi=data.get("wifi");ota=data.get("ota")
 if not isinstance(wifi,dict) or not str(wifi.get("ssid","")).strip():raise RuntimeError("Bootstrap config requires a Wi-Fi SSID")
 if not isinstance(ota,dict) or not str(ota.get("password","")):raise RuntimeError("Bootstrap config requires an OTA password")
 return data

def firmware_template()->Path:
 packaged=runtime_paths.application_root()/"firmware"/"robot-platform"
 if packaged.is_dir():return packaged
 if runtime_paths.is_frozen():raise RuntimeError(f"Packaged firmware project is missing: {packaged}")
 return ROOT/"robot-platform"

def deployment_environment(project_name:str)->dict[str,str]:
 env=deployment_runtime_environment(os.environ.copy(),project_name=project_name)
 env.update(build_isolation.build_environment(project_name,env));return env

def flash_bootstrap(config_path:Path,port:str|None)->int:
 config=validate_bootstrap_config(config_path.resolve());project="bootstrap";env=deployment_environment(project)
 env.update({"ROBOT_BOOTSTRAP_CONFIG":str(config_path.resolve()),"ROBOT_WIFI_SSID":str(config["wifi"]["ssid"]),"ROBOT_WIFI_PASSWORD":str(config["wifi"].get("password","")),"ROBOT_OTA_PASSWORD":str(config["ota"]["password"])})
 workspace=firmware_workspace.prepare_firmware_workspace(firmware_template(),project)
 command=platformio_command("run","-e","esp32dev_bootstrap","-t","upload")
 if port:command.extend(["--upload-port",port])
 run(command,cwd=workspace,env=env);print("FIRST-FLASH BOOTSTRAP PASS");return 0

def http_ota_upload(host:str,password:str,firmware:Path,timeout:float=180.0)->str:
 host=normalize_robot_host(host)
 if not password:raise RuntimeError("HTTP OTA requires the robot OTA password")
 if not firmware.is_file() or firmware.stat().st_size<=0:raise RuntimeError(f"Firmware image is invalid: {firmware}")
 boundary="----AnTechKidsRoboStudioOTA"+f"{int(time.time()*1000):x}";preamble=(f"--{boundary}\r\n"+f'Content-Disposition: form-data; name="firmware"; filename="{firmware.name}"\r\n'+'Content-Type: application/octet-stream\r\n\r\n').encode();closing=f"\r\n--{boundary}--\r\n".encode();total=len(preamble)+firmware.stat().st_size+len(closing);auth=base64.b64encode(f"robot:{password}".encode()).decode()
 from http.client import HTTPConnection
 deadline=time.monotonic()+timeout;c=HTTPConnection(host,80,timeout=min(10,timeout))
 try:
  c.connect();c.putrequest("POST","/api/v1/ota");c.putheader("Authorization",f"Basic {auth}");c.putheader("Content-Type",f"multipart/form-data; boundary={boundary}");c.putheader("Content-Length",str(total));c.putheader("Connection","close");c.endheaders();c.send(preamble)
  with firmware.open("rb") as stream:
   while chunk:=stream.read(8192):
    if time.monotonic()>=deadline:raise TimeoutError("HTTP OTA transport deadline exceeded")
    c.send(chunk)
  c.send(closing);response=c.getresponse();body=response.read().decode("utf-8",errors="replace").strip()
  if response.status!=200 or not body.startswith("OK"):raise RuntimeError(f"Robot rejected HTTP OTA ({response.status}): {body}")
  return body
 except (OSError,socket.error,TimeoutError) as exc:raise RuntimeError(f"HTTP OTA transport failed for {host}: {exc}") from exc
 finally:c.close()

def preflight_robot(host:str)->dict:
 host=normalize_robot_host(host)
 try:health=request_json(f"http://{host}/api/v1/health",3.0)
 except (OSError,ValueError,json.JSONDecodeError) as exc:raise RuntimeError(f"Robot preflight failed for {host}: {exc}") from exc
 if health.get("status")!="ok" or health.get("ready") is not True or health.get("network_ready") is not True or health.get("http_ota") is not True:raise RuntimeError(f"Robot preflight failed for {host}: {health}")
 return health

def compile_program(source:Path,build_dir:Path,timeout:float)->Path:
 build_dir.mkdir(parents=True,exist_ok=True);rewritten=build_dir/f"{source.stem}.rewrite.py";header=build_dir/"program.h";report=build_dir/"compile_report.json"
 run([sys.executable,str(ROOT/"tools"/"rewrite.py"),"--input",str(source),"--output",str(rewritten)],cwd=ROOT,timeout=timeout);run([sys.executable,str(ROOT/"tools"/"compile.py"),"--input",str(rewritten),"--output",str(header),"--report",str(report)],cwd=ROOT,timeout=timeout);return header

def main()->int:
 p=argparse.ArgumentParser(description="Deploy a student RoboSim program or bootstrap a new robot");p.add_argument("--input");p.add_argument("--mode",choices=("build","usb","bootstrap","ota"),default="build");p.add_argument("--port");p.add_argument("--robot");p.add_argument("--ssid");p.add_argument("--wifi-password",default=None);p.add_argument("--ota-password",default=None);p.add_argument("--bootstrap-config");p.add_argument("--process-timeout",type=float,default=DEFAULT_PROCESS_TIMEOUT_SECONDS);p.add_argument("--verify-timeout",type=float,default=30.0);a=p.parse_args()
 if a.process_timeout<=0 or a.verify_timeout<=0:p.error("timeouts must be greater than zero")
 if a.mode=="bootstrap":
  if not a.bootstrap_config:p.error("--mode bootstrap requires --bootstrap-config")
  return flash_bootstrap(Path(a.bootstrap_config),a.port)
 if not a.input:p.error("--input is required unless --mode bootstrap is used")
 source=Path(a.input).resolve()
 if not source.is_file() or source.suffix.lower()!=".py":p.error("--input must be an existing .py source file")
 ssid=a.ssid if a.ssid is not None else os.getenv("ROBOT_WIFI_SSID","");wifi_password=a.wifi_password if a.wifi_password is not None else os.getenv("ROBOT_WIFI_PASSWORD","");ota_password=a.ota_password if a.ota_password is not None else os.getenv("ROBOT_OTA_PASSWORD","")
 if a.mode=="ota":
  if not a.robot or not ssid:p.error("--mode ota requires --robot and --ssid (or ROBOT_WIFI_SSID)")
  if not ota_password:p.error("--mode ota requires --ota-password or ROBOT_OTA_PASSWORD")
  normalize_robot_host(a.robot)
 project=source.stem;build_dir=build_isolation.build_root(project);header=compile_program(source,build_dir,a.process_timeout);capabilities=infer_capabilities(header);manifest_path=build_dir/"deployment_manifest.json";manifest=create_manifest(build_dir,"esp32",capabilities,source_path=source,platformio_environment="esp32dev_ota" if a.mode=="ota" else "esp32dev");write_manifest(manifest,manifest_path);validate_manifest(manifest_path,expected_target="esp32")
 workspace=firmware_workspace.prepare_firmware_workspace(firmware_template(),project);firmware_workspace.install_generated_header(header,workspace);env=deployment_environment(project)
 if ssid:env.update({"ROBOT_WIFI_SSID":ssid,"ROBOT_WIFI_PASSWORD":wifi_password})
 if ota_password:env["ROBOT_OTA_PASSWORD"]=ota_password
 if a.mode=="build":run(platformio_command("run","-e","esp32dev"),cwd=workspace,env=env,timeout=a.process_timeout)
 elif a.mode=="usb":run(platformio_command("run","-e","esp32dev","-t","upload")+(["--upload-port",a.port] if a.port else []),cwd=workspace,env=env,timeout=a.process_timeout)
 else:
  preflight_robot(a.robot);run(platformio_command("run","-e","esp32dev_ota"),cwd=workspace,env=env,timeout=a.process_timeout);firmware=build_isolation.firmware_path(project,"esp32dev_ota");http_ota_upload(a.robot,ota_password,firmware);wait_for_robot(a.robot,a.verify_timeout)
 firmware=build_isolation.firmware_path(project,"esp32dev_ota" if a.mode=="ota" else "esp32dev")
 if firmware.is_file():
  data=manifest.to_dict();data.setdefault("artifacts",{})["firmware"]={"path":str(firmware),"size":firmware.stat().st_size,"sha256":sha256_file(firmware)};manifest_path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
 print("DEPLOYMENT PASS");return 0
if __name__=="__main__":raise SystemExit(main())
